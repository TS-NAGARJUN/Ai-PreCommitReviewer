from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.git_analyzer import GitAnalyzer
from app.ai_models import get_review_service
from app.secret_scanner import SecretScanner

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

@app.post("/analyze/context")
async def get_context(payload: dict):
    if "repoPath" not in payload:
        raise HTTPException(status_code=400, detail="repoPath is required")
    analyzer = GitAnalyzer(payload["repoPath"])
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
