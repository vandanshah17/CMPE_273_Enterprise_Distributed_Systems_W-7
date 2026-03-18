# Service Mesh Discovery (Istio / Linkerd)

This project now includes Kubernetes manifests for service mesh-based discovery and routing.

## Why This Is Different from Client-Side Discovery
- Client-side discovery: app queries Consul and chooses an endpoint.
- Service mesh discovery: app calls Kubernetes service DNS (`hello:8000`), and sidecar proxies + mesh policy handle routing, retries, mTLS, and telemetry.

## Prerequisites
- Docker Desktop running
- A local Kubernetes cluster (`kind` or `minikube`)
- `kubectl`

Optional tools:
- Istio CLI: `istioctl`
- Linkerd CLI: `linkerd`

## Build Image for Kubernetes

```bash
# from repository root
docker build -t discovery/hello-service:latest ./service
```

If using kind, load local image into cluster:

```bash
kind load docker-image discovery/hello-service:latest
```

## Option A: Istio

1. Install Istio (default profile):

```bash
istioctl install -y
```

2. Deploy app workloads with auto-injected Envoy sidecars:

```bash
kubectl apply -f k8s/istio/app.yaml
kubectl apply -f k8s/istio/traffic-policy.yaml
```

3. Verify pods and sidecars:

```bash
kubectl get pods -n discovery-mesh
kubectl get pod -n discovery-mesh -o jsonpath='{range .items[*]}{.metadata.name}{" -> "}{.spec.containers[*].name}{"\n"}{end}'
```

4. Observe routing and retries:

```bash
kubectl logs -n discovery-mesh deploy/caller -f
```

You should see responses from both `python-hello-service-v1` and `python-hello-service-v2` due to 50/50 traffic split.

## Option B: Linkerd

1. Install Linkerd control plane:

```bash
linkerd install | kubectl apply -f -
linkerd check
```

2. Deploy app workloads with auto-injected Linkerd proxies:

```bash
kubectl apply -f k8s/linkerd/app.yaml
```

3. If SMI extension is installed, apply traffic split:

```bash
kubectl apply -f k8s/linkerd/traffic-split.yaml
```

4. Verify mesh health and traffic:

```bash
linkerd -n discovery-mesh-linkerd stat deploy
kubectl logs -n discovery-mesh-linkerd deploy/caller -f
```

## Mesh Benefits Demonstrated
- Traffic routing: weighted split between v1 and v2.
- Observability: mesh-level request metrics and per-workload stats.
- Security: mTLS in Istio with `PeerAuthentication` set to `STRICT`.

## Cleanup

```bash
kubectl delete -f k8s/istio/traffic-policy.yaml --ignore-not-found
kubectl delete -f k8s/istio/app.yaml --ignore-not-found
kubectl delete -f k8s/linkerd/traffic-split.yaml --ignore-not-found
kubectl delete -f k8s/linkerd/app.yaml --ignore-not-found
```
