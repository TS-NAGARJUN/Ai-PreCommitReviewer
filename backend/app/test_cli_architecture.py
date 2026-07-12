import pytest
from fastapi.testclient import TestClient
from app.main import app


class DummyService:
    async def analyze(self, repo_path, branch, staged_diff, changed_files):
        return {
            "riskScore": 6.5,
            "summary": "Potential issue found",
            "commitMsg": "Address the warning",
            "findings": [
                {
                    "file": "app.py",
                    "line": 10,
                    "severity": "high",
                    "category": "bug",
                    "message": "Unsafe code pattern",
                }
            ],
        }


@pytest.fixture
def client():
    return TestClient(app)


def test_review_endpoint_returns_cli_payload(client, monkeypatch):
    monkeypatch.setattr("app.main.get_review_service", lambda: DummyService())

    response = client.post(
        "/review",
        json={"repoPath": "."},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "issues" in data
    assert "severity" in data
    assert "explanation" in data
    assert "suggestedFixes" in data
    assert data["severity"] == "high"
    assert data["issues"][0]["message"] == "Unsafe code pattern"
