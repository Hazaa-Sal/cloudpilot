import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from apps.api.app.history import list_plans, record_plan
from apps.api.app.main import app
from apps.api.app.models import DeploymentRequest
from apps.api.app.planner import create_plan


def test_history_survives_process_restart():
    with TestClient(app) as client:
        plan = client.post("/api/v1/plans", json={
            "name": "durable-plan", "environment": "prod", "replicas": 1,
        }).json()
    result = subprocess.run(
        [sys.executable, "-c", "from apps.api.app.history import list_plans; "
         "print(list_plans()[0].model_dump_json())"],
        env=os.environ.copy(), capture_output=True, text=True, check=True,
    )
    import json
    assert json.loads(result.stdout) == plan


def test_history_retains_more_than_25_and_paginates():
    plans = [create_plan(DeploymentRequest(name=f"plan-{i}")) for i in range(30)]
    for plan in plans:
        record_plan(plan)
    assert list_plans(100) == plans[::-1]
    with TestClient(app) as client:
        assert len(client.get("/api/v1/history").json()) == 25
        assert client.get("/api/v1/history?limit=5&offset=25").json() == [
            p.model_dump(mode="json") for p in plans[:5][::-1]
        ]
        assert client.get("/api/v1/history?limit=101").status_code == 422
        assert client.get("/api/v1/history?offset=-1").status_code == 422


def test_concurrent_writes_are_not_lost():
    plans = [create_plan(DeploymentRequest(name=f"parallel-{i}")) for i in range(20)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(record_plan, plans))
    assert {p.plan_id for p in list_plans()} == {p.plan_id for p in plans}


def sample(name, labels):
    return REGISTRY.get_sample_value(name, labels) or 0


def test_metrics_decisions_violations_latency_and_bounded_labels():
    labels = {"environment": "prod", "decision": "denied", "cost_risk": "medium"}
    before = sample("cloudpilot_plans_total", labels)
    violations = sample("cloudpilot_policy_violations_total", {"environment": "prod"})
    with TestClient(app) as client:
        assert client.post("/api/v1/plans", json={
            "name": "metrics-plan", "environment": "prod", "replicas": 1,
        }).status_code == 200
        assert client.post("/api/v1/plans", json={"name": "bad" , "replicas": 100}).status_code == 422
        client.get("/unknown-sensitive-path")
        response = client.get("/metrics")
    assert sample("cloudpilot_plans_total", labels) == before + 1
    assert sample("cloudpilot_policy_violations_total", {"environment": "prod"}) == violations + 1
    assert "text/plain" in response.headers["content-type"]
    assert "cloudpilot_http_request_duration_seconds_bucket" in response.text
    assert 'route="unmatched"' in response.text
    assert "unknown-sensitive-path" not in response.text
    assert "metrics-plan" not in response.text
    assert 'route="/metrics"' not in response.text
    assert sample("cloudpilot_http_requests_total", {
        "method": "POST", "route": "/api/v1/plans", "status": "422",
    }) >= 1


def test_storage_failure_is_not_reported_as_success(monkeypatch):
    def fail(plan):
        raise OSError("storage unavailable")
    monkeypatch.setattr("apps.api.app.main.record_plan", fail)
    labels = {"environment": "dev", "decision": "validated", "cost_risk": "low"}
    before = sample("cloudpilot_plans_total", labels)
    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.post("/api/v1/plans", json={"name": "failed-plan"}).status_code == 500
    assert sample("cloudpilot_plans_total", labels) == before
    assert list_plans() == []
    assert sample("cloudpilot_http_requests_total", {
        "method": "POST", "route": "/api/v1/plans", "status": "500",
    }) >= 1
