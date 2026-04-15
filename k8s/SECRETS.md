# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## Architecture Overview

This lab demonstrates two approaches to secret management in Kubernetes:
1. **Native Kubernetes Secrets** (base64 encoded, stored in etcd)
2. **HashiCorp Vault** (enterprise-grade secret storage with dynamic injection)

All experiments were performed on a local Kubernetes cluster (minikube) using Helm charts extended from Lab 10.

**Tech Stack:**
- Kubernetes (minikube)
- Helm Charts
- HashiCorp Vault 1.18+ (Helm deployment)
- Vault Agent Injector (sidecar pattern)

## Task 1 — Kubernetes Secrets Fundamentals

### Objective
Understand how Kubernetes Secrets work, their security model (encoding vs encryption), and basic operations.

### 1. Creating a Secret Using `kubectl`

Created a generic secret from literals:

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl create secret generic my-secret \
  --from-literal=username=admin \
  --from-literal=password=12345
secret/my-secret created
```

Also created a secret from a file to demonstrate different creation methods:

```bash
gleb-pp@gleb-mac iu-devops-course % echo "super-secret-key" > secret.txt
gleb-pp@gleb-mac iu-devops-course % kubectl create secret generic file-secret \
  --from-file=secret.txt
secret/file-secret created
```

### 2. Examining the Secret

Viewing the secret in YAML format reveals base64-encoded values:

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl get secret my-secret -o yaml
apiVersion: v1
data:
  password: MTIzNDU=
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-08T07:56:49Z"
  name: my-secret
  namespace: default
  resourceVersion: "307620"
  uid: b179e1b2-ffb8-4bb0-93a1-02ae46bf7d92
type: Opaque
```

### 3. Decoding Base64 Values

Decoding demonstrates that secrets are **encoded**, not encrypted:

```bash
gleb-pp@gleb-mac iu-devops-course % echo "YWRtaW4=" | base64 -d
admin%
```

**Key Insight:** Anyone with access to the Kubernetes API can decode these values trivially.

### 4. Security Implications

**Question:** Are Kubernetes Secrets encrypted at rest by default?

**Answer:** No. By default, Kubernetes Secrets are only base64-encoded and stored in etcd as plain text.

**What is etcd encryption and when should you enable it?**

etcd encryption is a feature that encrypts secret data at rest using AES-CBC or AES-GCM. It should be enabled in production environments to protect sensitive data if etcd is compromised.

**Security Recommendations for Production:**
- Enable etcd encryption at rest (`--encryption-provider-config`)
- Implement strict RBAC policies for secret access
- Use external secret managers (Vault) for highly sensitive data
- Never commit secrets to Git (even in values.yaml)

## Task 2 — Helm-Managed Secrets

### Objective
Integrate secrets into Helm charts and inject them as environment variables.

### 1. Secret Template (`templates/secrets.yaml`)

Added a secret template that uses Helm templating to create Kubernetes secrets dynamically:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ .Release.Name }}-secret
  labels:
    app: {{ .Release.Name }}
type: Opaque
data:
  username: {{ .Values.secrets.username | toString | b64enc }}
  password: {{ .Values.secrets.password | toString | b64enc }}
```

**Note:** Used `toString` filter to handle cases where values are provided as numbers (e.g., `12345`).

### 2. Values Configuration (`values.yaml`)

Added secret placeholders in `values.yaml`:

```yaml
secrets:
  username: "admin"
  password: "12345"
```

### 3. Consuming Secrets in Deployment

Updated `templates/deployment.yaml` to inject secrets as environment variables using `envFrom`:

```yaml
envFrom:
  - secretRef:
      name: {{ .Release.Name }}-secret
```

### 4. Resource Limits Configuration

Following Kubernetes best practices, resource limits are configurable via `values.yaml`:

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "256Mi"
```

**Explanation:**
- **Requests:** Minimum resources guaranteed to the container (used for scheduling)
- **Limits:** Maximum resources the container can consume (prevents resource starvation)
- **Choosing values:** Based on application profiling — 100m CPU / 128Mi RAM for typical web apps

### 5. Deployment Verification

Deployed the Helm chart successfully:

```bash
gleb-pp@gleb-mac k8s % helm install my-app ./mychart
NAME: my-app
LAST DEPLOYED: Wed Apr  8 11:04:58 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None
```

Secret was created automatically by Helm:

