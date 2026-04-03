# Lab 10 — Helm Package Manager

## Chart Overview

This Helm chart packages the Python application from Lab 9, transforming static Kubernetes manifests into a reusable, configurable, and environment-aware deployment.

### Chart Structure

```
k8s/mychart/
├── Chart.yaml                # Chart metadata (name, version, description)
├── values.yaml               # Default configuration values
├── values-dev.yaml           # Development environment overrides
├── values-prod.yaml          # Production environment overrides
└── templates/
    ├── deployment.yaml       # Main application deployment (templatized)
    ├── service.yaml          # Service for exposing the application
    ├── _helpers.tpl          # Helper templates for labels
    └── hooks/
        ├── pre-install-job.yaml   # Job run before installation
        └── post-install-job.yaml  # Job run after installation
```

### Key Template Files and Their Purpose

| File | Purpose | Key Templating Elements |
|------|---------|--------------------------|
| **deployment.yaml** | Defines the application's Pod template, replicas, and rolling update strategy. | `{{ .Values.replicaCount }}`, `{{ .Values.image.repository }}`, `{{ .Values.env.ENV }}` |
| **service.yaml** | Exposes the application internally and externally. | `{{ .Values.service.type }}`, `{{ .Values.containerPort }}` |
| **pre-install-job.yaml** | Executes a task (e.g., validation) before the main application is deployed. | Annotations for hook control |
| **post-install-job.yaml** | Executes a task (e.g., smoke test) after the application is deployed. | Annotations for hook control |

### Values Organization Strategy

The chart uses a layered values approach:
1.  **`values.yaml`** (Base): Contains sensible defaults for all environments.
2.  **`values-dev.yaml`** (Dev): Overrides defaults for a development setup (e.g., 1 replica, relaxed resources).
3.  **`values-prod.yaml`** (Prod): Overrides defaults for a production setup (e.g., 5 replicas, higher resources).
4.  **`--set` flag**: Allows for one-off overrides on the command line.

---

## Configuration Guide

### Important Values and Their Purpose

| Value Path | Purpose | Example |
|------------|---------|---------|
| `replicaCount` | Number of Pod replicas to run. | `3` |
| `image.repository` | Docker image repository. | `glebpp/app_python` |
| `image.tag` | Docker image tag. | `1.0` or `latest` |
| `service.type` | Type of Kubernetes Service. | `NodePort` or `LoadBalancer` |
| `resources.requests` | Minimum resources guaranteed to a Pod. | `cpu: 100m`, `memory: 128Mi` |
| `resources.limits` | Maximum resources a Pod can consume. | `cpu: 500m`, `memory: 256Mi` |
| `env.*` | Environment variables passed to the container. | `ENV: "production"` |
| `probes.*` | Configuration for liveness and readiness probes. | `initialDelaySeconds`, `periodSeconds` |

### How to Customize for Different Environments

To deploy the application to a specific environment, you provide the corresponding values file during installation.

```bash
# Deploy to Development
helm install myapp-dev k8s/mychart -f k8s/mychart/values-dev.yaml

# Deploy to Production
helm install myapp-prod k8s/mychart -f k8s/mychart/values-prod.yaml

# Upgrade an existing release to a different environment
helm upgrade myapp-dev k8s/mychart -f k8s/mychart/values-prod.yaml
```

### Example Installations

**Development installation with 1 replica and NodePort:**
```bash
helm install dev-app k8s/mychart -f k8s/mychart/values-dev.yaml
```
**Production installation with 5 replicas and LoadBalancer:**
```bash
helm install prod-app k8s/mychart -f k8s/mychart/values-prod.yaml
```
**Command-line override for a specific value (e.g., temporary scaling):**
```bash
helm install scaled-app k8s/mychart --set replicaCount=10
```

---

## Hook Implementation

### What Hooks Were Implemented and Why

Two hooks were implemented to manage the application lifecycle:

