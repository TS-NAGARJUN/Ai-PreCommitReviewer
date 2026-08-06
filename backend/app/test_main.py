from fastapi.testclient import TestClient

from app import main as main_module


class DummyService:
    async def analyze(self, repo_path, branch, staged_diff, changed_files):
        return {
            "riskScore": 0.0,
            "summary": "ok",
            "commitMsg": "looks good",
            "findings": [],
        }


def test_review_uses_payload_context_when_repo_path_is_unavailable(monkeypatch):
    monkeypatch.setattr(main_module, "get_review_service", lambda: DummyService())
    monkeypatch.setattr(main_module.SecretScanner, "scan", lambda diff_text: [])

    client = TestClient(main_module.app)
    response = client.post(
        "/review",
        json={
            "repoPath": "C:/does/not/exist",
            "branch": "feature/test",
            "stagedDiff": "diff --git a/app.py b/app.py\n+print('hello')",
            "changedFiles": ["app.py"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["severity"] == "low"
    assert payload["explanation"] == "ok"
    assert payload["issues"] == []
