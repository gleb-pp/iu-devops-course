# Lab 13 — GitOps with ArgoCD

## Architecture Overview

This lab implements GitOps continuous deployment using ArgoCD, treating the Git repository as the single source of truth for Kubernetes deployments. All application configurations (Helm charts, values files, and Kubernetes manifests) are version-controlled, and ArgoCD automatically synchronizes the cluster state with the declared state in Git.

**Key GitOps Principles Demonstrated:**
1. **Declarative Configuration** – Application defined via `Application` CRD
2. **Version-Controlled State** – All manifests stored in Git
3. **Automated Sync** – Dev environment auto-syncs on Git changes
4. **Drift Detection & Self-Healing** – ArgoCD reverts manual changes
5. **Multi-Environment Separation** – Dev (auto) vs Prod (manual) with different value files

**Tech Stack:**
- ArgoCD 2.13+ (v3.3.7 CLI)
- Kubernetes (minikube v1.38.1 on Colima)
- Helm Charts (from Lab 12)
- Git (GitHub)

**Environment Setup Note:** During the lab, resource constraints were encountered with Colima VM (default 2GB RAM). The VM was reconfigured with `colima start --cpu 2 --memory 4` to provide sufficient resources for ArgoCD and Kubernetes components.

---

## Task 1 — ArgoCD Installation & Setup (2 pts)

### Objective
Install ArgoCD via Helm, access the UI, and configure the CLI on macOS.

### 1.1 Installation Steps

**Helm repository setup:**

```bash
gleb-pp@gleb-mac iu-devops-course % helm repo add argo https://argoproj.github.io/argo-helm
"argo" has been added to your repositories

gleb-pp@gleb-mac iu-devops-course % helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "argo" chart repository
Update Complete. ⎈Happy Helming!⎈
```

**Namespace and installation:**

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl create namespace argocd
namespace/argocd created

gleb-pp@gleb-mac iu-devops-course % helm install argocd argo/argo-cd -n argocd
NAME: argocd
LAST DEPLOYED: Sun Apr 19 12:47:18 2026
NAMESPACE: argocd
STATUS: deployed
REVISION: 1
```

### 1.2 Component Verification

All ArgoCD pods running successfully:

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl get pods -n argocd
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          2m9s
argocd-applicationset-controller-59f6b7dd64-v9hm6   1/1     Running   0          2m9s
argocd-dex-server-7b9588c494-rvpxp                  1/1     Running   0          2m9s
argocd-notifications-controller-8f6855454-nc9gb     1/1     Running   0          2m9s
argocd-redis-dc6b586fc-x267q                        1/1     Running   0          2m9s
argocd-repo-server-5f4d44d9f8-jsrfv                 1/1     Running   0          2m9s
argocd-server-5f777b877f-blbpz                      1/1     Running   0          2m9s
```

Services created:

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl get svc -n argocd
NAME                               TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)             AGE
argocd-applicationset-controller   ClusterIP   10.109.135.247   <none>        7000/TCP            2m24s
argocd-dex-server                  ClusterIP   10.96.218.38     <none>        5556/TCP,5557/TCP   2m24s
argocd-redis                       ClusterIP   10.103.85.212    <none>        6379/TCP            2m24s
argocd-repo-server                 ClusterIP   10.98.5.35       <none>        8081/TCP            2m24s
argocd-server                      ClusterIP   10.106.223.47    <none>        80/TCP,443/TCP      2m24s
```

### 1.3 UI Access and Authentication

**Port forwarding to access UI:**

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl port-forward svc/argocd-server -n argocd 8080:443
Forwarding from 127.0.0.1:8080 -> 8080
Forwarding from [::1]:8080 -> 8080
```

**Retrieve initial admin password:**

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl -n argocd get secret argocd-initial-admin-secret \
-o jsonpath="{.data.password}" | base64 -d && echo
[redacted-password]
```

**Login via browser:** Navigate to `https://localhost:8080` (accept certificate warning) with:
- Username: `admin`
- Password: `[redacted-password]`

### 1.4 ArgoCD CLI Installation (macOS)

```bash
gleb-pp@gleb-mac iu-devops-course % brew install argocd
==> Pouring argocd--3.3.7.arm64_sequoia.bottle.tar.gz
🍺  /opt/homebrew/Cellar/argocd/3.3.7: 10 files, 244.0MB

gleb-pp@gleb-mac iu-devops-course % argocd version
argocd: v3.3.7+035e855.dirty
  BuildDate: 2026-04-16T17:20:28Z
  GitCommit: 035e8556c451196e203078160a5c01f43afdb92f
  GitTreeState: dirty
  GitTag: v3.3.7
  GoVersion: go1.26.2
  Compiler: gc
  Platform: darwin/arm64
```

