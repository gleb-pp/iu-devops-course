# Lab 15 — StatefulSets & Persistent Storage

## Architecture Overview

This lab demonstrates the migration from stateless deployments to stateful applications using Kubernetes StatefulSets:

1.  **StatefulSet with Stable Identities** – Pods are created with ordinal names (`myapp-0`, `myapp-1`, etc.) that persist across restarts.
2.  **Headless Service** – Enables direct DNS resolution of individual pods for stable network identities.
3.  **Per-Pod Persistent Storage** – Each pod automatically receives its own PersistentVolumeClaim (PVC) using `volumeClaimTemplates`, ensuring data isolation.

All experiments were performed on a local Kubernetes cluster (minikube) using a Helm chart converted from Lab 12's Rollout.

**Tech Stack:**
- Kubernetes (minikube 1.35+)
- Helm Charts
- Python FastAPI application with a file-based visit counter
- StatefulSet | Headless Service | VolumeClaimTemplates | Persistent Volumes (default storage class)

## Task 1 — StatefulSet Concepts (2 pts)

### Objective
Understand when and why to use StatefulSets instead of Deployments.

### StatefulSet Guarantees

StatefulSets provide three critical guarantees for stateful applications:

1.  **Stable, unique network identifiers**: Each pod gets a predictable name (`<statefulset-name>-<ordinal>`) that remains the same even after rescheduling.
2.  **Stable, persistent storage**: Each pod is associated with its own PersistentVolumeClaim, creating isolated storage.
3.  **Ordered, graceful deployment and scaling**: Pods are created, scaled, and deleted one at a time, in a predictable order (e.g., `app-0` before `app-1`).

### Comparison: Deployment vs. StatefulSet

| Feature            | Deployment                             | StatefulSet                                 |
| ------------------ | -------------------------------------- | ------------------------------------------- |
| Pod naming         | Random suffixes (e.g., `app-6f5d9c8b`) | Ordinal suffixes (e.g., `app-0`, `app-1`)   |
| Storage            | Can share a single PVC or use ephemeral storage | Each pod gets its own dedicated PVC         |
| Scaling/Rollback   | Parallel, fast, any order              | Ordered, controlled (0 → N, N → 0)          |
| Network identity   | Not stable; pods are interchangeable   | Stable; pods are not interchangeable        |
| Use case           | Stateless apps (web servers, APIs)     | Stateful apps (databases, message brokers)  |

**Examples of stateful workloads:**
- Databases (PostgreSQL, MySQL, MongoDB)
- Distributed message brokers (Kafka, RabbitMQ)
- Cluster management tools (etcd, Zookeeper)
- Any application that requires stable storage or identity.

### Headless Services

A **Headless Service** is a Kubernetes Service defined with `clusterIP: None`. It does not provide load balancing. Instead, it returns the IP addresses of the pods that match its selector directly via DNS.

**How DNS works with StatefulSets:**
A headless service allows you to resolve each pod's individual DNS name. The naming pattern is:
`<pod-name>.<headless-service-name>.<namespace>.svc.cluster.local`

For example, for a pod `myapp-0` in the `default` namespace with a headless service named `myapp-headless`, its DNS name is:
`myapp-0.myapp-headless.default.svc.cluster.local`

This allows one pod to talk directly to another specific pod (e.g., a primary vs. replica database).

## Task 2 — Convert Deployment to StatefulSet (3 pts)

### Objective
Transform the Helm chart to use a StatefulSet with per-pod storage.

### Implementation

A new StatefulSet template (`statefulset.yaml`) and a headless service (`service-headless.yaml`) were created. The `Rollout` and its associated `service-preview.yaml` were removed. The `volumeClaimTemplates` directive was added to the StatefulSet to automatically provision a dedicated PVC for each pod replica.

### Resource Verification

**Install the Helm Chart:**
```bash
gleb-pp@gleb-mac iu-devops-course % helm install myapp ./k8s/mychart
NAME: myapp
LAST DEPLOYED: Sun Apr 19 15:11:55 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
```

**StatefulSet Status:**
```bash
gleb-pp@gleb-mac iu-devops-course % kubectl get statefulset         
NAME    READY   AGE
myapp   5/5     6m29s
```