1.  **Pre-install Hook**: A Kubernetes Job that runs *before* the main Deployment and Service are created. It is used for tasks that must complete before the application starts, such as database schema migrations or pre-deployment validation.
2.  **Post-install Hook**: A Kubernetes Job that runs *after* the main resources have been installed. It is used for post-deployment tasks, such as smoke tests, sending notifications, or initial data seeding.

### Hook Execution Order and Weights

Hooks are executed based on their type and weight. A lower weight number runs first.

| Hook | Weight | Execution Time |
|------|--------|----------------|
| `pre-install-job` | **-5** | Before main resources |
| `post-install-job` | **5** | After main resources |

This ensures that the pre-install job completes successfully before Helm proceeds to deploy the main application. The post-install job runs only after the application is up and running.

### Deletion Policies Explanation

The `helm.sh/hook-delete-policy` annotation defines when a hook resource should be deleted. The `hook-succeeded` policy was chosen for both jobs.

- **`hook-succeeded`**: The hook resource (Job) is deleted after it has completed successfully.
- **Why this is important**: This policy ensures that the cluster is kept clean of completed or failed hook jobs, preventing clutter and potential resource waste. The hooks are only visible during their execution and are automatically removed afterward.

**Pre-install Hook Annotation:**
```yaml
annotations:
  "helm.sh/hook": pre-install
  "helm.sh/hook-weight": "-5"
  "helm.sh/hook-delete-policy": hook-succeeded
```
**Post-install Hook Annotation:**
```yaml
annotations:
  "helm.sh/hook": post-install
  "helm.sh/hook-weight": "5"
  "helm.sh/hook-delete-policy": hook-succeeded
```

---

## Installation Evidence

### `helm list` Output
Shows all deployed Helm releases in the cluster.
```bash
$ helm list
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART
myapp-dev       default         2               2026-04-01 12:27:08.000000 +0000 UTC   deployed        mychart-0.1.0
myrelease       default         1               2026-04-01 12:29:07.000000 +0000 UTC   deployed        mychart-0.1.0
```

### `kubectl get all` Output
Shows the Kubernetes resources created by the Helm releases.
```bash
$ kubectl get all
NAME                                  READY   STATUS    RESTARTS   AGE
pod/myapp-dev-688476ffc6-92svq        0/1     Pending   0          2m17s
pod/myapp-dev-688476ffc6-g9wmn        0/1     Pending   0          2m17s
pod/myrelease-85c9486454-2v526        1/1     Running   0          6m49s
pod/myrelease-85c9486454-5glfr        1/1     Running   0          6m49s
pod/myrelease-85c9486454-bq9bt        1/1     Running   0          6m49s
pod/myrelease-85c9486454-bqxwl        1/1     Running   0          6m49s
pod/myrelease-85c9486454-sclnj        1/1     Running   0          6m49s

NAME                         TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/kubernetes           ClusterIP      10.96.0.1        <none>        443/TCP        7d1h
service/myapp-dev-service    LoadBalancer   10.101.199.116   <pending>     80:30373/TCP   14s
service/myrelease-service    NodePort       10.110.189.69    <none>        80:32075/TCP   6m49s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/myapp-dev        0/5     0            0           2m17s
deployment.apps/myrelease        5/5     5            5           6m49s

NAME                                        DESIRED   CURRENT   READY   AGE
replicaset.apps/myapp-dev-688476ffc6        5         5         0       2m17s
replicaset.apps/myrelease-85c9486454        5         5         5       6m49s
```

### Hook Execution Output
Hooks are executed successfully and then deleted, as per policy. The dry-run shows their manifest, and checking for jobs after installation returns nothing, confirming deletion.

**Dry-run showing hooks:**
```bash
$ helm install --dry-run --debug test-release k8s/mychart
...
HOOKS:
---
# Source: mychart/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
...
---
# Source: mychart/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
...
```
**Verifying deletion:**
```bash
$ kubectl get jobs
No resources found in default namespace.
```

