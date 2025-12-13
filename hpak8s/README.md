Deploy
kubectl apply -f azaks_deployments/hpak8s/azaks/hpa-deployment.yaml

# List Pods, Deploy & Service
kubectl get pod
kubect get svc

# Access Application (Only if our Cluster is Public Subnet)
http://<PublicIP-from-Get-SVC-Output>i

Step-02: Create a Horizontal Pod Autoscaler resource for the "hpa-demo-deployment"
This command creates an autoscaler that targets 20 percent CPU utilization for the deployment, with a minimum of one pod and a maximum of ten pods.
When the average CPU load is below 20 percent, the autoscaler tries to reduce the number of pods in the deployment, to a minimum of one.
When the load is greater than 20 percent, the autoscaler tries to increase the number of pods in the deployment, up to a maximum of ten
# HPA Imperative - Template
kubectl autoscale deployment <deployment-name> --cpu-percent=20 --min=1 --max=10

# HPA Imperative - Replace
kubectl autoscale deployment hpa-demo-deployment --cpu-percent=20 --min=1 --max=10

# HPA Declarative (Optional - If you use above imperative command this is just for reference)
kubectl apply -f azaks_deployments/hpak8s/azaks/hpa-deployment.yaml

# Describe HPA
kubectl describe hpa/hpa-demo-deployment 

# List HPA
kubectl get horizontalpodautoscaler.autoscaling/hpa-demo-deployment 
Step-02: Create the load & Verify how HPA is working
# Generate Load (new Terminal)
kubectl run apache-bench -i --tty --rm --image=httpd -- ab -n 500000 -c 1000 http://hpa-demo-service-nginx.default.svc.cluster.local/ 

or
kubectl run apache-bench -i --tty --rm --image=httpd -- ab -n 500000 -c 1000 http://publicip/

# List all HPA
kubectl get hpa

# List specific HPA
kubectl get hpa hpa-demo-deployment 

# Describe HPA
kubectl describe hpa/hpa-demo-deployment 

# List Pods
kubectl get pods
Step-03: Cooldown / Scaledown
Default cooldown period is 5 minutes.
Once CPU utilization of pods is less than 20%, it will starting terminating pods and will reach to minimum 1 pod as configured.

Step-04: Clean-Up
# Delete HPA
kubectl delete hpa hpa-demo-deployment

# Delete Deployment & Service
kubectl delete -f zaks_deployments/hpak8s
