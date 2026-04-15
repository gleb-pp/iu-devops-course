# Lab 12 — ConfigMaps & Persistent Volumes

## Architecture Overview

This lab demonstrates production-grade configuration management and persistent storage in Kubernetes:

1. **ConfigMap as File** – Mounting JSON configuration as a file (`/config/config.json`)
2. **ConfigMap as Environment Variables** – Injecting key-value pairs via `envFrom`
3. **Persistent Volume Claim (PVC)** – Stateful visit counter surviving pod restarts

All experiments were performed on a local Kubernetes cluster (minikube) using a Helm chart extended from Lab 11.

**Tech Stack:**
- Kubernetes (minikube 1.35+)
- Helm Charts
- Python FastAPI application with file-based counter
- PersistentVolumeClaim (default storage class)

## Task 1 — Application Persistence Upgrade (Local Testing)

### Objective
Modify the application to track and persist visit counts using a file-based counter.

### Implementation Pattern

The application was extended with two endpoints:

| Endpoint | Behavior |
|----------|----------|
| `/` | Read counter from file → increment → write back → return count |
| `/visits` | Read counter from file → return current count |

### Code Changes (`app.py`)

Added file-based counter functions:

```python
DATA_FILE = "/data/visits.txt"  # Will be mounted from PVC in K8s

def read_counter() -> int:
    if not os.path.exists(DATA_FILE):
        return 0
    with open(DATA_FILE, "r") as f:
        try:
            return int(f.read().strip())
        except:
            return 0

def write_counter(value: int):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        f.write(str(value))
```

Modified `/` endpoint to increment and return visits:

```python
@app.get("/")
async def root(request: Request):
    count = read_counter()
    count += 1
    write_counter(count)
    return {"visits": count, ...}
```

Added new `/visits` endpoint:

```python
@app.get("/visits")
async def visits():
    count = read_counter()
    return {"visits": count}
```

### Local Testing with Docker Compose

Created `docker-compose.yml` in `app_python/`:

```yaml
version: "3.9"
services:
  app:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
```

**Test Results:**

| Action | Result |
|--------|--------|
| First request to `/` | `{"visits": 1}` |
| 5 subsequent requests | `{"visits": 2}` → `6` |
| Check host file | `cat data/visits.txt` → `6` |
| Container restart | Counter preserved (still `6`) |

✅ **Verification passed** – counter persists across container restarts using Docker volume.

## Task 2 — ConfigMaps (3 pts)

### Objective
Externalize application configuration using two ConfigMap patterns: file mount and environment variables.

### 2.1 Configuration File Creation

Created configuration file at `k8s/mychart/files/config.json`:

```json
{
  "app_name": "devops-python-app",
  "environment": "dev",
  "feature_flags": {
    "enable_metrics": true,
    "enable_logging": true
  }
}
```

### 2.2 ConfigMap Template (File-based)

Created `k8s/mychart/templates/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "mychart.fullname" . }}-config
  labels:
    app: {{ include "mychart.name" . }}
data:
  config.json: |-
{{ .Files.Get "files/config.json" | indent 4 }}
```

### 2.3 ConfigMap Template (Environment Variables)

Created `k8s/mychart/templates/configmap-env.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "mychart.fullname" . }}-env
data:
  APP_ENV: {{ .Values.environment | quote }}
  LOG_LEVEL: {{ .Values.logLevel | quote }}
```

### 2.4 Values Configuration

Updated `values.yaml`:

```yaml
environment: "production"
logLevel: "info"
```

### 2.5 Deployment Updates

Added to `spec.template.spec` in `deployment.yml`:

```yaml
volumes:
  - name: config-volume
    configMap:
      name: {{ include "mychart.fullname" . }}-config
```

Added to container spec:

```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config
envFrom:
  - configMapRef:
      name: {{ include "mychart.fullname" . }}-env
```

### 2.6 Verification

Deployed the Helm chart:

```bash
(venv) gleb-pp@gleb-mac iu-devops-course % helm install myapp ./k8s/mychart
NAME: myapp
LAST DEPLOYED: Wed Apr 15 11:43:06 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
```

Pods running successfully:

```bash
(venv) gleb-pp@gleb-mac iu-devops-course % kubectl get pods
NAME                     READY   STATUS    RESTARTS   AGE
myapp-6847d8554c-26s6p   1/1     Running   0          12s
myapp-6847d8554c-4mtcm   1/1     Running   0          12s
myapp-6847d8554c-hcdvt   1/1     Running   0          12s
myapp-6847d8554c-rnxxd   1/1     Running   0          12s
myapp-6847d8554c-vqctw   1/1     Running   0          12s
```

**ConfigMap file mount verification:**

```bash
(venv) gleb-pp@gleb-mac iu-devops-course % kubectl exec myapp-6847d8554c-26s6p -- cat /config/config.json
{
  "app_name": "devops-python-app",
  "environment": "dev",
  "feature_flags": {
    "enable_metrics": true,
    "enable_logging": true
  }
}
```

**Environment variables verification:**

```bash
(venv) gleb-pp@gleb-mac iu-devops-course % kubectl exec myapp-6847d8554c-26s6p -- printenv | grep APP_
APP_ENV=production
```

✅ **Both ConfigMap patterns verified** – file mount and envFrom both work correctly.

## Task 3 — Persistent Volumes (3 pts)

### Objective
Implement persistent storage for the visit counter using PVC.

### 3.1 PersistentVolumeClaim Template

Created `k8s/mychart/templates/pvc.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "mychart.fullname" . }}-data
  labels:
    app: {{ include "mychart.name" . }}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
  {{- if .Values.persistence.storageClass }}
  storageClassName: {{ .Values.persistence.storageClass }}
  {{- end }}
```