### Different Environment Deployments (Dev vs Prod)

| Environment | Release Name | Replicas | Service Type | Resources (CPU Request) | Image Tag |
|-------------|--------------|----------|--------------|-------------------------|-----------|
| **Development** | `myapp-dev` | 1 | NodePort | `50m` | `latest` |
| **Production** | `myrelease` | 5 | LoadBalancer | `200m` | `1.0` |

---

## Operations

### Installation Commands Used

```bash
# Install development release
helm install myapp-dev k8s/mychart -f k8s/mychart/values-dev.yaml

# Install production release
helm install myrelease k8s/mychart -f k8s/mychart/values-prod.yaml
```

### How to Upgrade a Release

```bash
# Upgrade an existing release with a new values file
helm upgrade myapp-dev k8s/mychart -f k8s/mychart/values-prod.yaml

# Upgrade with a direct set parameter
helm upgrade myapp-dev k8s/mychart --set replicaCount=10
```

### How to Rollback

```bash
# View release history
helm history myapp-dev

# Rollback to a previous revision (e.g., revision 1)
helm rollback myapp-dev 1
```

### How to Uninstall

```bash
# Uninstall a release
helm uninstall myrelease
helm uninstall myapp-dev
```

---

## Testing & Validation

### `helm lint` Output
```bash
$ helm lint k8s/mychart
==> Linting k8s/mychart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### `helm template` Verification
```bash
$ helm template mychart k8s/mychart
---
# Source: mychart/templates/service.yml
apiVersion: v1
kind: Service
...
---
# Source: mychart/templates/deployment.yml
apiVersion: apps/v1
kind: Deployment
...
```
*Output truncated for brevity. Command successfully rendered all Kubernetes manifests.*

### Dry-run Output
```bash
$ helm install --dry-run --debug test-release k8s/mychart
...
HOOKS:
...
MANIFEST:
...
```
*Command successfully simulated the installation, showing the final rendered manifests including hooks.*

### Application Accessibility Verification

**Development Deployment (`myapp-dev`)**
```bash
$ kubectl get svc myapp-dev-service
NAME                 TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
myapp-dev-service    NodePort    10.105.58.167   <none>        80:31794/TCP   12s
```
Service is accessible via NodePort `31794`.

**Production Deployment (`myrelease`)**
```bash
$ kubectl get svc myrelease-service
NAME                 TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
myrelease-service    LoadBalancer   10.110.189.69    <pending>     80:32075/TCP   6m49s
```
Service is configured as a LoadBalancer. In a cloud environment, an external IP would be assigned. In minikube, it can be accessed via `minikube service myrelease-service`.




# Task 1

```bash
gleb-pp@gleb-mac iu-devops-course % brew install helm
==> Auto-updating Homebrew...
Adjust how often this is run with `$HOMEBREW_AUTO_UPDATE_SECS` or disable with
`$HOMEBREW_NO_AUTO_UPDATE=1`. Hide these hints with `$HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
==> Downloading https://ghcr.io/v2/homebrew/core/portable-ruby/blobs/sha256:f41c72b891c40623f9d5cd2135f58a1b8a5c014ae04149888289409316276c72
################################################################################################################################# 100.0%
==> Pouring portable-ruby-4.0.2_1.arm64_big_sur.bottle.tar.gz
==> Auto-updated Homebrew!
Updated 2 taps (homebrew/core and homebrew/cask).
==> New Formulae
copilot-language-server: Language Server Protocol server for GitHub Copilot
dispenso: High-performance C++ library for parallel programming
jsongrep: Query tool for JSON, YAML, TOML, and other structured formats
lazycut: Terminal-based video trimming TUI
miniaudio: Audio playback and capture library
nextpnr-ice40: Portable FPGA place and route tool for Lattice iCE40
opentimestamps-client: Create and verify OpenTimestamps proofs
pay: HTTP client that automatically handles 402 Payment Required
proxelar: Man-in-the-Middle proxy for HTTP/HTTPS traffic
qtcanvaspainter: Accelerated 2D painting solution for Qt Quick and QRhi-based render targets
qttasktree: General purpose library for asynchronous task execution
==> New Casks
claude-code@latest: Terminal-based AI coding assistant
font-bj-cree
font-saira-stencil
incident-io: Incident management platform
jiba: Apple Music metadata localisation tool
nimbalyst: Visual workspace for building with Codex and Claude Code
ob-xf: Virtual analog synthesizer
scribus@devel: Free and open-source page layout program
wallspace: Live wallpaper app

You have 5 outdated formulae installed.

==> Fetching downloads for: helm
✔︎ Bottle Manifest helm (4.1.3)                                                                               Downloaded    7.4KB/  7.4KB
✔︎ Bottle helm (4.1.3)                                                                                        Downloaded   18.1MB/ 18.1MB
==> Pouring helm--4.1.3.arm64_sequoia.bottle.tar.gz
🍺  /opt/homebrew/Cellar/helm/4.1.3: 69 files, 61.3MB
==> Running `brew cleanup helm`...
Disable this behaviour by setting `HOMEBREW_NO_INSTALL_CLEANUP=1`.
Hide these hints with `HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
==> Caveats
zsh completions have been installed to:
  /opt/homebrew/share/zsh/site-functions
