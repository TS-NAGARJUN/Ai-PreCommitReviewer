import asyncio

from app.ai_models import AIReviewService, GeminiClient, GroqClient


def test_analyze_returns_fallback_when_all_backends_fail(monkeypatch):
    async def failing_review(self, prompt):
        raise RuntimeError("backend unavailable")

    monkeypatch.setattr(GeminiClient, "review", failing_review)
    monkeypatch.setattr(GroqClient, "review", failing_review)

    service = AIReviewService(groq_key="", antigravity_api_key="")
    result = asyncio.run(service.analyze("/tmp/repo", "main", "diff", ["file.py"]))

    assert result["riskScore"] == 0.0
    assert result["findings"] == []
    assert "AI review unavailable" in result["summary"]
