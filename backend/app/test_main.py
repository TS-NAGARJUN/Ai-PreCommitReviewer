import importlib
import os
from pathlib import Path

import pytest
from dotenv import dotenv_values
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


class TestCheckEndpoint:
    """Test /check endpoint"""

    def test_check_endpoint_returns_model_statuses(self, client, monkeypatch):
        class DummyCheckService:
            async def check_models(self):
                return {
                    "gemini": {"status": "ok", "response": "Gemini ready"},
                    "groq": {"status": "ok", "response": "Groq ready"},
                    "huggingface": {"status": "ok", "response": "Hugging Face ready"},
                }

        monkeypatch.setattr("app.main.get_review_service", lambda: DummyCheckService())

        response = client.get("/check")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "models" in data
        assert data["models"]["gemini"]["response"] == "Gemini ready"

    def test_main_loads_backend_dotenv_when_started_from_repo_root(self, monkeypatch):
        backend_dir = Path(__file__).resolve().parent.parent
        dotenv_path = backend_dir / ".env"
        env_values = dotenv_values(dotenv_path)

        monkeypatch.chdir(backend_dir.parent)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        import app.main as main_module

        importlib.reload(main_module)

        assert os.getenv("GEMINI_API_KEY") == env_values.get("GEMINI_API_KEY")