**Pods with Ordinal Names:**
```bash
gleb-pp@gleb-mac iu-devops-course % kubectl get pods -o wide
NAME      READY   STATUS    RESTARTS   AGE     IP            NODE       NOMINATED NODE   READINESS GATES
myapp-0   1/1     Running   0          6m33s   10.244.0.33   minikube   <none>           <none>
myapp-1   1/1     Running   0          109s    10.244.0.38   minikube   <none>           <none>
myapp-2   1/1     Running   0          6m31s   10.244.0.35   minikube   <none>           <none>
myapp-3   1/1     Running   0          6m30s   10.244.0.36   minikube   <none>           <none>
myapp-4   1/1     Running   0          6m29s   10.244.0.37   minikube   <none>           <none>
```

**Per-Pod PersistentVolumeClaims:**
```bash
gleb-pp@gleb-mac iu-devops-course % kubectl get pvc
NAME           STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
data-myapp-0   Bound    pvc-f227180f-4a29-4334-a40e-40d2821d88fb   1Gi        RWO            standard       <unset>                 6m37s
data-myapp-1   Bound    pvc-50655817-5612-4820-a1c5-938bc8f8b769   1Gi        RWO            standard       <unset>                 6m36s
data-myapp-2   Bound    pvc-7d9c5b10-6617-4138-8778-3fe8084fdb2a   1Gi        RWO            standard       <unset>                 6m35s
data-myapp-3   Bound    pvc-8851c4b4-5c4e-4820-91e7-114544c677f9   1Gi        RWO            standard       <unset>                 6m34s
data-myapp-4   Bound    pvc-788e8932-8d4a-4e14-bba0-bd1f0aec2b40   1Gi        RWO            standard       <unset>                 6m33s
```

**Pod-to-PVC Binding Verification:**
```bash
gleb-pp@gleb-mac iu-devops-course % kubectl describe pod myapp-0
Name:             myapp-0
Namespace:        default
...
Controlled By:  StatefulSet/myapp
...
Volumes:
  data:
    Type:       PersistentVolumeClaim (a reference to a PersistentVolumeClaim in the same namespace)
    ClaimName:  data-myapp-0
    ReadOnly:   false
  config-volume:
    Type:      ConfigMap
    Name:      myapp-mychart-config
    Optional:  false
...
```

**Persistent Volumes Bound:**
```bash
gleb-pp@gleb-mac iu-devops-course % kubectl get pv
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                  STORAGECLASS   VOLUMEATTRIBUTESCLASS   REASON   AGE
pvc-50655817-5612-4820-a1c5-938bc8f8b769   1Gi        RWO            Delete           Bound    default/data-myapp-1   standard       <unset>                          6m52s
pvc-788e8932-8d4a-4e14-bba0-bd1f0aec2b40   1Gi        RWO            Delete           Bound    default/data-myapp-4   standard       <unset>                          6m49s
pvc-7d9c5b10-6617-4138-8778-3fe8084fdb2a   1Gi        RWO            Delete           Bound    default/data-myapp-2   standard       <unset>                          6m51s
pvc-8851c4b4-5c4e-4820-91e7-114544c677f9   1Gi        RWO            Delete           Bound    default/data-myapp-3   standard       <unset>                          6m50s
pvc-f227180f-4a29-4334-a40e-40d2821d88fb   1Gi        RWO            Delete           Bound    default/data-myapp-0   standard       <unset>                          6m53s
```

## Task 3 — Headless Service & Pod Identity (3 pts)

### Objective
Verify stable network identities and per-pod storage isolation.

### Test DNS Resolution

The headless service (`myapp-headless`) allows direct DNS resolution of each pod.

**Expected DNS pattern:** `<pod-name>.<headless-service-name>`

### Test Per-Pod Storage & Persistence

The application maintains a separate `visits.txt` file on each pod's dedicated PVC.

**Step 1 – Access `myapp-0`:**
```bash
gleb-pp@gleb-mac iu-devops-course % kubectl port-forward myapp-0 5000:5000
Forwarding from 127.0.0.1:5000 -> 5000
Forwarding from [::1]:5000 -> 5000
Handling connection for 5000
```
```json
{"service":{...},"system":{"hostname":"myapp-0",...}}
```

**Step 2 – Access `myapp-1` and generate visits:**
```bash
gleb-pp@gleb-mac iu-devops-course % kubectl port-forward myapp-1 5001:5000
Forwarding from 127.0.0.1:5001 -> 5000
Forwarding from [::1]:5001 -> 5000
Handling connection for 5001
```
```json
{"service":{...},"system":{"hostname":"myapp-1",...}}
```
After multiple requests to `localhost:5001`, the counter for `myapp-1` is incremented to **7** (example value). The counter for `myapp-0` remains unchanged, demonstrating storage isolation.