```bash
gleb-pp@gleb-mac k8s % kubectl get secret my-app-secret -o yaml
apiVersion: v1
data:
  password: MTIzNDU=
  username: YWRtaW4=
kind: Secret
metadata:
  annotations:
    meta.helm.sh/release-name: my-app
    meta.helm.sh/release-namespace: default
  creationTimestamp: "2026-04-08T08:05:08Z"
  labels:
    app: my-app
    app.kubernetes.io/managed-by: Helm
  name: my-app-secret
  namespace: default
  resourceVersion: "308338"
  uid: 4320486a-25ec-41b5-8deb-5d6fed597392
type: Opaque
```

### 6. Environment Variable Injection Verification

Connected to a running pod and verified secrets were properly injected as environment variables:

```bash
gleb-pp@gleb-mac k8s % kubectl exec -it my-app-76d86756f4-2glx5 -- sh
$ env | grep username
username=admin
$ env | grep password
password=12345
$ exit
```

### 7. Security Verification

Using `kubectl describe pod` confirms that secret values are NOT visible in the pod specification (only references to the secret):

```bash
gleb-pp@gleb-mac k8s % kubectl describe pod my-app-76d86756f4-2glx5
...
Environment Variables from:
  my-app-secret  Secret  Optional: false
Environment:
  ENV:      production
  VERSION:  v2
...
```

The actual secret values (`admin`, `12345`) do NOT appear in the describe output.

## Task 3 — HashiCorp Vault Integration

### Objective
Deploy HashiCorp Vault, configure Kubernetes authentication, and inject secrets using the Vault Agent Injector (sidecar pattern).

### 1. Installing Vault via Helm

Added HashiCorp Helm repository and installed Vault in dev mode:

```bash
gleb-pp@gleb-mac k8s % helm repo add hashicorp https://helm.releases.hashicorp.com 
"hashicorp" has been added to your repositories

gleb-pp@gleb-mac k8s % helm install vault hashicorp/vault \
  --set "server.dev.enabled=true"
NAME: vault
LAST DEPLOYED: Wed Apr  8 11:10:56 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
```

### 2. Verification — Vault Pods Running

```bash
gleb-pp@gleb-mac k8s % kubectl get pods
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          113s
vault-agent-injector-848dd747d7-5xlqh   1/1     Running   0          113s
```

### 3. Configuring Vault (KV Secrets Engine)

Connected to the Vault pod and enabled the KV v2 secrets engine:

```bash
gleb-pp@gleb-mac k8s % kubectl exec -it vault-0 -- sh
/ $ vault secrets enable -path=secret kv-v2
Success! Enabled the kv-v2 secrets engine at: secret/
```

Stored application secrets:

```bash
/ $ vault kv put secret/myapp username=admin password=12345
== Secret Path ==
secret/data/myapp

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-08T08:13:49.089579622Z
version            1
```

Verified the secret:

```bash
/ $ vault kv get secret/myapp
== Secret Path ==
secret/data/myapp

====== Data ======
Key         Value
---         -----
password    12345
username    admin
```

### 4. Configuring Kubernetes Authentication

Enabled the Kubernetes auth method:

```bash
/ $ vault auth enable kubernetes
Success! Enabled kubernetes auth method at: kubernetes/
```

Configured Vault to communicate with the Kubernetes API:

```bash
/ $ vault write auth/kubernetes/config \
>   token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
>   kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443" \
>   kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
Success! Data written to: auth/kubernetes/config
```

### 5. Creating Policy and Role

Created a policy granting read access to the secret:

```bash
/ $ vault policy write myapp-policy - <<EOF
> path "secret/data/myapp" {
>   capabilities = ["read"]
> }
> EOF
Success! Uploaded policy: myapp-policy
```

Created a role bound to the `default` service account:

```bash
/ $ vault write auth/kubernetes/role/myapp-role \
>   bound_service_account_names=default \
>   bound_service_account_namespaces=default \
>   policies=myapp-policy \
>   ttl=1h
WARNING! The following warnings were returned from Vault:
  * Role myapp-role does not have an audience configured...
```

### 6. Enabling Vault Agent Injection

Updated the Helm chart deployment with annotations to enable sidecar injection (added to `templates/deployment.yaml`):

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "myapp-role"
  vault.hashicorp.com/agent-inject-secret-config.txt: "secret/data/myapp"
  vault.hashicorp.com/agent-inject-template-config.txt: |
    {{- with secret "secret/data/myapp" -}}
    username={{ .Data.data.username }}
    password={{ .Data.data.password }}
    {{- end }}
