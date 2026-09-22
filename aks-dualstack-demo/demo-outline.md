# AKS Dual-Stack + Node Public IPs — Demo Outline

**Audience:** Technical (engineers/architects) | **Duration:** ~20–25 min | **Format:** Slides + live CLI walkthrough

---

## Slide 1 — Title
"AKS Networking Deep Dive: Dual-Stack Clusters & Per-Node Public IPs"

## Slide 2 — Agenda
1. Why dual-stack? Why node public IPs?
2. Architecture requirements
3. Live demo: build a dual-stack cluster with per-node dual-stack public IPs
4. Verify at every layer (node, pod, service)
5. Gotchas & limitations
6. Q&A

## Slide 3 — The problem statement
- Default AKS: nodes have **no public IP**. Inbound only via LoadBalancer Service; outbound via LB/NAT Gateway/UDR.
- Two independent asks that show up in real engagements:
  - "We need IPv6 end-to-end" (compliance, telecom, mobile carriers, future-proofing)
  - "We need each node individually reachable from the internet" (gaming servers, VoIP media relays, IoT device call-back, direct-to-node compliance scanning)
- AKS now supports **both together**: a node can carry one public IPv4 *and* one public IPv6 address (preview).

## Slide 4 — Architecture requirements
| Requirement | Detail |
|---|---|
| Network plugin | Azure CNI **Overlay**, or Azure CNI Powered by Cilium (Linux, K8s ≥1.29) — NOT legacy Azure CNI |
| IP families | `--ip-families IPv4,IPv6` at cluster create |
| Node public IP | `--enable-node-public-ip` |
| Prefixes (this demo) | One Standard-SKU IPv4 prefix + one Standard-SKU IPv6 prefix, same region |
| Preview flag | `NodePublicIPv6PrefixPreview` registered on the subscription |
| Immutability | Node public IP config can't be toggled on an existing pool — must be set at pool creation |
| Not supported with | AKS Automatic, Node Auto-Provisioning (Karpenter), multi-NIC pools |

## Slide 5 — Live Demo (see `demo-script.sh`)
Walk through: register preview → create prefixes → create cluster → verify nodes/VMSS → deploy dual-stack Service → curl both address families.

## Slide 6 — Gotchas to call out live
- Node Public IP is immutable — plan the pool size/IP capacity up front.
- Each node gets exactly **one** IPv6 public IP even in dual-stack mode (not a whole prefix per node).
- NSG on the node subnet becomes your only inbound gatekeeper — show the NSG blade.
- Cluster Autoscaler `max-count` must not exceed prefix address capacity (a `/28` IPv4 prefix = 16 usable addresses).
- Standard NAT Gateway is IPv4-only; dual-stack egress via NAT Gateway needs **NAT Gateway StandardV2**.
- Azure CNI Overlay + dual-stack does not support Azure/Calico NetworkPolicy — Cilium is the policy-capable path.
- Azure Linux 2.0 is retiring (frozen 2025-11-30, removed 2026-10-31) — use AzureLinux3 images for new pools.

## Slide 7 — Wrap-up
- Recap: dual-stack = protocol reach; node public IP = per-node direct reachability; combined = both, per node, from your own prefixes.
- Link to Microsoft Learn: "Use dual-stack networking" and "Assign public IP addresses to nodes" docs.

## Slide 8 — Q&A

---
## Files in this folder
- `demo-script.sh` — copy/paste CLI walkthrough (idempotent-ish, includes cleanup)
- `dualstack-app.yaml` — demo Deployment + dual-stack LoadBalancer Service to curl from both IPv4 and IPv6
