from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .history import list_plans, record_plan
from .models import DeploymentRequest, InfrastructurePlan, RuntimeStatus
from .planner import create_plan
from .runtime import get_runtime_status

app = FastAPI(
    title="CloudPilot",
    description="Self-service cloud infrastructure control plane",
    version="0.2.0",
)

DASHBOARD_PATH = Path(__file__).with_name("dashboard.html")


@app.get("/")
def root():
    return {"name": "CloudPilot", "version": "0.2.0", "status": "running"}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_PATH.read_text(encoding="utf-8")


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/v1/runtime", response_model=RuntimeStatus)
def runtime_status() -> RuntimeStatus:
    return get_runtime_status()


@app.get("/api/v1/history", response_model=list[InfrastructurePlan])
def deployment_history() -> list[InfrastructurePlan]:
    return list_plans()


@app.post("/api/v1/plans", response_model=InfrastructurePlan)
def generate_plan(request: DeploymentRequest) -> InfrastructurePlan:
    plan = create_plan(request)
    record_plan(plan)
    return plan
