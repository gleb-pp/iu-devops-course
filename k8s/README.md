# LAB09 — Kubernetes Fundamentals

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster (minikube)                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Control Plane Node                    │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐    │    │
│  │  │ API Server  │ │  Scheduler  │ │ Controller Mgr  │    │    │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘    │    │
│  │  ┌─────────────┐ ┌─────────────┐                        │    │
│  │  │   etcd      │ │  CoreDNS    │                        │    │
│  │  └─────────────┘ └─────────────┘                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Worker Node                          │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │              Deployment: python-app             │    │    │
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐            │    │    │
│  │  │  │  Pod 1  │ │  Pod 2  │ │  Pod 3  │  ...       │    │    │
│  │  │  │ :5000   │ │ :5000   │ │ :5000   │            │    │    │
│  │  │  └─────────┘ └─────────┘ └─────────┘            │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  │                         ▲                               │    │
│  │                         │                               │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │         Service: python-app-service             │    │    │
│  │  │         Type: NodePort (30007)                  │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    External Access (Browser)
                    http://192.168.49.2:30007
```

### Components

| Component | Purpose | Details |
|-----------|---------|---------|
| **Control Plane** | Manages cluster state | API Server, Scheduler, Controller Manager, etcd |
| **Worker Node** | Runs application workloads | kubelet, container runtime |
| **Deployment** | Manages Pod lifecycle | 3-5 replicas, rolling updates, self-healing |
| **Service** | Stable network endpoint | NodePort (30007) for external access |
| **Python App** | Containerized application | Port 5000, health checks enabled |

## Task 1: Local Kubernetes Setup

### Installation & Cluster Startup

```bash
# Install minikube and kubectl
gleb-pp@gleb-mac iu-devops-course % brew install minikube kubectl

# Start minikube cluster
gleb-pp@gleb-mac iu-devops-course % minikube start                
😄  minikube v1.38.1 on Darwin 15.7.3 (arm64)
✨  Using the docker driver based on existing profile
👍  Starting "minikube" primary control-plane node in "minikube" cluster
🚜  Pulling base image v0.0.50 ...
💾  Downloading Kubernetes v1.35.1 preload ...
❗  minikube cannot pull kicbase image from any docker registry, and is trying to download kicbase tarball from github release page via HTTP.
❗  It's very likely that you have an internet issue. Please ensure that you can access the internet at least via HTTP, directly or with proxy. Currently your proxy configuration is:

    > preloaded-images-k8s-v18-v1...:  243.95 MiB / 243.95 MiB  100.00% 14.79 M
    > kicbase-v0.0.50-arm64.tar:  1.26 GiB / 1.26 GiB  100.00% 9.36 MiB p/s 2m1
❗  minikube was unable to download gcr.io/k8s-minikube/kicbase:v0.0.50, but successfully downloaded kicbase/stable:v0.0.50 as a fallback image
🤷  docker "minikube" container is missing, will recreate.
🔥  Creating docker container (CPUs=2, Memory=1959MB) ...
🐳  Preparing Kubernetes v1.35.1 on Docker 29.2.1 ...
🔗  Configuring bridge CNI (Container Networking Interface) ...
🔎  Verifying Kubernetes components...
    ▪ Using image gcr.io/k8s-minikube/storage-provisioner:v5
🌟  Enabled addons: storage-provisioner, default-storageclass
🏄  Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
```

### Cluster Verification

```bash
# Check cluster info
gleb-pp@gleb-mac iu-devops-course % kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:32771
CoreDNS is running at https://127.0.0.1:32771/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.

# Check nodes
gleb-pp@gleb-mac iu-devops-course % kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   33s   v1.35.1

# Check all pods in cluster
gleb-pp@gleb-mac iu-devops-course % kubectl get pods -A
NAMESPACE     NAME                               READY   STATUS    RESTARTS   AGE
kube-system   coredns-7d764666f9-5gd7f           1/1     Running   0          31s
kube-system   coredns-7d764666f9-l5dhq           1/1     Running   0          31s
kube-system   etcd-minikube                      1/1     Running   0          37s
kube-system   kube-apiserver-minikube            1/1     Running   0          37s
kube-system   kube-controller-manager-minikube   1/1     Running   0          36s
kube-system   kube-proxy-mjccd                   1/1     Running   0          31s
kube-system   kube-scheduler-minikube            1/1     Running   0          36s
kube-system   storage-provisioner                0/1     Error     0          35s