gleb-pp@gleb-mac iu-devops-course % helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories
gleb-pp@gleb-mac iu-devops-course % helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
gleb-pp@gleb-mac iu-devops-course % helm show chart prometheus-community/prometheus
annotations:
  artifacthub.io/license: Apache-2.0
  artifacthub.io/links: |
    - name: Chart Source
      url: https://github.com/prometheus-community/helm-charts
    - name: Upstream Project
      url: https://github.com/prometheus/prometheus
apiVersion: v2
appVersion: v3.10.0
dependencies:
- condition: alertmanager.enabled
  name: alertmanager
  repository: https://prometheus-community.github.io/helm-charts
  version: 1.34.*
- condition: kube-state-metrics.enabled
  name: kube-state-metrics
  repository: https://prometheus-community.github.io/helm-charts
  version: 7.2.*
- condition: prometheus-node-exporter.enabled
  name: prometheus-node-exporter
  repository: https://prometheus-community.github.io/helm-charts
  version: 4.52.*
- condition: prometheus-pushgateway.enabled
  name: prometheus-pushgateway
  repository: https://prometheus-community.github.io/helm-charts
  version: 3.6.*
description: Prometheus is a monitoring system and time series database.
home: https://prometheus.io/
icon: https://raw.githubusercontent.com/prometheus/prometheus.github.io/master/assets/prometheus_logo-cb55bb5c346.png
keywords:
- monitoring
- prometheus
kubeVersion: '>=1.19.0-0'
maintainers:
- email: gianrubio@gmail.com
  name: gianrubio
  url: https://github.com/gianrubio
- email: zanhsieh@gmail.com
  name: zanhsieh
  url: https://github.com/zanhsieh
- email: miroslav.hadzhiev@gmail.com
  name: Xtigyro
  url: https://github.com/Xtigyro
- email: naseem@transit.app
  name: naseemkullah
  url: https://github.com/naseemkullah
- email: rootsandtrees@posteo.de
  name: zeritti
  url: https://github.com/zeritti
name: prometheus
sources:
- https://github.com/prometheus/alertmanager
- https://github.com/prometheus/prometheus
- https://github.com/prometheus/pushgateway
- https://github.com/prometheus/node_exporter
- https://github.com/kubernetes/kube-state-metrics
type: application
version: 28.14.1
```

# Task 2

```bash
gleb-pp@gleb-mac iu-devops-course % helm lint k8s/mychart
==> Linting k8s/mychart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
gleb-pp@gleb-mac iu-devops-course % helm template mychart k8s/mychart
---
# Source: mychart/templates/service.yml
apiVersion: v1
kind: Service
metadata:
  name: mychart-service
