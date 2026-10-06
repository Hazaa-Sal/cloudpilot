from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from . import __version__

from .history import initialize_history, list_plans, record_plan
from .metrics import MetricsMiddleware, PLANS, VIOLATIONS
from .models import DeploymentRequest, InfrastructurePlan, RuntimeStatus
from .planner import create_plan
from .runtime import get_runtime_status

@asynccontextmanager
async def lifespan(app):
    initialize_history()
    yield


app = FastAPI(
    title="CloudPilot",
    description="Self-service cloud infrastructure control plane",
    version=__version__,
    lifespan=lifespan,
)
app.add_middleware(MetricsMiddleware)

DASHBOARD_PATH = Path(__file__).with_name("dashboard.html")


@app.get("/")
def root():
    return {"name": "CloudPilot", "version": __version__, "status": "running"}


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
def deployment_history(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[InfrastructurePlan]:
    return list_plans(limit, offset)


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/v1/plans", response_model=InfrastructurePlan)
def generate_plan(request: DeploymentRequest) -> InfrastructurePlan:
    plan = create_plan(request)
    record_plan(plan)
    PLANS.labels(plan.environment.value, plan.status, plan.policy.cost_risk.value).inc()
    VIOLATIONS.labels(plan.environment.value).inc(len(plan.policy.violations))
    return plan
