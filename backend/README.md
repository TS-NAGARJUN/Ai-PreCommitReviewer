# Backend service for review-cli

This backend exposes a lightweight review endpoint that the CLI calls.

## Run locally

```bash
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8765
```

## Environment variables

- REVIEW_API_TOKEN: optional bearer token for the CLI endpoint
- GROQ_API_KEY / HF_TOKEN: optional model credentials for AI review
