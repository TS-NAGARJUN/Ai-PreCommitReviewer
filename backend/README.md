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

## Deploying the backend

This project is a Python/FastAPI service, so it cannot run directly inside Supabase Edge Functions. The practical approach is:

1. Deploy the FastAPI app to a host that supports Python containers or Gunicorn, such as Render, Railway, Fly.io, or Azure App Service.
2. Point the CLI at the deployed URL with REVIEW_BACKEND_URL.
3. Keep Supabase for database/auth/storage if you want to extend the project later.

A Dockerfile and process definition are included for container-based deployments.

Example:

```bash
cd backend
pip install -r requirements.txt
PORT=8000 python app/main.py
```

For hosted platforms, set:

- PORT
- REVIEW_API_TOKEN
- GROQ_API_KEY or HF_TOKEN
