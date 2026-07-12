# AI-PreCommitReviewer

This repository now supports a standalone CLI-first architecture for AI-assisted code review.

## Architecture

- A lightweight npm CLI named review runs from any Git repository.
- The CLI inspects the current repository, reads staged changes, and sends a clean JSON payload to a backend service.
- The backend handles authentication, prompt construction, provider integration, and structured review responses.

## CLI usage

Install the package locally or globally:

```bash
cd cli
npm install
npm link
```

Run it from a Git repository:

```bash
review
```

Set the backend endpoint and optional auth token:

```bash
export REVIEW_BACKEND_URL=http://127.0.0.1:8765/review
export REVIEW_API_TOKEN=your-token
review
```

## Backend usage

Start the FastAPI backend locally:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8765
```

The backend exposes:

- GET /health
- POST /review
- POST /analyze/review
- POST /analyze/context

## Testing

Run the Python backend tests:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest app/test_cli_architecture.py app/test_main.py
```

## Notes

The old extension package has been removed, and the primary workflow is now the standalone CLI plus backend service.