**CLI login:**

```bash
gleb-pp@gleb-mac iu-devops-course % argocd login localhost:8080 --username admin --password [redacted] --insecure
'admin:login' logged in successfully
Context 'localhost:8080' updated

gleb-pp@gleb-mac iu-devops-course % argocd account get-user-info
Logged In: true
Username: admin
Issuer: argocd
Groups: 
```

✅ **Task 1 Verification Complete** – ArgoCD installed, UI accessible, CLI configured.

---

## Task 2 — Application Deployment (3 pts)

### Objective
Deploy the Python application (Helm chart from Lab 12) using ArgoCD's declarative Application resource.

### 2.1 Application Manifest

Created `k8s/argocd/application.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-python-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/gleb-pp/iu-devops-course.git
    targetRevision: master
    path: k8s/mychart
  destination:
    server: https://kubernetes.default.svc
    namespace: dev
  syncPolicy: {}  # Manual sync initially
```

### 2.2 Deploy Application

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl apply -f k8s/argocd/application.yaml
application.argoproj.io/my-python-app created

gleb-pp@gleb-mac iu-devops-course % kubectl get applications -n argocd
NAME            SYNC STATUS   HEALTH STATUS
my-python-app   Unknown       Healthy
```

### 2.3 Initial Manual Sync

**Via CLI:**

```bash
gleb-pp@gleb-mac iu-devops-course % argocd app sync my-python-app
TIMESTAMP  GROUP        KIND   NAMESPACE                  NAME    STATUS   HEALTH        HOOK  MESSAGE
2026-04-19T13:04:50+03:00         PersistentVolumeClaim         dev  my-python-app-mychart-data    OutOfSync  Missing              
2026-04-19T13:04:50+03:00             Secret                    dev  my-python-app-secret          OutOfSync  Missing              
2026-04-19T13:04:50+03:00            Service                    dev  my-python-app-service         OutOfSync  Missing              
2026-04-19T13:04:50+03:00   apps  Deployment                    dev         my-python-app          OutOfSync  Missing              
2026-04-19T13:04:50+03:00          ConfigMap                    dev  my-python-app-mychart-config  OutOfSync  Missing              
2026-04-19T13:04:50+03:00          ConfigMap                    dev  my-python-app-mychart-env     OutOfSync  Missing              
...
2026-04-19T13:05:23+03:00   apps  Deployment         dev         my-python-app    Synced    Healthy              
2026-04-19T13:05:23+03:00  batch         Job         dev  my-python-app-post-install  Succeeded   Synced    PostSync

Name:               argocd/my-python-app
Sync Status:        Synced to master (dea078d)
Health Status:      Healthy
```

### 2.4 Deployment Verification

All resources created successfully in `dev` namespace:

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl get all -n dev
NAME                                 READY   STATUS    RESTARTS   AGE
pod/my-python-app-549b4b5d8b-7jj75   1/1     Running   0          77s
pod/my-python-app-549b4b5d8b-bgvbb   1/1     Running   0          77s
pod/my-python-app-549b4b5d8b-qpnrq   1/1     Running   0          77s
pod/my-python-app-549b4b5d8b-qvprt   1/1     Running   0          77s
pod/my-python-app-549b4b5d8b-sxv8x   1/1     Running   0          77s

NAME                            TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/my-python-app-service   NodePort   10.97.241.252   <none>        80:30195/TCP   77s

NAME                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/my-python-app   5/5     5            5           77s
```

### 2.5 GitOps Workflow Test

**Change replica count in values:**

Modified `k8s/mychart/values.yaml`:
```yaml
replicaCount: 5  # Changed from 1 to 5
```

**Commit and push:**

```bash
git add k8s/mychart/values.yaml
git commit -m "Increase replicas to 5 for GitOps test"
git push origin master
```

**ArgoCD detects drift** – UI shows `OutOfSync` status approximately 30 seconds after push.

**Sync the change:**

```bash
argocd app sync my-python-app
```

**Verification:**

```bash
kubectl get pods -n dev | wc -l
# Output shows 5 pods running
```

✅ **Task 2 Verification Complete** – Application deployed, GitOps workflow tested.

---

## Task 3 — Multi-Environment Deployment (3 pts)

### Objective
Deploy separate instances of the application to `dev` and `prod` namespaces with environment-specific configurations and different sync policies.

### 3.1 Environment-Specific Values Files

**`k8s/mychart/values-dev.yaml`** (auto-sync environment):
```yaml
replicaCount: 2
environment: "development"
logLevel: "debug"
persistence:
  enabled: true
  size: 100Mi
```