# Check services
gleb-pp@gleb-mac iu-devops-course % kubectl get services
NAME         TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP   55s
```

### Tool Selection

> **Why minikube?**
> 
> I chose minikube because it provides:
> - Single-node cluster ideal for local development and learning
> - Easy setup with Docker driver on macOS
> - Built-in addons (storage-provisioner, dashboard)
> - Simple external access via `minikube service` command
> - Good balance between simplicity and production-like behavior

## Task 2: Application Deployment

### Deployment Manifest

**File:** `k8s/deployment.yml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-app
  labels:
    app: python-app
spec:
  replicas: 3

  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1

  selector:
    matchLabels:
      app: python-app

  template:
    metadata:
      labels:
        app: python-app
    spec:
      containers:
        - name: python-app
          image: glebpp/app_python:1.0
          imagePullPolicy: IfNotPresent

          ports:
            - containerPort: 5000

          env:
            - name: ENV
              value: "production"

          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "256Mi"

          readinessProbe:
            httpGet:
              path: /
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 5

          livenessProbe:
            httpGet:
              path: /
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 10
```

### Key Configuration Decisions

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **replicas** | 3 | High availability with minimal resource overhead |
| **rollingUpdate** | maxUnavailable=1, maxSurge=1 | Zero-downtime updates with controlled rollout |
| **cpu requests** | 100m | Guarantee minimum CPU for scheduling |
| **cpu limits** | 500m | Prevent CPU starvation of other pods |
| **memory requests** | 128Mi | Ensure memory availability |
| **memory limits** | 256Mi | Prevent OOM kills due to leaks |
| **readinessProbe** | /, 5s delay | Check app is ready for traffic before routing |
| **livenessProbe** | /, 10s delay | Restart unresponsive containers |

### Deployment Verification

```bash
# Apply deployment
gleb-pp@gleb-mac iu-devops-course % kubectl apply -f k8s/deployment.yml
deployment.apps/python-app created

# Check deployments
gleb-pp@gleb-mac iu-devops-course % kubectl get deployments
NAME         READY   UP-TO-DATE   AVAILABLE   AGE
python-app   0/3     3            0           5s

# Check pods (creating)
gleb-pp@gleb-mac iu-devops-course % kubectl get pods
NAME                          READY   STATUS              RESTARTS   AGE
python-app-5fdbccc45f-bfmbn   0/1     ContainerCreating   0          11s
python-app-5fdbccc45f-j5vgs   0/1     ContainerCreating   0          11s
python-app-5fdbccc45f-nrkjp   0/1     ContainerCreating   0          11s

# Detailed deployment information
gleb-pp@gleb-mac iu-devops-course % kubectl describe deployment python-app
Name:                   python-app
Namespace:              default
CreationTimestamp:      Wed, 25 Mar 2026 11:24:40 +0300
Labels:                 app=python-app
Annotations:            deployment.kubernetes.io/revision: 1
Selector:               app=python-app
Replicas:               3 desired | 3 updated | 3 total | 0 available | 3 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  1 max unavailable, 1 max surge
Pod Template:
  Labels:  app=python-app
  Containers:
   python-app:
    Image:      glebpp/app_python:1.0
    Port:       5000/TCP
    Host Port:  0/TCP
    Limits:
      cpu:     500m
      memory:  256Mi
    Requests:
      cpu:      100m
      memory:   128Mi
    Liveness:   http-get http://:5000/ delay=10s timeout=1s period=10s #success=1 #failure=3
    Readiness:  http-get http://:5000/ delay=5s timeout=1s period=5s #success=1 #failure=3
    Environment:
      ENV:         production
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      False   MinimumReplicasUnavailable
  Progressing    True    ReplicaSetUpdated
OldReplicaSets:  <none>
NewReplicaSet:   python-app-5fdbccc45f (3/3 replicas created)
Events:
  Type    Reason             Age   From                   Message
  ----    ------             ----  ----                   -------
  Normal  ScalingReplicaSet  15s   deployment-controller  Scaled up replica set python-app-5fdbccc45f from 0 to 3
```

## Task 3: Service Configuration

### Service Manifest

**File:** `k8s/service.yml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: python-app-service
spec:
  type: NodePort

  selector:
    app: python-app

  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000 
      nodePort: 30007
```

### Service Deployment & Verification

```bash
# Apply service
gleb-pp@gleb-mac iu-devops-course % kubectl apply -f k8s/service.yml
service/python-app-service created

# Check services
gleb-pp@gleb-mac iu-devops-course % kubectl get services
NAME                 TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
kubernetes           ClusterIP   10.96.0.1      <none>        443/TCP        16m
python-app-service   NodePort    10.109.4.248   <none>        80:30007/TCP   5s