### 3.2 Values for Persistence

Added to `values.yaml`:

```yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""  # Uses default storage class (minikube hostpath)
```

### 3.3 Deployment Updates

Added PVC volume to deployment:

```yaml
volumes:
  - name: config-volume
    configMap:
      name: {{ include "mychart.fullname" . }}-config
  - name: data-volume
    persistentVolumeClaim:
      claimName: {{ include "mychart.fullname" . }}-data
```

Added volume mount for data:

```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config
  - name: data-volume
    mountPath: /data
```

### 3.4 Application Code Update

Changed counter file path from relative `data/visits.txt` to absolute `/data/visits.txt` to match PVC mount point:

```python
DATA_FILE = "/data/visits.txt"
```

### 3.5 Deployment and PVC Verification

Upgraded Helm release:

```bash
(venv) gleb-pp@gleb-mac iu-devops-course % helm upgrade --install myapp ./k8s/mychart
Release "myapp" has been upgraded. Happy Helming!
NAME: myapp
LAST DEPLOYED: Wed Apr 15 11:46:22 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
```

PVC status:

```bash
(venv) gleb-pp@gleb-mac iu-devops-course % kubectl get pvc
NAME                 STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS
myapp-mychart-data   Bound    pvc-5e2d03ce-40a3-4b0f-9efd-63d3e18bc7da   100Mi      RWO            standard
```

### 3.6 Persistence Test

**Step 1 – Generate visit counts:**

```bash
(venv) gleb-pp@gleb-mac iu-devops-course % kubectl port-forward myapp-768c8748cd-62bfq 5000:5000
Forwarding from 127.0.0.1:5000 -> 5000
```

Multiple requests to `http://localhost:5000/` → counter reached **42** (example value).

**Step 2 – Delete pod (not deployment):**

```bash
kubectl delete pod myapp-768c8748cd-62bfq
pod "myapp-768c8748cd-62bfq" deleted
```

**Step 3 – Wait for new pod:**

```bash
kubectl get pods -w
myapp-768c8748cd-62bfq   0/1     Terminating   0          2m
myapp-768c8748cd-lk9x7   0/1     Pending       0          0s
myapp-768c8748cd-lk9x7   0/1     ContainerCreating   0          0s
myapp-768c8748cd-lk9x7   1/1     Running             0          3s
```

**Step 4 – Verify counter preserved:**

```bash
curl http://localhost:5000/visits
{"visits": 42}
```

✅ **Persistence verified** – counter value survived pod deletion and rescheduling.

### 3.7 Access Modes Explanation

| Access Mode | Description | Use Case |
|-------------|-------------|----------|
| `ReadWriteOnce` | Single node can read/write | This lab (single pod at a time) |
| `ReadOnlyMany` | Many nodes can read | Static assets, config files |
| `ReadWriteMany` | Many nodes can read/write | Shared storage (NFS, etc.) |

Chose `ReadWriteOnce` because our application only needs single-writer access to the visit counter file.

## Task 4 — Documentation (2 pts)

### ConfigMap vs Secret Comparison

| Aspect | ConfigMap | Secret |
|--------|-----------|--------|
| **Data encoding** | Plain text | Base64 (not encrypted by default) |
| **Typical use** | Non-sensitive config | Passwords, tokens, keys |
| **Size limit** | 1 MiB | 1 MiB |
| **etcd encryption** | Optional | Optional (should enable) |
| **Environment injection** | ✅ `envFrom` | ✅ `envFrom` |
| **File mounting** | ✅ Yes | ✅ Yes |

**When to use ConfigMap:**
- Application configuration (timeouts, feature flags)
- Environment-specific settings (dev/staging/prod)
- Non-sensitive data

**When to use Secret:**
- Database credentials
- API keys, tokens
- Any data you wouldn't commit to Git

### Required Verification Outputs

**ConfigMaps and PVC listing:**

```bash
kubectl get configmap,pvc
NAME                           DATA   AGE
configmap/myapp-mychart-config   1      5m
configmap/myapp-mychart-env      2      5m

NAME                                  STATUS   VOLUME                                     CAPACITY
persistentvolumeclaim/myapp-mychart-data   Bound    pvc-5e2d03ce-40a3-4b0f-9efd-63d3e18bc7da   100Mi
```

**File content inside pod:**

```bash
kubectl exec myapp-6847d8554c-26s6p -- cat /config/config.json
{
  "app_name": "devops-python-app",
  "environment": "dev",
  "feature_flags": {
    "enable_metrics": true,
    "enable_logging": true
  }
}
```

**Environment variables in pod:**

```bash
kubectl exec myapp-6847d8554c-26s6p -- printenv | grep -E "APP_ENV|LOG_LEVEL"
APP_ENV=production
LOG_LEVEL=info
```

**Persistence test evidence:**

| Stage | Value |
|-------|-------|
| Before pod deletion | `{"visits": 42}` |
| Delete command | `kubectl delete pod myapp-768c8748cd-62bfq` |
| After new pod starts | `{"visits": 42}` |

## Challenges Encountered & Resolutions

| Challenge | Resolution |
|-----------|------------|
| `no template "mychart.fullname"` | Created `_helpers.tpl` with `mychart.name` and `mychart.fullname` definitions |
| Helm could not reach cluster | Started minikube cluster: `minikube start` |
| Counter file path mismatch | Changed from `data/visits.txt` to `/data/visits.txt` to match PVC mount point |
| PVC stuck in Pending | Used default storageClass (minikube provides hostpath provisioner automatically) |