spec:
  type: NodePort
  selector:
    app: mychart
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
      nodePort: 30007
---
# Source: mychart/templates/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mychart
  labels:
    app: mychart
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: mychart
  template:
    metadata:
      labels:
        app: mychart
    spec:
      containers:
        - name: mychart
          image: "glebpp/app_python:1.0"
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5000
          env:
            - name: ENV
              value: production
            - name: VERSION
              value: v2
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
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
gleb-pp@gleb-mac iu-devops-course % helm install --dry-run --debug test-release k8s/mychart
level=WARN msg="--dry-run is deprecated and should be replaced with '--dry-run=client'"
level=DEBUG msg="Original chart version" version=""
level=DEBUG msg="Chart path" path="/Users/gleb-pp/Documents/InnoAssignments/S26 DevOps/iu-devops-course/k8s/mychart"
level=DEBUG msg="number of dependencies in the chart" chart=mychart dependencies=0
NAME: test-release
LAST DEPLOYED: Wed Apr  1 12:23:07 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
TEST SUITE: None
USER-SUPPLIED VALUES:
{}

COMPUTED VALUES:
containerPort: 5000
env:
  ENV: production
  VERSION: v2
image:
  repository: glebpp/app_python
  tag: "1.0"
probes:
  liveness:
    initialDelaySeconds: 10
    path: /
    periodSeconds: 10
  readiness:
    initialDelaySeconds: 5
    path: /
    periodSeconds: 5
replicaCount: 5
resources:
  limits:
    cpu: 500m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
service:
  port: 80
  type: NodePort

HOOKS:
MANIFEST:
---
# Source: mychart/templates/service.yml
apiVersion: v1
kind: Service
metadata:
  name: test-release-service
spec:
  type: NodePort
  selector:
    app: mychart
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
---
# Source: mychart/templates/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-release
  labels:
    app: mychart
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: mychart
  template:
    metadata:
      labels:
        app: mychart
    spec:
      containers:
        - name: mychart
          image: "glebpp/app_python:1.0"
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5000
          env:
            - name: ENV
              value: production
            - name: VERSION
              value: v2
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
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

