# Lab 14 — Progressive Delivery with Argo Rollouts

## Architecture Overview

This lab implements progressive delivery strategies using Argo Rollouts to replace standard Kubernetes Deployments. Two advanced deployment strategies were implemented:

1. **Canary Deployment** – Gradual traffic shifting from 20% to 100% with manual and automated pauses
2. **Blue-Green Deployment** – Instant traffic switching between active and preview environments

All experiments were performed on a local Kubernetes cluster (minikube) using a Helm chart extended from Lab 13 (ArgoCD).

**Tech Stack:**
- Kubernetes (minikube)
- Argo Rollouts 1.8.3 (Controller + Dashboard)
- Helm Charts
- kubectl-argo-rollouts plugin
- Python FastAPI application with Vault integration, ConfigMaps, and PVC

## Task 1 — Argo Rollouts Fundamentals (2 pts)

### Objective
Install Argo Rollouts, verify the Rollout CRD, and understand the differences from standard Deployments.

### 1.1 Argo Rollouts Controller Installation

Installed via `kubectl` in dedicated namespace:

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

**Verification:**
```bash
kubectl get pods -n argo-rollouts
NAME                            READY   STATUS    RESTARTS   AGE
argo-rollouts-5f64f8d68-wrrgz   1/1     Running   0          11m
```

### 1.2 kubectl Plugin Installation

Installed via Homebrew on macOS:

```bash
brew install argoproj/tap/kubectl-argo-rollouts
kubectl argo rollouts version
```

**Output:**
```
kubectl-argo-rollouts: v1.8.3+49fa151
  BuildDate: 2025-06-04T22:19:21Z
  GitCommit: 49fa1516cf71672b69e265267da4e1d16e1fe114
  GoVersion: go1.23.9
  Platform: darwin/amd64
```

### 1.3 Argo Rollouts Dashboard

Installed and accessed via port-forward:

```bash
kubectl apply -n argo-rollouts \
  -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml

kubectl -n argo-rollouts port-forward svc/argo-rollouts-dashboard 3100:3100
```

Dashboard available at: `http://localhost:3100`

### 1.4 Rollout vs Deployment — Key Differences

| Feature | Standard Deployment | Argo Rollout |
|---------|---------------------|--------------|
| Rolling update | ✅ Basic | ✅ Advanced |
| Canary strategy | ❌ | ✅ With traffic weights |
| Blue-Green strategy | ❌ | ✅ With preview service |
| Pause & resume | ❌ | ✅ Manual or timed |
| Metrics-based analysis | ❌ | ✅ Prometheus integration |
| Automated rollback | ❌ | ✅ Based on analysis |
| Traffic splitting | ❌ | ✅ Weight-based |

**Additional fields in Rollout CRD:**
- `strategy.canary.steps` – Defines progressive traffic weights and pauses
- `strategy.blueGreen` – Defines active/preview services
- `spec.analysis` – Metrics-based success/failure criteria

## Task 2 — Canary Deployment (3 pts)

### Objective
Convert existing Deployment to Rollout with canary strategy and progressive traffic shifting.

### 2.1 Canary Strategy Configuration

Created `rollout.yaml` in Helm chart with the following strategy:

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - pause: {}          # Manual promotion

      - setWeight: 40
      - pause:
          duration: 30s

      - setWeight: 60
      - pause:
          duration: 30s

      - setWeight: 80
      - pause:
          duration: 30s
```

### 2.2 Initial Deployment

```bash
helm upgrade --install myapp k8s/mychart
kubectl get rollouts
NAME    DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
myapp   5         5         5            5           17s
```

### 2.3 Trigger Canary Rollout

Modified `values.yaml` to change version:

```yaml
env:
  ENV: "production"
  VERSION: "v3"
```

Applied the change:

```bash
helm upgrade myapp k8s/mychart
```

### 2.4 Rollout Progression

**Step 1 – 20% weight (Paused for manual promotion):**
```bash
kubectl argo rollouts get rollout myapp --watch
```

```
Name:            myapp
Status:          ॥ Paused
Message:         CanaryPauseStep
Strategy:        Canary
  Step:          1/8
  SetWeight:     20
  ActualWeight:  20
Images:          glebpp/app_python:1.0 (canary, stable)
Replicas:
  Desired:       5
  Current:       5
  Updated:       1
  Ready:         5
```

**Manual promotion:**
```bash
kubectl argo rollouts promote myapp
```

**Automatic progression (40% → 60% → 80% → 100%):**  
Each subsequent step progressed automatically after 30-second pauses.

### 2.5 Canary Rollback Test

During an active rollout, aborted the process:

```bash
kubectl argo rollouts abort myapp
```

**Result:** Traffic immediately shifted back to the stable (previous) version. New ReplicaSet was scaled down, and original version continued serving all traffic.

## Task 3 — Blue-Green Deployment (3 pts)

### Objective
Implement blue-green deployment with separate active/preview services and instant traffic switching.

### 3.1 Service Configuration

Created two separate services (replaced single `service.yml`):

**`service-active.yaml`:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}-active
spec:
  type: {{ .Values.service.type }}
  selector:
    app: {{ .Chart.Name }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: {{ .Values.containerPort }}
```