# Check endpoints (pods behind service)
gleb-pp@gleb-mac iu-devops-course % kubectl get endpoints
Warning: v1 Endpoints is deprecated in v1.33+; use discovery.k8s.io/v1 EndpointSlice
NAME                 ENDPOINTS                                         AGE
kubernetes           192.168.49.2:8443                                 16m
python-app-service   10.244.0.4:5000,10.244.0.5:5000,10.244.0.6:5000   11s
```

### Service Access

```bash
# Get service URL via minikube
gleb-pp@gleb-mac iu-devops-course % minikube service python-app-service
┌───────────┬────────────────────┬─────────────┬───────────────────────────┐
│ NAMESPACE │        NAME        │ TARGET PORT │            URL            │
├───────────┼────────────────────┼─────────────┼───────────────────────────┤
│ default   │ python-app-service │ 80          │ http://192.168.49.2:30007 │
└───────────┴────────────────────┴─────────────┴───────────────────────────┘
🔗  Starting tunnel for service python-app-service.
┌───────────┬────────────────────┬─────────────┬────────────────────────┐
│ NAMESPACE │        NAME        │ TARGET PORT │          URL           │
├───────────┼────────────────────┼─────────────┼────────────────────────┤
│ default   │ python-app-service │             │ http://127.0.0.1:55349 │
└───────────┴────────────────────┴─────────────┴────────────────────────┘
🎉  Opening service default/python-app-service in default browser...
```

**Access verification:** Service accessible at `http://192.168.49.2:30007` (minikube node IP + nodePort) and via tunnel at `http://127.0.0.1:55349`.

## Task 4: Scaling and Updates

### Scaling to 5 Replicas

```bash
# Apply updated deployment with replicas: 5
gleb-pp@gleb-mac iu-devops-course % kubectl apply -f k8s/deployment.yml
deployment.apps/python-app configured

# Watch pods being created
gleb-pp@gleb-mac iu-devops-course % kubectl get pods -w
NAME                          READY   STATUS    RESTARTS   AGE
python-app-5fdbccc45f-bfmbn   1/1     Running   0          10m
python-app-5fdbccc45f-j5vgs   1/1     Running   0          10m
python-app-5fdbccc45f-nrkjp   1/1     Running   0          10m
python-app-5fdbccc45f-qcfzj   0/1     Running   0          4s
python-app-5fdbccc45f-r927h   0/1     Running   0          4s
python-app-5fdbccc45f-r927h   1/1     Running   0          7s
python-app-5fdbccc45f-qcfzj   1/1     Running   0          8s

# Verify scaling completed
gleb-pp@gleb-mac iu-devops-course % kubectl get pods
NAME                          READY   STATUS    RESTARTS   AGE
python-app-5fdbccc45f-bfmbn   1/1     Running   0          10m
python-app-5fdbccc45f-j5vgs   1/1     Running   0          10m
python-app-5fdbccc45f-nrkjp   1/1     Running   0          10m
python-app-5fdbccc45f-qcfzj   1/1     Running   0          41s
python-app-5fdbccc45f-r927h   1/1     Running   0          41s

# Check deployment status
gleb-pp@gleb-mac iu-devops-course % kubectl get deployment
NAME         READY   UP-TO-DATE   AVAILABLE   AGE
python-app   5/5     5            5           10m
```

### Rolling Update

```yaml
# Add VERSION environment variable to trigger update
env:
  - name: ENV
    value: "production"
  - name: VERSION
    value: "v2"
```

```bash
# Apply update
gleb-pp@gleb-mac iu-devops-course % kubectl apply -f k8s/deployment.yml
deployment.apps/python-app configured

# Watch rollout
gleb-pp@gleb-mac iu-devops-course % kubectl rollout status deployment/python-app
deployment "python-app" successfully rolled out

# Observe rolling update process
gleb-pp@gleb-mac iu-devops-course % kubectl get pods -w
NAME                          READY   STATUS    RESTARTS   AGE
python-app-5cb7f6674d-fgjg6   1/1     Running   0          36s
python-app-5cb7f6674d-pfd6l   1/1     Running   0          22s
python-app-5cb7f6674d-pqqpf   1/1     Running   0          29s
python-app-5cb7f6674d-wmtzs   1/1     Running   0          36s
python-app-5cb7f6674d-z6wms   1/1     Running   0          29s
```

### Rollback Demonstration

```bash
# View rollout history
gleb-pp@gleb-mac iu-devops-course % kubectl rollout history deployment/python-app
deployment.apps/python-app 
REVISION  CHANGE-CAUSE
1         <none>
2         <none>

# Perform rollback
gleb-pp@gleb-mac iu-devops-course % kubectl rollout undo deployment/python-app
deployment.apps/python-app rolled back

# Verify rollback in progress
gleb-pp@gleb-mac iu-devops-course % kubectl get pods
NAME                          READY   STATUS    RESTARTS   AGE
python-app-5cb7f6674d-pfd6l   1/1     Running   0          84s
python-app-5cb7f6674d-pqqpf   1/1     Running   0          91s
python-app-5cb7f6674d-wmtzs   1/1     Running   0          98s
python-app-5cb7f6674d-z6wms   1/1     Running   0          91s
python-app-5fdbccc45f-5t74v   0/1     Running   0          4s
python-app-5fdbccc45f-kpt66   0/1     Running   0          4s
```

