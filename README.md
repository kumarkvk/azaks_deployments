# azaks_deployments
--- Deployment yaml name nginx-deployment.yaml
--- COMMAND to deploy a simple nginx pod
     kubectl apply -f nginx-deployment.yaml



kubectl exec -it net-test -- bash
ping my-service.default.svc.cluster.local
curl http://my-service:8080
dig my-service.default.svc.cluster.local
ip route
