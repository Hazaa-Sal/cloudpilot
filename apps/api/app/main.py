from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .models import DeploymentRequest, InfrastructurePlan
from .planner import create_plan

app = FastAPI(
    title="CloudPilot",
    description="Self-service cloud infrastructure control plane",
    version="0.1.0",
)

DASHBOARD_PATH = Path(__file__).with_name("dashboard.html")


@app.get("/")
def root():
    return {"name": "CloudPilot", "version": "0.1.0", "status": "running"}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_PATH.read_text(encoding="utf-8")


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/api/v1/plans", response_model=InfrastructurePlan)
def generate_plan(request: DeploymentRequest) -> InfrastructurePlan:
    return create_plan(request)