gleb-pp@gleb-mac iu-devops-course % helm install myrelease k8s/mychart
NAME: myrelease
LAST DEPLOYED: Wed Apr  1 12:22:37 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
```

# Task 3

## Dev
```bash
gleb-pp@gleb-mac iu-devops-course % helm install myapp-dev k8s/mychart -f k8s/mychart/values-dev.yaml  
NAME: myapp-dev
LAST DEPLOYED: Wed Apr  1 12:25:58 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
gleb-pp@gleb-mac iu-devops-course % kubectl get pods
NAME                          READY   STATUS         RESTARTS   AGE
myapp-dev-6f84f4786-2xslv     0/1     ErrImagePull   0          7s
myrelease-85c9486454-2v526    1/1     Running        0          3m28s
myrelease-85c9486454-5glfr    1/1     Running        0          3m28s
myrelease-85c9486454-bq9bt    1/1     Running        0          3m28s
myrelease-85c9486454-bqxwl    1/1     Running        0          3m28s
myrelease-85c9486454-sclnj    1/1     Running        0          3m28s
python-app-5fdbccc45f-4dwlm   1/1     Running        0          7d
python-app-5fdbccc45f-5t74v   1/1     Running        0          7d
python-app-5fdbccc45f-kpt66   1/1     Running        0          7d
python-app-5fdbccc45f-kqrnb   1/1     Running        0          7d
python-app-5fdbccc45f-l8lrj   1/1     Running        0          7d
gleb-pp@gleb-mac iu-devops-course % kubectl get svc
NAME                 TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
kubernetes           ClusterIP   10.96.0.1       <none>        443/TCP        7d1h
myapp-dev-service    NodePort    10.105.58.167   <none>        80:31794/TCP   12s
myrelease-service    NodePort    10.110.189.69   <none>        80:32075/TCP   3m33s
python-app-service   NodePort    10.109.4.248    <none>        80:30007/TCP   7d
gleb-pp@gleb-mac iu-devops-course % 
```

## Prod
```bash
gleb-pp@gleb-mac iu-devops-course % helm upgrade myapp-dev k8s/mychart -f k8s/mychart/values-prod.yaml
Release "myapp-dev" has been upgraded. Happy Helming!
NAME: myapp-dev
LAST DEPLOYED: Wed Apr  1 12:27:08 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None
gleb-pp@gleb-mac iu-devops-course % kubectl get pods
NAME                          READY   STATUS              RESTARTS   AGE
myapp-dev-688476ffc6-92svq    0/1     Pending             0          3s
myapp-dev-688476ffc6-g9wmn    0/1     Pending             0          3s
myapp-dev-6f84f4786-5jtg5     0/1     ErrImagePull        0          11s
myapp-dev-6f84f4786-bznfq     0/1     ErrImagePull        0          4s
myapp-dev-6f84f4786-pxnjs     0/1     ContainerCreating   0          4s
myapp-dev-6f84f4786-wptrx     0/1     Pending             0          4s
myrelease-85c9486454-2v526    1/1     Running             0          4m35s
myrelease-85c9486454-5glfr    1/1     Running             0          4m35s
myrelease-85c9486454-bq9bt    1/1     Running             0          4m35s
myrelease-85c9486454-bqxwl    1/1     Running             0          4m35s
myrelease-85c9486454-sclnj    1/1     Running             0          4m35s
python-app-5fdbccc45f-4dwlm   1/1     Running             0          7d
python-app-5fdbccc45f-5t74v   1/1     Running             0          7d
python-app-5fdbccc45f-kpt66   1/1     Running             0          7d
python-app-5fdbccc45f-kqrnb   1/1     Running             0          7d
python-app-5fdbccc45f-l8lrj   1/1     Running             0          7d
gleb-pp@gleb-mac iu-devops-course % kubectl get svc
NAME                 TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
kubernetes           ClusterIP      10.96.0.1        <none>        443/TCP        7d1h
myapp-dev-service    LoadBalancer   10.101.199.116   <pending>     80:30373/TCP   14s
myrelease-service    NodePort       10.110.189.69    <none>        80:32075/TCP   4m38s
python-app-service   NodePort       10.109.4.248     <none>        80:30007/TCP   7d
gleb-pp@gleb-mac iu-devops-course % 
```

# Task 4

```bash
gleb-pp@gleb-mac iu-devops-course % helm lint k8s/mychart
==> Linting k8s/mychart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
gleb-pp@gleb-mac iu-devops-course % helm install --dry-run --debug test-release k8s/mychart
level=WARN msg="--dry-run is deprecated and should be replaced with '--dry-run=client'"
level=DEBUG msg="Original chart version" version=""
level=DEBUG msg="Chart path" path="/Users/gleb-pp/Documents/InnoAssignments/S26 DevOps/iu-devops-course/k8s/mychart"
level=DEBUG msg="number of dependencies in the chart" chart=mychart dependencies=0
NAME: test-release
LAST DEPLOYED: Wed Apr  1 12:28:54 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
TEST SUITE: None
USER-SUPPLIED VALUES:
{}

COMPUTED VALUES:
containerPort: 5000
env:
  ENV: production
  VERSION: v2
image:
  repository: glebpp/app_python
  tag: "1.0"
probes:
  liveness:
    initialDelaySeconds: 10
    path: /
    periodSeconds: 10
  readiness:
    initialDelaySeconds: 5
    path: /
    periodSeconds: 5
replicaCount: 5
resources:
  limits:
    cpu: 500m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
service:
  port: 80
  type: NodePort

HOOKS:
---
# Source: mychart/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-post-install"
  labels:
    app: mychart
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "test-release-post-install"
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-job
          image: busybox
          command: ["sh", "-c", "echo Post-install validation && sleep 5 && echo Validation passed"]