## Task 5: Documentation

### Architecture Overview

The deployment consists of:
- **5 Pods** (scaled from initial 3) running the Python application
- **1 Deployment** managing Pod lifecycle with RollingUpdate strategy
- **1 NodePort Service** exposing the application externally

**Netflow:** External request → NodePort (30007) → Service (80) → Pod (5000)

**Resource allocation:** Each Pod requests 100m CPU and 128Mi memory, with limits of 500m CPU and 256Mi memory.

### Manifest Files Summary

| File | Purpose | Key Configuration |
|------|---------|-------------------|
| **deployment.yml** | Manages application Pods | 3-5 replicas, rolling updates, resource limits, health probes |
| **service.yml** | Exposes application | NodePort type, selector matching deployment labels, port 30007 |

### Deployment Evidence

```bash
# Full cluster state
gleb-pp@gleb-mac iu-devops-course % kubectl get all
NAME                              READY   STATUS    RESTARTS   AGE
pod/python-app-5cb7f6674d-fgjg6   1/1     Running   0          2m
pod/python-app-5cb7f6674d-pfd6l   1/1     Running   0          2m
pod/python-app-5cb7f6674d-pqqpf   1/1     Running   0          2m
pod/python-app-5cb7f6674d-wmtzs   1/1     Running   0          2m
pod/python-app-5cb7f6674d-z6wms   1/1     Running   0          2m

NAME                         TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/kubernetes           ClusterIP   10.96.0.1      <none>        443/TCP        20m
service/python-app-service   NodePort    10.109.4.248   <none>        80:30007/TCP   4m

NAME                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/python-app   5/5     5            5           15m

NAME                                    DESIRED   CURRENT   READY   AGE
replicaset.apps/python-app-5cb7f6674d   5         5         5       2m
replicaset.apps/python-app-5fdbccc45f   0         0         0       15m
```

### Operations Performed

| Operation | Command | Outcome |
|-----------|---------|---------|
| **Deploy** | `kubectl apply -f k8s/deployment.yml` | 3 pods created |
| **Expose** | `kubectl apply -f k8s/service.yml` | Service with NodePort 30007 |
| **Scale** | `kubectl apply -f k8s/deployment.yml` (replicas:5) | 5 pods running |
| **Update** | `kubectl apply -f k8s/deployment.yml` (add version) | Rolling update, zero downtime |
| **Rollback** | `kubectl rollout undo deployment/python-app` | Reverted to previous version |

### Production Considerations

#### Health Checks Implementation

**Readiness Probe:** HTTP GET on `/` with 5s initial delay, 5s interval
- Ensures traffic only reaches fully initialized Pods
- Prevents request failures during startup

**Liveness Probe:** HTTP GET on `/` with 10s initial delay, 10s interval
- Detects deadlocks and unresponsive application states
- Automatically restarts unhealthy containers

#### Resource Limits Rationale

- **CPU (100m request, 500m limit):** Guarantees baseline performance while preventing noisy neighbor issues
- **Memory (128Mi request, 256Mi limit):** Provides headroom for normal operation, limits prevent OOM kills from memory leaks

#### Production Improvements

1. **Horizontal Pod Autoscaler:** Add HPA to automatically scale based on CPU/memory metrics
2. **Ingress Controller:** Replace NodePort with Ingress for HTTP routing and SSL termination
3. **ConfigMaps/Secrets:** Externalize configuration and credentials
4. **Monitoring Stack:** Deploy Prometheus + Grafana for metrics collection
5. **Network Policies:** Restrict pod-to-pod communication
6. **PodDisruptionBudget:** Ensure minimum availability during voluntary disruptions

### Challenges and Solutions

#### Challenge 1: ImagePullBackOff
**Problem:** Local Docker image not accessible by minikube
**Solution:** Used `eval $(minikube docker-env)` to use minikube's Docker daemon, or pushed image to registry

#### Challenge 2: Probes Failing
**Problem:** Application took longer than expected to become ready
**Solution:** Increased initialDelaySeconds from 3 to 5 for readiness, 10 for liveness

#### Challenge 3: Service Not Accessible
**Problem:** Endpoints showed empty, no pods behind service
**Solution:** Verified selector labels matched between Deployment and Service (`app: python-app`)
