# CloudPilot

CloudPilot is a zero-cost, portfolio-grade cloud engineering project that demonstrates a self-service infrastructure control plane using FastAPI, Docker, Terraform, Kubernetes, Helm, and GitHub Actions.

## What it does

CloudPilot accepts a deployment request, validates it, and returns a structured infrastructure plan. The project is designed to evolve into a platform that can enforce policy, generate infrastructure plans, deploy workloads, and expose operational telemetry.

## Architecture

```text
Developer
   |
   v
CloudPilot API (FastAPI)
   |
   +--> Request validation (Pydantic)
   |
   +--> Planning engine
   |
   +--> Terraform plan-only AWS architecture
   |
   +--> Local Kubernetes (kind)
            |
            +--> Helm
            +--> Health checks
```

## Current capabilities

- FastAPI control-plane API
- Pydantic request validation
- Environment-aware planning
- Policy engine with allow/deny decisions
- Cost-risk warnings and zero-cost guardrails
- SQLite deployment plan history that survives restarts
- Live local/Kubernetes runtime detection
- Interactive web dashboard
- Dockerized development
- Automated API tests
- Terraform modules for AWS networking and compute planning
- Local Kubernetes deployment with kind
- Helm packaging
- GitHub Actions CI
- Bandit, Checkov, and Trivy security gates
- Local Prometheus metrics and provisioned Grafana dashboard
- Zero-cost local development path

## Tech stack

Python · FastAPI · Pydantic · Docker · Pytest · Terraform · AWS · Kubernetes · Helm · GitHub Actions

## Run locally

```bash
docker compose up --build
```

Open the dashboard at:

```text
http://localhost:8000/dashboard
```

The dashboard now shows policy decisions, cost risk, deployment history, and live runtime/Kubernetes metadata.

### Local monitoring

```bash
docker compose --profile monitoring up -d --build
```

- Dashboard: http://localhost:8000/dashboard
- Metrics: http://localhost:8000/metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000/d/cloudpilot-overview (anonymous read-only viewing)

The Grafana dashboard is provisioned automatically: API scrape health, saved and
denied plans, policy violations, plans by environment/cost risk, request rate,
HTTP errors, and p95 latency. Create plans in CloudPilot, then allow two scrapes
(about 30 seconds) for rate panels. Counters reset when the API process restarts;
SQLite history remains intact. Metrics exclude scrape requests and use bounded
route labels, never application names, raw URLs, or plan IDs.

All ports bind to loopback. Override `CLOUDPILOT_PORT`, `PROMETHEUS_PORT`, or
`GRAFANA_PORT` if those ports are occupied. This unauthenticated demo is for local
use only; add authentication before exposing it. Grafana's initial admin login
is `admin` / `admin` and prompts for a password change; viewing requires no login.
Prometheus retains at most seven days / 1 GB of metrics. No AWS credentials,
paid cloud resources, or external observability subscription are needed.

### Durable history

`CLOUDPILOT_DB_PATH` defaults to `data/cloudpilot.db` for a direct Python run,
and `/cloudpilot/data/cloudpilot.db` in containers. Compose stores it in the
`cloudpilot-data` named volume. Both allowed and denied plans retain their ID,
timestamp, request fields, resources, status, and complete policy result.

`GET /api/v1/history?limit=25&offset=0` keeps the existing newest-first JSON array
response. `limit` accepts 1–100; `offset` accepts non-negative integers. Records
are not automatically pruned. The dashboard shows eight plans per page with
Newer/Older navigation. Select a saved plan to reopen its full policy result or
download it as JSON. API health is checked on load and every 30 seconds while
the page is visible.

`docker compose down` preserves data; `docker compose down -v` deletes volumes.
For backups, stop the API before copying the volume, or use SQLite's backup API;
do not copy only the main database file while WAL writes are active. Old v0.2
in-memory history cannot be recovered after its original process exits.

