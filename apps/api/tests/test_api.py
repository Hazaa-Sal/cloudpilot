from fastapi.testclient import TestClient

from apps.api.app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "name": "CloudPilot",
        "version": "0.1.0",
        "status": "running",
    }


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


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
    assert "networking" in data["resources"]


def test_generate_prod_plan():
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
    resources = response.json()["resources"]
    assert "high-availability" in resources
    assert "autoscaling" in resources


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