**`service-preview.yaml`:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}-preview
spec:
  type: {{ .Values.service.type }}
  selector:
    app: {{ .Chart.Name }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: {{ .Values.containerPort }}
```

### 3.2 Blue-Green Strategy Configuration

Updated `rollout.yaml` with blue-green strategy:

```yaml
strategy:
  blueGreen:
    activeService: {{ .Release.Name }}-active
    previewService: {{ .Release.Name }}-preview
    autoPromotionEnabled: false   # Manual promotion required
```

### 3.3 Initial Blue Deployment

```bash
helm upgrade --install myapp k8s/mychart
kubectl argo rollouts get rollout myapp
```

```
Name:            myapp
Status:          Healthy
Strategy:        BlueGreen
Images:          glebpp/app_python:1.0 (stable)
```

**Services created:**
```bash
kubectl get svc
NAME            TYPE        CLUSTER-IP       PORT(S)        AGE
myapp-active    NodePort    10.108.254.116   80:30858/TCP   83s
myapp-preview   NodePort    10.103.190.196   80:31399/TCP   83s
```

### 3.4 Trigger Green Deployment

Modified `values.yaml` to deploy new version:

```yaml
env:
  VERSION: "v4"
```

```bash
helm upgrade myapp k8s/mychart
```

**Rollout status during preview:**
```bash
kubectl argo rollouts get rollout myapp
```

```
Name:            myapp
Status:          ॥ Paused
Strategy:        BlueGreen
Images:          glebpp/app_python:1.0 (stable, preview)
Replicas:
  Desired:       5
  Current:       5
  Updated:       5
  Ready:         5
```

### 3.5 Preview Environment Testing

Accessed new version via preview service before promotion:

```bash
# Preview service NodePort: 31399
curl http://localhost:31399/
```

New version (v4) was verified without affecting production traffic.

### 3.6 Promotion to Active

```bash
kubectl argo rollouts promote myapp
```

**Result:** Instant traffic switch – preview service became active, old version became inactive. No gradual traffic shifting, complete cutover in milliseconds.

### 3.7 Instant Rollback Test

```bash
kubectl argo rollouts undo myapp
```

**Result:** Previous version immediately became active again. Rollback completed in <1 second, significantly faster than canary rollback.

## Task 4 — Documentation (2 pts)

### Argo Rollouts Setup Summary

| Component | Status | Access |
|-----------|--------|--------|
| Controller | ✅ Running in `argo-rollouts` namespace | `kubectl get pods -n argo-rollouts` |
| CRDs | ✅ Installed | `kubectl get crd \| grep argoproj` |
| kubectl plugin | ✅ v1.8.3 | `kubectl argo rollouts version` |
| Dashboard | ✅ Deployed | `http://localhost:3100` (port-forward) |

### Canary vs Blue-Green Comparison

| Aspect | Canary | Blue-Green |
|--------|--------|------------|
| **Traffic shifting** | Gradual (20% → 40% → 60% → 80% → 100%) | Instant (100% switch at promotion) |
| **Rollback speed** | Gradual (depends on current weight) | Instant (<1 second) |
| **Preview environment** | ❌ No separate preview | ✅ Preview service for testing |
| **Risk profile** | Low (gradual exposure) | Medium (all-or-nothing switch) |
| **Production impact** | Minimal (small % first) | Potential full impact if new version has issues |
| **Best for** | High-traffic APIs, microservices | UI applications, batch jobs |

### Strategy Recommendations

**Use Canary when:**
- Serving critical production traffic where gradual exposure reduces blast radius
- You have good observability and can detect issues at low percentages
- Need fine-grained control over rollout pace

**Use Blue-Green when:**
- You need to test new version in production-like environment before release
- Instant rollback capability is critical
- Application state doesn't require gradual migration (stateless)

### Useful CLI Commands

```bash
# List all rollouts
kubectl argo rollouts list rollouts -A

# Get rollout details
kubectl argo rollouts get rollout <name>

# Watch rollout progression
kubectl argo rollouts get rollout <name> --watch

# Promote to next step (canary) or switch (blue-green)
kubectl argo rollouts promote <name>

# Abort ongoing rollout
kubectl argo rollouts abort <name>

# Rollback to previous version
kubectl argo rollouts undo <name>

# Rollback to specific revision
kubectl argo rollouts undo <name> --to-revision=<N>

# Dashboard access
kubectl -n argo-rollouts port-forward svc/argo-rollouts-dashboard 3100:3100
```

### Verification Evidence

**Rollout CRD installed:**
```bash
kubectl get crd | grep rollouts
rollouts.argoproj.io                             2026-04-19T11:30:10Z
```

**Canary rollout with paused step:**
```
Strategy: Canary
Step: 1/8
SetWeight: 20
ActualWeight: 20
```

**Blue-green strategy active:**
```
Strategy: BlueGreen
Status: Healthy
```

**Both services operational:**
```
myapp-active    NodePort    10.108.254.116   80:30858/TCP
myapp-preview   NodePort    10.103.190.196   80:31399/TCP
```

## Challenges Encountered & Resolutions

| Challenge | Resolution |
|-----------|------------|
| Helm upgrade conflict with existing rollout (`conflicts with "kubectl-argo-rollouts"`) | Deleted existing rollout with `kubectl delete rollout myapp` before applying new strategy |
| Both `rollout.yaml` (canary) and `rollout-bluegreen.yaml` present simultaneously | Removed canary file, kept only blue-green, renamed to `rollout.yaml` |
| `kubectl argo rollouts undo` warning about `creationTimestamp` | Warning ignored — rollback still succeeded. For clean rollbacks, used `--to-revision` flag |
| Preview service testing attempted as shell command (`myapp-preview`) | Correct approach: use NodePort URL (`http://localhost:31399`) or `minikube service myapp-preview` |