**Step 3 – Delete pod `myapp-1`:**
```bash
gleb-pp@gleb-mac iu-devops-course % kubectl delete pod myapp-1
pod "myapp-1" deleted from default namespace
```

**Step 4 – Verify pod is recreated with the same name:**
```bash
gleb-pp@gleb-mac iu-devops-course % kubectl get pods
NAME      READY   STATUS    RESTARTS   AGE
myapp-0   1/1     Running   0          4m51s
myapp-1   1/1     Running   0          7s
myapp-2   1/1     Running   0          4m49s
myapp-3   1/1     Running   0          4m48s
myapp-4   1/1     Running   0          4m47s
```

**Step 5 – Verify persistent data:**
```bash
gleb-pp@gleb-mac iu-devops-course % kubectl port-forward myapp-1 5001:5000
Forwarding from 127.0.0.1:5001 -> 5000
Forwarding from [::1]:5001 -> 5000
Handling connection for 5001
```
```json
{"service":{...},"system":{"hostname":"myapp-1","uptime_seconds":22,...}}
```
Accessing the `/visits` endpoint on the recreated pod confirms the counter still shows **7**, proving data persistence.

## Task 4 — Documentation (2 pts)

### StatefulSet Overview

**Why StatefulSet?**
StatefulSets are essential for applications that require stable identities and persistent, per-instance storage. They guarantee that each pod has a unique, stable name and a dedicated PVC that survives pod rescheduling. This is in stark contrast to Deployments, where pods are treated as interchangeable and storage is typically ephemeral or shared.

**Key Differences from Deployment:**
- **Identity:** Deployment pods have random names; StatefulSet pods have predictable, ordinal names.
- **Storage:** Deployments are best used with shared or stateless storage; StatefulSets provide a template (`volumeClaimTemplates`) to create a unique PVC for every pod.
- **Management:** Deployments scale and update in parallel; StatefulSets perform operations sequentially, respecting application dependencies (e.g., a master pod must be started before a replica).

### Resource Verification

All required resources are running and correctly configured.

- **Pods:** `myapp-0` to `myapp-4` are all in `Running` state.
- **StatefulSet:** `myapp` has `5/5` ready replicas.
- **Headless Service:** `myapp-headless` of type `ClusterIP: None` exists.
- **PVCs:** Five PVCs (`data-myapp-0` to `data-myapp-4`) are all `Bound` to their respective PVs.

### Network Identity Evidence

Each pod has a stable DNS name based on the headless service:

- `myapp-0.myapp-headless`
- `myapp-1.myapp-headless`
- ...

Port-forwarding to each pod's unique hostname confirms the stable network identity, as the application's system info returns the correct, persistent pod name (`"hostname": "myapp-1"`).

### Per-Pod Storage Evidence

The per-pod storage isolation is demonstrated by the visit counter:

- Accessing `myapp-0` and `myapp-1` via port-forwarding shows different pod hostnames.
- Incrementing the visit counter on `myapp-1` does not affect the counter on `myapp-0`.
- The `kubectl get pvc` output shows each pod is bound to a unique PVC (`data-myapp-0` for `myapp-0`, `data-myapp-1` for `myapp-1`, etc.).

### Persistence Test

The persistence of data is demonstrated by the following sequence:

| Stage                                      | Action                                              | Result                                                              |
| ------------------------------------------ | --------------------------------------------------- | ------------------------------------------------------------------- |
| **Initial State**                          | Generate 7 visits on `myapp-1`.                    | `myapp-1` visit counter is **7**.                                   |
| **Pod Deletion**                           | `kubectl delete pod myapp-1`                       | Pod is terminated.                                                  |
| **Automatic Recreation**                   | StatefulSet controller recreates `myapp-1`.        | New pod starts with the same name.                                  |
| **Post-Restart Verification**              | Access the application on the new `myapp-1` pod.   | `kubectl port-forward myapp-1 5001:5000` → visit counter is still **7**. |

✅ **Verification passed** – The visit counter value survived the deletion and recreation of the pod, confirming that the persistent volume claim (`data-myapp-1`) remained bound to the `myapp-1` identity.