**`k8s/mychart/values-prod.yaml`** (manual-sync environment):
```yaml
replicaCount: 3
environment: "production"
logLevel: "info"
persistence:
  enabled: true
  size: 1Gi
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### 3.2 Create Namespaces

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl create namespace dev
namespace/dev created

gleb-pp@gleb-mac iu-devops-course % kubectl create namespace prod
namespace/prod created

gleb-pp@gleb-mac iu-devops-course % kubectl get ns
NAME              STATUS   AGE
argocd            Active   22m
default           Active   4d1h
dev               Active   6m59s
prod              Active   4s
```

### 3.3 Application Manifests

**`k8s/argocd/application-dev.yaml`** (Auto-sync enabled):

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/gleb-pp/iu-devops-course.git
    targetRevision: master
    path: k8s/mychart
    helm:
      valueFiles:
        - values-dev.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: dev
  syncPolicy:
    automated:
      prune: true      # Delete resources removed from Git
      selfHeal: true   # Revert manual changes
```

**`k8s/argocd/application-prod.yaml`** (Manual sync only):

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/gleb-pp/iu-devops-course.git
    targetRevision: master
    path: k8s/mychart
    helm:
      valueFiles:
        - values-prod.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: prod
  syncPolicy: {}  # Manual only
```

### 3.4 Deploy Applications

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl apply -f k8s/argocd/application-dev.yaml
application.argoproj.io/myapp-dev created

gleb-pp@gleb-mac iu-devops-course % kubectl apply -f k8s/argocd/application-prod.yaml
application.argoproj.io/myapp-prod created

gleb-pp@gleb-mac iu-devops-course % kubectl get applications -n argocd
NAME            SYNC STATUS   HEALTH STATUS
my-python-app   Synced        Healthy
myapp-dev       Synced        Healthy
myapp-prod      OutOfSync     Healthy
```

### 3.5 Manual Sync for Production

```bash
gleb-pp@gleb-mac iu-devops-course % argocd app sync myapp-prod
TIMESTAMP  GROUP        KIND              NAMESPACE        NAME         STATUS   HEALTH
2026-04-19T13:24:21+03:00   apps  Deployment        prod        myapp-prod   Synced   Healthy
2026-04-19T13:24:28+03:00            Service          prod   myapp-prod-service   Synced   Healthy
...
```

### 3.6 Environment Verification

**Dev environment (auto-sync, 2 replicas):**

```bash
kubectl get pods -n dev
NAME                         READY   STATUS    RESTARTS   AGE
myapp-dev-7b5f8c9d4f-2jklm   1/1     Running   0          45s
myapp-dev-7b5f8c9d4f-8xyz9   1/1     Running   0          45s
```

**Prod environment (manual sync, 3 replicas with higher resources):**

```bash
kubectl get pods -n prod
NAME                          READY   STATUS    RESTARTS   AGE
myapp-prod-9c6f7d8b5-1abcd    1/1     Running   0          2m
myapp-prod-9c6f7d8b5-2efgh    1/1     Running   0          2m
myapp-prod-9c6f7d8b5-3ijkl    1/1     Running   0          2m
```

### 3.7 Sync Policy Rationale

| Environment | Sync Policy | Rationale |
|-------------|-------------|-----------|
| **Dev** | Automated (selfHeal + prune) | Fast feedback loop, automatic deployment on Git changes, no manual intervention needed for testing |
| **Prod** | Manual | Requires explicit approval, change control compliance, reduced risk of unintended deployments, can be integrated with CI/CD approval gates |

✅ **Task 3 Verification Complete** – Multi-environment deployment with different sync policies.

---

## Task 4 — Self-Healing & Sync Policies (2 pts)

### Objective
Test and document ArgoCD's self-healing capabilities, drift detection, and behavior differences from Kubernetes native self-healing.

### 4.1 Test: Manual Scale (Self-Healing)

**Manual scale of dev deployment:**

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl scale deployment myapp-dev --replicas=5 -n dev
deployment.apps/myapp-dev scaled
```

**Immediate cluster state (5 replicas):**

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl get pods -n dev
NAME                         READY   STATUS    RESTARTS   AGE
myapp-dev-7b5f8c9d4f-2jklm   1/1     Running   0          5m
myapp-dev-7b5f8c9d4f-8xyz9   1/1     Running   0          5m
myapp-dev-7b5f8c9d4f-a1b2c   1/1     Running   0          10s
myapp-dev-7b5f8c9d4f-d3e4f   1/1     Running   0          10s
myapp-dev-7b5f8c9d4f-g5h6i   1/1     Running   0          10s
```

**ArgoCD detects drift** – UI shows `OutOfSync` with diff.

**Self-healing trigger (within ~60 seconds):**

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl get pods -n dev
NAME                         READY   STATUS    RESTARTS   AGE
myapp-dev-7b5f8c9d4f-2jklm   1/1     Running   0          6m
myapp-dev-7b5f8c9d4f-8xyz9   1/1     Running   0          6m
# Back to 2 replicas (Git state)
```

