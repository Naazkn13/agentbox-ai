---
id: kubernetes
name: Kubernetes Expert
category: deploying
level1: "For Kubernetes deployments, services, Helm charts, HPA, ingress, RBAC, and kubectl"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Kubernetes Expert** — Activate for: writing Kubernetes YAML, Deployments, Services, ConfigMaps, Secrets, Helm charts, HPA, ingress rules, RBAC, namespace isolation, kubectl commands, debugging crashing pods.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Kubernetes Expert — Core Instructions

1. **Always set resource requests and limits** — a container without `resources` can starve neighbors or get OOM-killed unpredictably. Requests drive scheduling; limits enforce caps.
2. **Always define liveness and readiness probes** — without them, Kubernetes cannot distinguish a healthy pod from a stuck one, and traffic is sent to pods that are not ready.
3. **Never store secrets in ConfigMaps or env vars from plain strings** — use `kind: Secret` with base64 values, or a secrets manager (Vault, AWS Secrets Manager, External Secrets Operator).
4. **Use namespaces to isolate environments** — `dev`, `staging`, and `prod` belong in separate namespaces (or clusters). Apply RBAC per namespace.
5. **Set PodDisruptionBudgets and rolling update strategy** — `maxUnavailable: 0` with `maxSurge: 1` ensures zero-downtime rollouts. PDB prevents eviction from taking down all replicas.
6. **Label everything consistently** — use `app`, `version`, and `component` labels on all resources. Selectors must match labels exactly or Services and deployments will silently orphan pods.
7. **Diagnose crashing pods methodically** — `kubectl describe pod` for events, `kubectl logs --previous` for the last crash output, `kubectl exec` to inspect the running container.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Kubernetes Expert — Full Reference

### Deployment with Best Practices

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  namespace: production
  labels:
    app: api-server
    version: "1.4.2"
    component: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-server
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  template:
    metadata:
      labels:
        app: api-server
        version: "1.4.2"
        component: backend
    spec:
      terminationGracePeriodSeconds: 30
      containers:
        - name: api-server
          image: myregistry/api-server:1.4.2
          ports:
            - containerPort: 8080
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: password
            - name: APP_ENV
              valueFrom:
                configMapKeyRef:
                  name: api-config
                  key: app_env
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 20
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
            failureThreshold: 3
```

---

### Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: api-server
  namespace: production
  labels:
    app: api-server
spec:
  selector:
    app: api-server       # must match Deployment pod labels exactly
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: ClusterIP         # use LoadBalancer for external; ClusterIP + Ingress preferred
```

---

### ConfigMap and Secret

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
  namespace: production
data:
  app_env: "production"
  log_level: "info"
  max_connections: "100"
```

```yaml
# secret.yaml  — values are base64-encoded: echo -n 'value' | base64
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
  namespace: production
type: Opaque
data:
  password: c3VwZXJzZWNyZXQ=   # base64 of 'supersecret'
  username: YXBpdXNlcg==
```

```bash
# Create secret from literal without writing to disk
kubectl create secret generic db-secret \
  --from-literal=password=supersecret \
  --from-literal=username=apiuser \
  -n production
```

---

### Horizontal Pod Autoscaler (HPA)

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-server-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

---

### Ingress (nginx)

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  namespace: production
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - api.example.com
      secretName: api-tls-cert
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-server
                port:
                  number: 80
```

---

### RBAC — Namespace-scoped Role and Binding

```yaml
# rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer-role
  namespace: staging
rules:
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets"]
    verbs: ["get", "list", "watch", "update", "patch"]
  - apiGroups: [""]
    resources: ["pods", "pods/log", "configmaps"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: developer-binding
  namespace: staging
subjects:
  - kind: User
    name: jane@example.com
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: developer-role
  apiGroup: rbac.authorization.k8s.io
```

---

### Helm Chart Structure

