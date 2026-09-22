#!/usr/bin/env bash
# AKS Dual-Stack + Node Public IPs — Demo Script
# Run each block in order; pause between blocks to narrate/verify in the portal.

set -euo pipefail

LOCATION="eastus"
RG="rg-dualstack-demo"
AKS_NAME="aks-dualstack-demo"

# -----------------------------------------------------------------------
# Step 0 — Preview extension + feature registration (do this BEFORE the demo;
# registration can take several minutes to propagate)
# -----------------------------------------------------------------------
az extension add --name aks-preview --upgrade
az feature register --namespace Microsoft.ContainerService --name NodePublicIPv6PrefixPreview
# Poll until state == Registered before continuing:
az feature show --namespace Microsoft.ContainerService --name NodePublicIPv6PrefixPreview \
  --query "properties.state" -o tsv
az provider register --namespace Microsoft.ContainerService

# -----------------------------------------------------------------------
# Step 1 — Resource group + public IP prefixes (bring-your-own IPv4 + IPv6)
# -----------------------------------------------------------------------
az group create --name "$RG" --location "$LOCATION"

az network public-ip prefix create -g "$RG" -n pip-v4-prefix \
  --location "$LOCATION" --length 28 --sku Standard --version IPv4

az network public-ip prefix create -g "$RG" -n pip-v6-prefix \
  --location "$LOCATION" --length 124 --sku Standard --version IPv6

IPV4_PREFIX_ID=$(az network public-ip prefix show -g "$RG" -n pip-v4-prefix --query id -o tsv)
IPV6_PREFIX_ID=$(az network public-ip prefix show -g "$RG" -n pip-v6-prefix --query id -o tsv)
echo "IPv4 prefix: $IPV4_PREFIX_ID"
echo "IPv6 prefix: $IPV6_PREFIX_ID"

# -----------------------------------------------------------------------
# Step 2 — Create the dual-stack cluster with per-node dual-stack public IPs
# -----------------------------------------------------------------------
az aks create \
  --resource-group "$RG" \
  --name "$AKS_NAME" \
  --location "$LOCATION" \
  --network-plugin azure --network-plugin-mode overlay \
  --ip-families IPv4,IPv6 \
  --enable-node-public-ip \
  --node-public-ip-prefix-ids "${IPV4_PREFIX_ID},${IPV6_PREFIX_ID}" \
  --node-count 2 \
  --generate-ssh-keys

# -----------------------------------------------------------------------
# Step 3 — Verify: Kubernetes-side node addresses (both families)
# -----------------------------------------------------------------------
az aks get-credentials -g "$RG" -n "$AKS_NAME" --overwrite-existing
kubectl get nodes -o wide
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.addresses}{"\n"}{end}'

# -----------------------------------------------------------------------
# Step 4 — Verify: actual public IPs on the VMSS instances (the "wow" moment)
# -----------------------------------------------------------------------
NODE_RG=$(az aks show -g "$RG" -n "$AKS_NAME" --query nodeResourceGroup -o tsv)
VMSS_NAME=$(az vmss list -g "$NODE_RG" --query "[0].name" -o tsv)
echo "Node resource group: $NODE_RG  VMSS: $VMSS_NAME"
az vmss list-instance-public-ips -g "$NODE_RG" --vmss-name "$VMSS_NAME" -o table

# -----------------------------------------------------------------------
# Step 5 — Deploy dual-stack demo app + Service
# -----------------------------------------------------------------------
kubectl apply -f dualstack-app.yaml
kubectl get svc dualstack-demo-svc -o wide
kubectl get svc dualstack-demo-svc -o jsonpath='{.spec.clusterIPs}{"\n"}'
kubectl get svc dualstack-demo-svc -o jsonpath='{.status.loadBalancer.ingress}{"\n"}'

# Once EXTERNAL-IP(s) populate, curl both families from your workstation:
#   curl -4 http://<ipv4-address>/
#   curl -6 http://[<ipv6-address>]/

# -----------------------------------------------------------------------
# Cleanup (don't forget on a live demo!)
# -----------------------------------------------------------------------
# az group delete --name "$RG" --yes --no-wait
