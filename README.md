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
- Dockerized development
- Automated API tests
- Terraform modules for AWS networking and compute planning
- Local Kubernetes deployment with kind
- Helm packaging
- GitHub Actions CI
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

- Policy engine
- Kubernetes deployment API
- Prometheus and Grafana
- Security scanning
- Drift detection
- Cost controls
- Deployment history and rollback
- GitOps
