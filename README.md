# azaks_deployments
--- Deployment yaml name nginx-deployment.yaml
--- COMMAND to deploy a simple nginx pod
     kubectl apply -f nginx-deployment.yaml



kubectl exec -it net-test -- bash
ping my-service.default.svc.cluster.local
curl http://my-service:8080
dig my-service.default.svc.cluster.local
ip rout







Strategy	Description	Effect	Example Resource Type
Recreate	Deletes old pods before creating new ones	Downtime during update	Deployment
RollingUpdate	Gradually replaces pods	Minimized downtime	Deployment
Canary	Incremental rollouts	Controlled release	Deployment + tools
Blue/Green	Two parallel environments, switch traffic	Zero downtime, risk reduction	Multiple deploymentse
