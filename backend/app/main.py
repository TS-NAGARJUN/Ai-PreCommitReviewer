from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BACKEND_DIR / ".env", override=False)

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from app.git_analyzer import GitAnalyzer
from app.ai_models import get_review_service
from app.secret_scanner import SecretScanner
import os

app = FastAPI(title="PreCommit Reviewer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}

@app.get("/check")
async def check():
    service = get_review_service()
    if hasattr(service, "check_models"):
        result = await service.check_models()
    else:
        result = {
            "status": "error",
            "models": {
                "gemini": {"status": "error", "response": "check_models not available"},
                "groq": {"status": "error", "response": "check_models not available"},
                "huggingface": {"status": "error", "response": "check_models not available"},
            },
        }

    if isinstance(result, dict) and "models" in result:
        models = result.get("models", {})
        if not isinstance(models, dict):
            models = {}
        status = result.get("status", "ok")
        if status == "ok" and any(
            isinstance(item, dict) and item.get("status") != "ok"
            for item in models.values()
        ):
            status = "partial_error"
        return {"status": status, "models": models}

    return {"status": "ok", "models": result}

def _validate_repo_path(repo_path: str) -> str:
    if not repo_path:
        raise HTTPException(status_code=400, detail="repoPath is required")
    if not os.path.isdir(repo_path):
        raise HTTPException(status_code=400, detail=f"repoPath does not exist or is not a directory: {repo_path}")
    return repo_path


def _get_review_context(payload: dict) -> tuple[str, dict]:
    repo_path = payload.get("repoPath")
    if repo_path and os.path.isdir(repo_path):
        analyzer = GitAnalyzer(repo_path)
        return repo_path, analyzer.get_context()

    branch = payload.get("branch") or ""
    staged_diff = payload.get("stagedDiff") or ""
    changed_files = payload.get("changedFiles") or []
    if isinstance(changed_files, str):
        changed_files = [changed_files]
    return repo_path or "", {
        "branch": branch,
        "stagedDiff": staged_diff,
        "changedFiles": changed_files,
    }

@app.post("/analyze/context")
async def get_context(payload: dict):
    if "repoPath" not in payload:
        raise HTTPException(status_code=400, detail="repoPath is required")
    repo_path = _validate_repo_path(payload["repoPath"])
    analyzer = GitAnalyzer(repo_path)
    return analyzer.get_context()

@app.post("/analyze/review")
async def review(payload: dict):
    if "repoPath" not in payload:
        raise HTTPException(status_code=400, detail="repoPath is required")

    analyzer = GitAnalyzer(payload["repoPath"])
    context = analyzer.get_context()
    secret_findings = SecretScanner.scan(context.get("stagedDiff", ""))
    if secret_findings:
        return {
            "riskScore": 10.0,
            "summary": "Secrets detected in staged changes. Commit is blocked.",
            "commitMsg": "Remove secrets from staged changes before committing.",
            "findings": secret_findings,
        }

    service = get_review_service()
    return await service.analyze(
        payload["repoPath"],
        context.get("branch", ""),
        context.get("stagedDiff", ""),
        context.get("changedFiles", []),
    )


@app.post("/review")
async def review_cli(payload: dict, request: Request):
    if "repoPath" not in payload:
        raise HTTPException(status_code=400, detail="repoPath is required")

    expected_token = os.getenv("REVIEW_API_TOKEN", "").strip()
    if expected_token:
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authorization token required")

        token = auth_header.split(" ", 1)[1].strip()
        if token != expected_token:
            raise HTTPException(status_code=401, detail="Invalid authorization token")

    repo_path = payload.get("repoPath") or "."
    if repo_path and os.path.isdir(repo_path):
        repo_path = _validate_repo_path(repo_path)
    else:
        repo_path = repo_path or ""

    try:
        repo_path_for_context, context = _get_review_context(payload)
        secret_findings = SecretScanner.scan(context.get("stagedDiff", ""))
        if secret_findings:
            return {
                "issues": [
                    {
                        "file": finding.get("file", "unknown"),
                        "line": finding.get("line"),
                        "message": finding.get("message", "Secret detected"),
                        "category": finding.get("category", "security"),
                    }
                    for finding in secret_findings
                ],
                "severity": "high",
                "explanation": "Secrets detected in staged changes. Review blocked.",
                "suggestedFixes": ["Remove the credential or secret from the staged diff before continuing."],
            }

        service = get_review_service()
        result = await service.analyze(
            repo_path_for_context or repo_path,
            context.get("branch", ""),
            context.get("stagedDiff", ""),
            context.get("changedFiles", []),
        )

        findings = result.get("findings", []) or []
        issues = [
            {
                "file": finding.get("file", "unknown"),
                "line": finding.get("line"),
                "message": finding.get("message", "No message provided."),
                "category": finding.get("category", "other"),
            }
            for finding in findings
            if isinstance(finding, dict)
        ]

        risk_score = float(result.get("riskScore", 0.0) or 0.0)
        if risk_score >= 7.0 or any(
            str(finding.get("severity", "")).lower() in {"high", "critical", "error"}
            for finding in findings
            if isinstance(finding, dict)
        ):
            severity = "high"
        elif risk_score >= 3.0 or any(
            str(finding.get("severity", "")).lower() in {"medium", "moderate", "warning", "warn"}
            for finding in findings
            if isinstance(finding, dict)
        ):
            severity = "medium"
        else:
            severity = "low"

        suggested_fixes = [result.get("commitMsg", "Review complete.")]
        if not suggested_fixes[0]:
            suggested_fixes = ["Review the diff and address the flagged issues."]

        return {
            "issues": issues,
            "severity": severity,
            "explanation": result.get("summary", "Review completed successfully."),
            "suggestedFixes": suggested_fixes,
        }
    except Exception as exc:
        logger = __import__("logging").getLogger("main")
        logger.exception("Review endpoint failed")
        return {
            "issues": [],
            "severity": "low",
            "explanation": f"Review service temporarily unavailable: {exc}",
            "suggestedFixes": ["Try again in a moment or check backend environment variables."],
        }

@app.post("/analyze/hook")
async def hook(payload: dict):
    if "repoPath" not in payload:
        raise HTTPException(status_code=400, detail="repoPath is required")

    analyzer = GitAnalyzer(payload["repoPath"])
    context = analyzer.get_context()
    secret_findings = SecretScanner.scan(context.get("stagedDiff", ""))
    if secret_findings:
        return {"riskScore": 10.0, "findings": secret_findings}

    service = get_review_service()
    result = await service.analyze(
        payload["repoPath"],
        context.get("branch", ""),
        context.get("stagedDiff", ""),
        context.get("changedFiles", []),
    )
    return {"riskScore": result["riskScore"], "findings": result["findings"]}


@app.post("/analyze/scan")
async def scan(payload: dict):
    """Run secret-only scan on the repo's staged diff and return findings."""
    if "repoPath" not in payload:
        raise HTTPException(status_code=400, detail="repoPath is required")

    analyzer = GitAnalyzer(payload["repoPath"])
    context = analyzer.get_context()
    findings = SecretScanner.scan(context.get("stagedDiff", ""))
    return {"findings": findings, "count": len(findings)}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8765"))
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