```
my-chart/
├── Chart.yaml
├── values.yaml
├── values-staging.yaml
├── values-production.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    ├── hpa.yaml
    ├── configmap.yaml
    ├── secret.yaml
    └── _helpers.tpl
```

```yaml
# Chart.yaml
apiVersion: v2
name: api-server
description: API Server Helm chart
type: application
version: 0.1.0
appVersion: "1.4.2"
```

```yaml
# values.yaml
replicaCount: 2
image:
  repository: myregistry/api-server
  tag: "1.4.2"
  pullPolicy: IfNotPresent

resources:
  requests:
    cpu: 250m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70

ingress:
  enabled: true
  host: api.example.com
```

```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "api-server.fullname" . }}
  labels:
    {{- include "api-server.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "api-server.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "api-server.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
```

```bash
# Helm commands
helm install api-server ./my-chart -f values-production.yaml -n production
helm upgrade api-server ./my-chart -f values-production.yaml -n production
helm rollback api-server 1 -n production   # roll back to revision 1
helm diff upgrade api-server ./my-chart    # preview changes (helm-diff plugin)
helm lint ./my-chart                       # validate chart syntax
```

---

### Debugging Crashing Pods

```bash
# Step 1: See events and state transitions
kubectl describe pod <pod-name> -n <namespace>

# Step 2: Check logs of the crashed container
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous   # last crash output

# Step 3: Check all pods + status in a namespace
kubectl get pods -n <namespace> -o wide

# Step 4: Exec into a running container
kubectl exec -it <pod-name> -n <namespace> -- /bin/sh

# Step 5: Check resource pressure on nodes
kubectl top nodes
kubectl top pods -n <namespace>

# Step 6: Describe the node a pod is scheduled on
kubectl describe node <node-name>

# Common crash reasons:
# CrashLoopBackOff    — app is exiting; check logs --previous
# OOMKilled           — hit memory limit; increase limits.memory
# ImagePullBackOff    — bad image name or missing imagePullSecret
# Pending             — no node fits; check resource requests or taints
# Init:Error          — init container failed; check init container logs
kubectl logs <pod-name> -c <init-container-name> -n <namespace>
```

---

### PodDisruptionBudget

```yaml
# pdb.yaml — ensures at least 2 replicas stay up during node drain
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-server-pdb
  namespace: production
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: api-server
```

---

### Common kubectl Commands

```bash
# Context and namespace
kubectl config get-contexts
kubectl config use-context prod-cluster
kubectl config set-context --current --namespace=production

# Apply and delete
kubectl apply -f manifests/          # apply all files in directory
kubectl delete -f manifests/
kubectl apply -f - <<EOF             # apply inline YAML
...
EOF

# Rolling restart (forces new pods without changing spec)
kubectl rollout restart deployment/api-server -n production

# Watch rollout progress
kubectl rollout status deployment/api-server -n production

# Undo last rollout
kubectl rollout undo deployment/api-server -n production

# Scale manually
kubectl scale deployment api-server --replicas=5 -n production

# Port-forward for local debugging
kubectl port-forward svc/api-server 8080:80 -n production

# Copy files to/from a pod
kubectl cp <pod-name>:/app/logs/error.log ./error.log -n production
```

---

### Anti-patterns to Avoid
- Omitting `resources` — pods get evicted under pressure or starve other workloads without limits
- Using `latest` image tag — makes rollbacks impossible and breaks reproducibility; always pin to a specific digest or semver tag
- Putting secrets in ConfigMaps or unencrypted env literals — any user with `get configmap` access can read them
- Setting `readinessProbe` and `livenessProbe` to the same endpoint with no `initialDelaySeconds` — the liveness probe kills the pod before it finishes starting
- Creating resources in the `default` namespace for production workloads — namespace isolation is your first security boundary
- Not setting a `PodDisruptionBudget` — a routine node drain can take all replicas offline simultaneously
<!-- LEVEL 3 END -->
