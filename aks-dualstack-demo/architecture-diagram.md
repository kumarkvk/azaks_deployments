# AKS Dual-Stack + Node Public IP — Architecture Diagrams

## 1. Mermaid diagram (paste into Markdown-capable slide tools, Mermaid Live Editor, or Draw.io's Mermaid import)

```mermaid
flowchart TB
    Internet(("Internet"))

    subgraph Prefixes["Bring-your-own Public IP Prefixes (RG: rg-dualstack-demo)"]
        direction LR
        PfxV4["pip-v4-prefix\n/28 Standard IPv4"]
        PfxV6["pip-v6-prefix\n/124 Standard IPv6"]
    end

    subgraph AKS["AKS Cluster: aks-dualstack-demo (Azure CNI Overlay, dual-stack)"]
        direction TB

        subgraph Node1["Node 1 (VMSS instance)"]
            N1V4["Public IPv4\n(from pip-v4-prefix)"]
            N1V6["Public IPv6\n(from pip-v6-prefix)"]
            N1Priv["Private IPv4 + IPv6\n(node subnet)"]
            Pod1A["Pod A\nIPv4 + IPv6 (overlay)"]
            Pod1B["Pod B\nIPv4 + IPv6 (overlay)"]
        end

        subgraph Node2["Node 2 (VMSS instance)"]
            N2V4["Public IPv4\n(from pip-v4-prefix)"]
            N2V6["Public IPv6\n(from pip-v6-prefix)"]
            N2Priv["Private IPv4 + IPv6\n(node subnet)"]
            Pod2A["Pod C\nIPv4 + IPv6 (overlay)"]
        end

        Svc["Service: dualstack-demo-svc\ntype=LoadBalancer\nipFamilyPolicy=RequireDualStack\nclusterIPs: [v4, v6]"]

        LB["Azure Load Balancer\nFrontend IPv4 + Frontend IPv6"]
    end

    Internet -- "direct to node\n(gaming/VoIP/IoT use case)" --> N1V4
    Internet -- "direct to node (IPv6)" --> N1V6
    Internet -- "direct to node" --> N2V4
    Internet -- "direct to node (IPv6)" --> N2V6

    Internet -- "normal ingress path\n(Service type=LoadBalancer)" --> LB
    LB --> Svc
    Svc --> Pod1A
    Svc --> Pod1B
    Svc --> Pod2A

    PfxV4 -.->|"one IPv4 per node"| N1V4
    PfxV4 -.->|"one IPv4 per node"| N2V4
    PfxV6 -.->|"one IPv6 per node"| N1V6
    PfxV6 -.->|"one IPv6 per node"| N2V6
```

**Talking points while showing this slide:**
- Two independent inbound paths exist side by side: the **normal** Service/LoadBalancer path (what almost every cluster uses), and the **direct-to-node** path enabled only because Node Public IP is turned on.
- Every box that says "IPv4 + IPv6" is a live illustration of dual-stack: pods (overlay CIDR), the Service `clusterIPs`, and the node addresses all carry both families simultaneously.
- The dotted lines from the prefixes to each node show the 1:1 allocation — one IPv4 and one IPv6 address per node, drawn from your own reserved prefixes, not ephemeral Azure-assigned addresses.

---

## 2. ASCII fallback (for plain-text decks or terminal walkthroughs)

```
                                   INTERNET
                                       |
         +-----------------------------+-----------------------------+
         |                             |                             |
   (direct-to-node)              (normal ingress)              (direct-to-node)
         |                             |                             |
         v                             v                             v
+-----------------+           +-------------------+          +-----------------+
| Node 1           |          | Azure LoadBalancer |          | Node 2           |
| Pub IPv4 (prefix)|          | FE: IPv4 + IPv6    |          | Pub IPv4 (prefix)|
| Pub IPv6 (prefix)|          +---------+----------+          | Pub IPv6 (prefix)|
| Priv IPv4+IPv6    |                   |                     | Priv IPv4+IPv6    |
|                   |                   v                     |                   |
| Pod A (v4+v6)     |          +-------------------+          | Pod C (v4+v6)     |
| Pod B (v4+v6)     |<-------- | Svc: dualstack-svc |--------->|                   |
+-------------------+          | clusterIPs: v4,v6  |          +-------------------+
                                +-------------------+

Public IP Prefixes (bring-your-own, Standard SKU):
  pip-v4-prefix (/28)  -----> one IPv4 assigned per node
  pip-v6-prefix (/124) -----> one IPv6 assigned per node
```

## 3. One-line summary graphic (good for a title-slide watermark)

```
[ Pod IPv4/IPv6 ]  <-- overlay -->  [ Node IPv4/IPv6 ]  <-- prefix -->  [ Internet ]
        ^                                    ^
        |                                    |
   Service clusterIPs                 az vmss list-instance-public-ips
   (dual-stack proof #1)              (dual-stack proof #2)
```
