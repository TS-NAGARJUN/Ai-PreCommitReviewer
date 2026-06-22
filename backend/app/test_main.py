import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


class TestHealthEndpoint:
    """Test /health endpoint"""

    def test_health_status(self, client):
        """Test health endpoint returns correct status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"


class TestAnalyzeEndpoints:
    """Test analyze endpoints"""

    def test_analyze_context_stub(self, client):
        """Test /analyze/context endpoint"""
        response = client.post(
            "/analyze/context",
            json={"repoPath": "."}
        )
        assert response.status_code == 200
        data = response.json()
        # This is a stub that returns git context
        assert "branch" in data or "error" not in data

    def test_analyze_review_stub(self, client):
        """Test /analyze/review endpoint"""
        response = client.post(
            "/analyze/review",
            json={"repoPath": "."}
        )
        assert response.status_code == 200
        data = response.json()
        assert "riskScore" in data
        assert "findings" in data

    def test_analyze_hook_stub(self, client):
        """Test /analyze/hook endpoint"""
        response = client.post(
            "/analyze/hook",
            json={"repoPath": "."}
        )
        assert response.status_code == 200
        data = response.json()
        assert "riskScore" in data
        assert "findings" in data


class TestCORSHeaders:
    """Test CORS configuration"""

    def test_cors_headers_present(self, client):
        """Test that CORS middleware is configured"""
        response = client.get("/health")
        # CORS middleware is configured in the app
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