```

Upgraded the Helm release:

```bash
gleb-pp@gleb-mac k8s % helm upgrade my-app ./mychart
Release "my-app" has been upgraded. Happy Helming!
NAME: my-app
LAST DEPLOYED: Wed Apr  8 11:21:01 2026
NAMESPACE: default
STATUS: deployed
REVISION: 3
```

### 7. Verification — Sidecar Injection Working

After the upgrade, pods now have **2 containers** (main app + Vault Agent sidecar):

```bash
gleb-pp@gleb-mac k8s % kubectl get pods
NAME                                    READY   STATUS    RESTARTS   AGE
my-app-59cc87b5b4-lgh4s                 2/2     Running   0          39s
my-app-59cc87b5b4-spmqr                 2/2     Running   0          39s
```

### 8. Proof of Secret Injection

Connected to the main application container and verified the injected secret file:

```bash
gleb-pp@gleb-mac k8s % kubectl exec -it my-app-59cc87b5b4-lgh4s -- sh
Defaulted container "mychart" out of: mychart, vault-agent, vault-agent-init (init)
$ cat /vault/secrets/config.txt
username=admin
password=12345
```

**Success!** The Vault Agent sidecar successfully injected the secret as a file at `/vault/secrets/config.txt`.

### Explanation of the Sidecar Injection Pattern

The Vault Agent Injector adds an **init container** and a **sidecar container** to the pod:

1. **Init container:** Authenticates with Vault and fetches secrets before the main app starts
2. **Sidecar container:** Keeps secrets renewed and maintains the authentication token
3. **Shared volume:** Secrets are written to `/vault/secrets/` and shared with the main container

This pattern provides:
- **Zero application code changes** (read from file instead of environment variables)
- **Automatic secret renewal** (no manual rotation)
- **No secrets in environment variables** (reduces exposure risk)

## Task 4 — Security Analysis & Recommendations

### Comparison: Kubernetes Secrets vs. HashiCorp Vault

| Aspect | Kubernetes Secrets | HashiCorp Vault |
|--------|-------------------|-----------------|
| **Default encryption** | ❌ No (only base64) | ✅ Yes (AES-256) |
| **Dynamic secrets** | ❌ No | ✅ Yes |
| **Secret rotation** | Manual | Automated |
| **Audit logging** | Basic (API server) | Advanced (detailed) |
| **Integration complexity** | Low (native) | Medium (sidecar) |
| **Use case** | Non-sensitive config, dev/test | Production, sensitive data |

### When to Use Each Approach

**Use Kubernetes Secrets when:**
- Low sensitivity data (e.g., feature flags, non-critical config)
- Development / testing environments
- Simple deployment scenarios without compliance requirements

**Use HashiCorp Vault when:**
- Production workloads with sensitive data (API keys, DB passwords)
- Compliance requirements (SOC2, HIPAA, PCI-DSS)
- Dynamic secret generation needed
- Audit trails required for secret access
- Multi-cloud or hybrid deployments

### Production Recommendations

1. **For Kubernetes Secrets:**
   - Enable etcd encryption at rest
   - Implement RBAC to restrict secret access
   - Rotate secrets regularly
   - Never commit secrets to Git (use SealedSecrets or ExternalSecrets Operator)

2. **For HashiCorp Vault:**
   - Run Vault in HA mode (not dev mode)
   - Use auto-unseal with cloud KMS
   - Enable audit logging
   - Use Vault Agent (not sidecar) for long-running apps
   - Implement Vault policies using least-privilege principle

3. **General Best Practices:**
   - Prefer **files over environment variables** for secrets (reduces exposure in /proc)
   - Use **short-lived secrets** whenever possible
   - Implement secret rotation as part of CI/CD pipelines

## Challenges Encountered & Resolutions

| Challenge | Resolution |
|-----------|------------|
| `wrong type for value; expected string; got float64` when using `b64enc` | Added `toString` filter: `{{ .Values.secrets.password | toString | b64enc }}` |
| Pods stuck in `Pending` state with `Insufficient cpu` | Cleaned up old deployments and increased minikube CPU: `minikube start --cpus=4` |
| Vault CLI not available locally | Used `kubectl exec -it vault-0 -- vault` to run Vault commands inside the pod |
