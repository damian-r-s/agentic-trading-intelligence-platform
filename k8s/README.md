# k3s deployment

This is a 1:1 lift of the local `docker-compose.yml` stack onto k3s: `postgres`,
`api` (with DB migrations running as an init container instead of a separate
`migrate` step), `finbert`, `grafana`, plus the two workers that were
`while true; sleep N` containers in compose and are now real `CronJob`s.

**Not covered here:** the React frontend (no Dockerfile/nginx config exists
for it yet) and Ollama (kept external — it runs on the VM's host, not in the
cluster).

These manifests were written without a live cluster to test against — treat
the first `kubectl apply` as the real test, and check `kubectl describe` /
`kubectl logs` for anything that doesn't come up clean.

## 0. Prerequisites

- k3s installed on the target VM (ships with the `local-path` storage
  provisioner used by every PVC here — no extra setup needed).
- `kubectl` configured against that cluster.

## 1. Build the image and import it into k3s

There is one image for `api`, `finbert`, `evaluation-worker`,
`metrics-engine`, and the `migrate` init container — same as `build: .` being
reused four times in `docker-compose.yml`.

```bash
# on the VM, from the repo root
podman build -t agentic-trading-platform:local -f DockerFile .
podman save agentic-trading-platform:local | sudo k3s ctr images import -
```

Re-run both commands after every code change — `imagePullPolicy: Never` means
k3s will never try to pull this tag from a registry, so a stale local image is
the most likely cause if pods come up running old code.

## 2. Fill in secrets

```bash
cp k8s/secret.example.yaml k8s/secret.yaml
# edit k8s/secret.yaml with real values (Binance keys, NewsAPI key, JWT
# secret, bcrypt password hash, postgres password)
```

`k8s/secret.yaml` is gitignored — it should never be committed.

## 3. Set the Ollama host IP

Edit `k8s/configmap.yaml` — replace `CHANGE_ME_VM_HOST_IP` in
`OLLAMA_BASE_URL` with the VM's own reachable IP address (the one its
primary NIC has, not `127.0.0.1` / `localhost` — pods can't reach the host
through that from inside the cluster).

## 4. Generate the Grafana provisioning ConfigMaps

These are generated from the same files used by the local `docker-compose`
Grafana setup, so there's a single source of truth for the dashboard:

```bash
kubectl create configmap grafana-datasource \
  --from-file=grafana/provisioning/datasources/datasource.yml
kubectl create configmap grafana-dashboard-provider \
  --from-file=grafana/provisioning/dashboards/dashboard.yml
kubectl create configmap grafana-dashboards \
  --from-file=grafana/dashboards/signal_quality.json
```

Re-run these (with `kubectl create configmap ... -o yaml --dry-run=client |
kubectl apply -f -` instead, to update in place) whenever the dashboard JSON
or provisioning YAML changes.

## 5. Apply

```bash
kubectl apply -f k8s/configmap.yaml -f k8s/secret.yaml
kubectl apply -f k8s/postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres --timeout=120s

kubectl apply -f k8s/api.yaml -f k8s/finbert.yaml
kubectl apply -f k8s/evaluation-worker-cronjob.yaml -f k8s/metrics-engine-cronjob.yaml
kubectl apply -f k8s/grafana.yaml
```

`postgres` needs to be up before `api` starts (its init container runs `yoyo
apply` against it), which is why it's applied and waited on separately.

## 6. Verify

```bash
kubectl get pods                       # everything Running/Completed
kubectl logs deploy/api -c migrate     # migration init container output
curl http://<VM-IP>:30080/openapi.json # api
curl http://<VM-IP>:30030/api/health   # grafana (admin/admin)
kubectl create job --from=cronjob/evaluation-worker eval-test-run
kubectl logs job/eval-test-run         # manually trigger + check a CronJob once
```