Run one API process and one replica. SQLite uses WAL and a busy timeout for
concurrent local requests; shared network storage and multiple replicas are not
supported. Process-local metrics likewise assume one worker.

Open the API docs at:

```text
http://localhost:8000/docs
```

Run tests:

```bash
docker compose exec cloudpilot-api python -m pytest -v apps/api/tests
```

## Kubernetes

Build and load the image:

```bash
docker build -t cloudpilot:local .
kind load docker-image cloudpilot:local --name cloudpilot
```

Deploy with Helm:

```bash
helm upgrade --install cloudpilot deploy/helm/cloudpilot
kubectl port-forward svc/cloudpilot 8080:8000
```

The chart uses a 1 GiB ReadWriteOnce PVC and a Recreate strategy to preserve
SQLite across pod replacement. A default local StorageClass is required; set
`persistence.storageClass` when needed. `replicaCount` must be 1. The PVC is kept
on uninstall; deleting it manually deletes history. The API runs non-root with
a read-only root filesystem and no service-account token. `/metrics` is also
available through the port-forward. A Prometheus instance inside the cluster
can scrape `cloudpilot:8000` in the same namespace. The included Compose
monitoring stack targets the Compose API by default.

Then open the dashboard:

```text
http://localhost:8080/dashboard
```

Or open the API docs:

```text
http://localhost:8080/docs
```

## Terraform

This repository keeps AWS provisioning in plan/validation mode by default to avoid unexpected cloud charges.

```bash
terraform -chdir=infra/terraform/environments/dev init
terraform -chdir=infra/terraform/environments/dev validate
terraform -chdir=infra/terraform/environments/dev plan
```

> Do not run `terraform apply` unless you intentionally want to create AWS resources and understand the associated costs.

## Example request

```json
{
  "name": "portfolio-api",
  "provider": "aws",
  "region": "us-east-1",
  "environment": "dev",
  "replicas": 2
}
```

## Example response

```json
{
  "application": "portfolio-api",
  "provider": "aws",
  "region": "us-east-1",
  "environment": "dev",
  "replicas": 2,
  "resources": [
    "container-workload",
    "load-balancer",
    "networking",
    "iam-role",
    "logging"
  ],
  "status": "validated"
}
```

## Roadmap

- Kubernetes deployment API
- Drift detection
- Cost controls
- Deployment history and rollback
- GitOps

## Security and validation

GitHub Actions runs API tests, Terraform format/init/validate, Helm lint/render,
Compose validation, Prometheus configuration validation, and a local monitoring
smoke test. Terraform is never applied and no AWS secrets are required.

The independent security jobs upload reports even on scan failure:

- Bandit scans application Python and blocks on findings.
- Checkov scans Terraform and blocks on unsuppressed findings.
- Trivy scans the built API image and blocks on fixable HIGH/CRITICAL OS or
  Python vulnerabilities. Unfixed and lower-severity vulnerabilities are outside
  this gate; a passing scan is not a claim of no vulnerabilities.

Checkov exceptions are narrowly attached to resources: paid KMS keys, ECS
Container Insights, VPC flow-log storage, and the intentionally unattached
security group in this plan-only scaffold. ECR tags are immutable, automatic
public IP assignment is disabled, default security-group traffic is denied,
and workload egress is limited to HTTPS. Reassess the exceptions and network
requirements before any future real deployment.

```bash
python -m pytest -v apps/api/tests
bandit -r apps/api/app
checkov -d infra/terraform --framework terraform
helm lint deploy/helm/cloudpilot
docker compose --profile monitoring config --quiet
```

Optional browser regression check (requires Playwright CLI):

```bash
playwright-cli -s=cloudpilot open http://localhost:8000/dashboard
playwright-cli -s=cloudpilot run-code --filename=scripts/dashboard-smoke.js
playwright-cli -s=cloudpilot close
```

This creates one denied demo plan, then checks JSON export, keyboard selection,
history pagination, failed requests, live health, and mobile layout. Pagination
fixtures are mocked in the browser; they are not stored in your database.