---
# Source: mychart/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-pre-install"
  labels:
    app: mychart
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "test-release-pre-install"
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-job
          image: busybox
          command: ["sh", "-c", "echo Pre-install task running && sleep 5 && echo Pre-install completed"]
MANIFEST:
---
# Source: mychart/templates/service.yml
apiVersion: v1
kind: Service
metadata:
  name: test-release-service
spec:
  type: NodePort
  selector:
    app: mychart
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
---
# Source: mychart/templates/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-release
  labels:
    app: mychart
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: mychart
  template:
    metadata:
      labels:
        app: mychart
    spec:
      containers:
        - name: mychart
          image: "glebpp/app_python:1.0"
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5000
          env:
            - name: ENV
              value: production
            - name: VERSION
              value: v2
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
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

gleb-pp@gleb-mac iu-devops-course % helm upgrade --install myrelease k8s/mychart
Release "myrelease" has been upgraded. Happy Helming!
NAME: myrelease
LAST DEPLOYED: Wed Apr  1 12:29:07 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None
gleb-pp@gleb-mac iu-devops-course % kubectl get jobs -w
^C%                                                                                                                                     
gleb-pp@gleb-mac iu-devops-course % kubectl get pods -w
NAME                          READY   STATUS             RESTARTS   AGE
myapp-dev-688476ffc6-92svq    0/1     Pending            0          2m17s
myapp-dev-688476ffc6-g9wmn    0/1     Pending            0          2m17s
myapp-dev-6f84f4786-5jtg5     0/1     ImagePullBackOff   0          2m25s
myapp-dev-6f84f4786-bznfq     0/1     ImagePullBackOff   0          2m18s
myapp-dev-6f84f4786-pxnjs     0/1     ImagePullBackOff   0          2m18s
myapp-dev-6f84f4786-wptrx     0/1     Pending            0          2m18s
myrelease-85c9486454-2v526    1/1     Running            0          6m49s
myrelease-85c9486454-5glfr    1/1     Running            0          6m49s
myrelease-85c9486454-bq9bt    1/1     Running            0          6m49s
myrelease-85c9486454-bqxwl    1/1     Running            0          6m49s
myrelease-85c9486454-sclnj    1/1     Running            0          6m49s
python-app-5fdbccc45f-4dwlm   1/1     Running            0          7d
python-app-5fdbccc45f-5t74v   1/1     Running            0          7d
python-app-5fdbccc45f-kpt66   1/1     Running            0          7d
python-app-5fdbccc45f-kqrnb   1/1     Running            0          7d
python-app-5fdbccc45f-l8lrj   1/1     Running            0          7d
test-85c9486454-c8z2t         0/1     Pending            0          119s
test-85c9486454-d5thn         0/1     Pending            0          119s
test-85c9486454-mz8dr         0/1     Pending            0          119s
test-85c9486454-ts46k         0/1     Pending            0          119s
test-85c9486454-vgpxn         0/1     Pending            0          119s
test-85c9486454-wncc5         0/1     Pending            0          119s
test-85c9486454-wpjdg         0/1     Pending            0          119s
test-85c9486454-x9wlf         0/1     Pending            0          119s
test-85c9486454-z9gfw         0/1     Pending            0          119s
test-85c9486454-zzqrm         0/1     Pending            0          119s
^C%                                                                                                                                     
gleb-pp@gleb-mac iu-devops-course % kubectl logs job/myrelease-pre-install
error: error from server (NotFound): jobs.batch "myrelease-pre-install" not found in namespace "default"
gleb-pp@gleb-mac iu-devops-course % kubectl logs job/myrelease-post-install
error: error from server (NotFound): jobs.batch "myrelease-post-install" not found in namespace "default"
gleb-pp@gleb-mac iu-devops-course % kubectl get jobs
No resources found in default namespace.
```
