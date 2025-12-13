
What is KEDA
KEDA (Kubernetes Event-driven Autoscaling) is a tool that works alongside the Kubernetes native Horizontal Pod Autoscaler (HPA) to enable event-driven pod scaling.

Unlike traditional HPA, which relies solely on CPU or memory metrics, KEDA can respond to external event sources to scale workloads more flexibly and efficiently.

Why KEDA
First of all, KEDA extend Kubernetes HPA behavior without introducing conflicts. You can explicitly define which workloads should respond to the event-driven triggers, which can be external event sources like Prometheus metrics, Loki query results, Kafka topics, etc.

Secondly, KEDA is easy-to-use and operate. It can be deployed with Helm and mainly consists the core components:

KEDA Operator: reconciles the changes on its custom resources (CR) i.e., ScaledObject and the number of app instance to be scaled in/out.
Scalers: connect to event sources, pulling current usage data.
Metrics Server: provides the event sources metrics to Kubernetes’ HPA for making scaling decisions.
Admission Webhook: ensure the configuration is correct.

Hands-on
The below section walks you through a simple hands-on on how to trigger the autoscale of an application by KEDA using Cron.

Step 1: Installation
Install KEDA with Helm.

helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda --version 2.16.1 -n keda --create-namespace
Step 2: Deploy Nginx Application
The Nginx application consists a Deployment and a Service.

Step 3: Create a ScaledObject Custom Resource
Create a ScaledObject to autoscale the Nginx Deployment triggered by Cron during the specific time.

# scaledobject.yaml

kubectl apply -f scaledobject.yaml
kubectl get hpa
NAME             REFERENCE          TARGETS     MINPODS   MAXPODS   REPLICAS   AGE
keda-hpa-nginx   Deployment/nginx   1/1 (avg)   1         5         1          2m
And the Pods should be scaled up to 5 replicas during the time window defined in the ScaledObject custom resource.

kubectl get pod
NAME                     READY   STATUS    RESTARTS   AGE
nginx-76b7b9547d-rrfh2   1/1     Running   0          10m
After passing the end time, the pods will shrink to 1 replica.