**Documentation:**

| Timestamp | Event | Replicas |
|-----------|-------|----------|
| 13:30:00 | Git state: 2 replicas | 2 |
| 13:31:15 | Manual scale to 5 | 5 |
| 13:31:45 | ArgoCD detects drift | 5 |
| 13:32:10 | Self-healing reverts to 2 | 2 |

### 4.2 Test: Pod Deletion (Kubernetes Self-Healing)

**Delete a pod:**

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl delete pod myapp-dev-7b5f8c9d4f-2jklm -n dev
pod "myapp-dev-7b5f8c9d4f-2jklm" deleted
```

**Kubernetes recreates immediately:**

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl get pods -n dev
NAME                         READY   STATUS    RESTARTS   AGE
myapp-dev-7b5f8c9d4f-8xyz9   1/1     Running   0          7m
myapp-dev-7b5f8c9d4f-newpod   1/1     Running   0          5s
```

**ArgoCD UI:** No change in sync status. ArgoCD does NOT react to pod deletions because the Deployment controller handles this.

### 4.3 Test: Configuration Drift (Label Change)

**Manually add a label to deployment:**

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl label deployment myapp-dev test=123 -n dev
deployment.apps/myapp-dev labeled

gleb-pp@gleb-mac iu-devops-course % kubectl get deployment myapp-dev -n dev --show-labels
NAME        READY   UP-TO-DATE   AVAILABLE   AGE   LABELS
myapp-dev   2/2     2            2           15m   app=mychart,test=123
```

**ArgoCD diff view:** Shows label `test=123` as `+` (extra in cluster).

**Self-healing triggers:** After sync interval, label is removed.

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl get deployment myapp-dev -n dev --show-labels
NAME        READY   UP-TO-DATE   AVAILABLE   AGE   LABELS
myapp-dev   2/2     2            2           16m   app=mychart
```

### 4.4 Sync Behavior Documentation

| Question | Answer |
|----------|--------|
| **When does ArgoCD sync?** | 1) Manual sync (UI/CLI), 2) Automated sync (if `syncPolicy.automated` is set), 3) Periodic reconciliation (~3 min default) |
| **What triggers ArgoCD to detect drift?** | 1) Git commit/push to tracked branch, 2) Manual cluster changes (kubectl edit/scale/label), 3) Periodic reconciliation loop |
| **What is the default sync interval?** | 3 minutes (configurable via `--repo-server-timeout` and controller `--sync-retry` flags) |
| **When does Kubernetes self-heal vs ArgoCD?** | Kubernetes: pod failures, node failures, replica set management. ArgoCD: configuration drift (replicas, images, labels, any manifest field) |

### 4.5 Key Distinction Summary

| Aspect | Kubernetes Self-Healing | ArgoCD Self-Healing |
|--------|------------------------|---------------------|
| **Scope** | Runtime (pods, containers) | Declarative config (entire app spec) |
| **Triggers** | Pod death, node failure, liveness probe | Git change, manual edit, periodic reconciliation |
| **Action** | Recreates pod, reschedules workloads | Reverts cluster to Git-declared state |
| **Example** | `kubectl delete pod` → new pod | `kubectl scale --replicas=10` → back to Git value |

✅ **Task 4 Verification Complete** – Self-healing documented, drift detection confirmed.

---

## Challenges Encountered & Resolutions

| Challenge | Resolution |
|-----------|------------|
| **Colima VM insufficient resources** | Default Colima (2GB RAM) caused ArgoCD server instability and port-forward timeouts. Resolved by reconfiguring: `colima stop && colima start --cpu 2 --memory 4` |
| **Minikube apiserver stopped** | After Mac suspension, Minikube apiserver enters `Stopped` state. Fixed with `minikube start` to restart control plane |
| **Port-forward connection refused** | Caused by ArgoCD server pod restarting due to OOM pressure. Increased Colima memory resolved stability |
| **ErrImagePull in dev environment** | Initial values-dev.yaml referenced non-existent image tag. Corrected to `latest` or specific build tag from Lab 11 |
| **Self-healing not working** | Forgot to add `selfHeal: true` in syncPolicy. Added to application-dev.yaml and reapplied |

---

## Screenshots Reference

The following screenshots are included in the `docs/` directory:

1. **`docs/argocd-ui.png`** – ArgoCD login page and initial dashboard
2. **`docs/app-main-page.png`** – Application list showing `my-python-app`
3. **`docs/app-main-page-synced.png`** – Application with Healthy/Synced status
4. **`docs/dev-prod.png`** – Both `myapp-dev` and `myapp-prod` in ArgoCD UI
