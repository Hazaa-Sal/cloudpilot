from fastapi.testclient import TestClient

from apps.api.app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "name": "CloudPilot",
        "version": "0.2.0",
        "status": "running",
    }


def test_dashboard():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "CloudPilot" in response.text
    assert "Create deployment plan" in response.text


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_runtime_status():
    response = client.get("/api/v1/runtime")
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] in {"local", "kubernetes"}
    assert isinstance(body["kubernetes_detected"], bool)


def test_generate_dev_plan():
    response = client.post(
        "/api/v1/plans",
        json={
            "name": "portfolio-api",
            "provider": "aws",
            "region": "us-east-1",
            "environment": "dev",
            "replicas": 2,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "validated"
    assert data["policy"]["allowed"] is True
    assert data["policy"]["cost_risk"] == "low"
    assert "networking" in data["resources"]
    assert data["plan_id"]


def test_production_policy_denies_single_replica():
    response = client.post(
        "/api/v1/plans",
        json={
            "name": "production-api",
            "provider": "aws",
            "region": "us-east-1",
            "environment": "prod",
            "replicas": 1,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "denied"
    assert data["policy"]["allowed"] is False
    assert "Production deployments require at least 2 replicas." in data["policy"]["violations"]


def test_generate_prod_plan_with_risk_warning():
    response = client.post(
        "/api/v1/plans",
        json={
            "name": "production-api",
            "provider": "aws",
            "region": "us-east-1",
            "environment": "prod",
            "replicas": 3,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "validated"
    assert data["policy"]["cost_risk"] == "medium"
    assert "high-availability" in data["resources"]
    assert data["policy"]["warnings"]


def test_high_replica_count_is_high_risk():
    response = client.post(
        "/api/v1/plans",
        json={
            "name": "scale-test",
            "provider": "aws",
            "region": "us-east-1",
            "environment": "dev",
            "replicas": 5,
        },
    )
    assert response.status_code == 200
    assert response.json()["policy"]["cost_risk"] == "high"


def test_history_records_plans():
    response = client.get("/api/v1/history")
    assert response.status_code == 200
    history = response.json()
    assert len(history) >= 1
    assert "plan_id" in history[0]


def test_invalid_replica_count():
    response = client.post(
        "/api/v1/plans",
        json={
            "name": "bad-api",
            "provider": "aws",
            "region": "us-east-1",
            "environment": "dev",
            "replicas": 100,
        },
    )
    assert response.status_code == 422
