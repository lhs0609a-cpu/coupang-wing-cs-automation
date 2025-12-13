"""
API Health Check Tests
API 헬스체크 테스트
"""
import pytest


@pytest.mark.unit
def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert "name" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "running"


@pytest.mark.unit
def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data
    assert "uptime_seconds" in data


@pytest.mark.unit
def test_monitoring_metrics(client):
    """Test monitoring metrics endpoint"""
    response = client.get("/api/monitoring/metrics")

    assert response.status_code == 200
    data = response.json()

    assert "uptime_seconds" in data
    assert "total_requests" in data
    assert "error_rate" in data
    assert "memory_percent" in data
    assert "cpu_percent" in data


@pytest.mark.unit
def test_docs_accessible(client):
    """Test that API documentation is accessible"""
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/redoc")
    assert response.status_code == 200

    response = client.get("/openapi.json")
    assert response.status_code == 200
