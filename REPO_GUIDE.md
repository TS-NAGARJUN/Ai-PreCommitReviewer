# Review CLI Repository Guide

## 1. Overview

This repository now follows a standalone CLI-first architecture for AI-assisted code review.

### Components
- CLI: a lightweight Node.js package that runs from any Git repository.
- Backend: a FastAPI service that receives staged Git context and returns structured review output.
- AI provider layer: currently supports Gemini first, with fallback to Groq and Hugging Face.

## 2. Repository Structure

```text
backend/
  app/
    ai_models.py         # AI provider integration and response normalization
    git_analyzer.py      # Git repository context collection
    main.py              # FastAPI endpoints
    secret_scanner.py    # Secret detection for staged diffs
    test_main.py         # Backend endpoint tests
    test_cli_architecture.py
  requirements.txt
  README.md

cli/
  bin/
    review.js           # CLI entrypoint
  package.json
  README.md
  test/
    review.test.js

README.md               # Project overview
REPO_GUIDE.md           # This guide
```

## 3. How the System Works

### CLI flow
1. The user runs `review` from a Git repository.
2. The CLI checks whether the current directory is a Git repo.
3. It collects Git context such as:
   - branch name
   - repository name
   - current commit hash
   - staged diff
   - changed files
4. It sends a JSON payload to the backend review endpoint.
5. The backend returns structured review data:
   - issues
   - severity
   - explanation
   - suggestedFixes
6. The CLI renders the result in the terminal.

### Backend flow
1. The backend receives the payload at `/review`.
2. It gathers repository context using GitAnalyzer.
3. It runs secret scanning on the staged diff.
4. It sends the review context to the AI provider.
5. It returns normalized structured JSON.

## 4. REST API Endpoints

### Health
- GET `/health`
- Purpose: verifies the backend is alive.
- Example request:
  ```bash
  curl http://127.0.0.1:8765/health
  ```

### Review
- POST `/review`
- Purpose: main endpoint used by the CLI.
- Required payload:
  ```json
  {
    "repoPath": "."
  }
  ```
- Optional header:
  ```http
  Authorization: Bearer <token>
  ```
- Example request:
  ```bash
  curl -X POST http://127.0.0.1:8765/review \
    -H "Content-Type: application/json" \
    -d '{"repoPath":"."}'
  ```

### Legacy endpoints
- POST `/analyze/review`
- POST `/analyze/context`
- POST `/analyze/hook`
- POST `/analyze/scan`

These still exist for compatibility but the primary workflow is `/review`.

## 5. How to Test the API

### Start the backend
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
$env:GEMINI_API_KEY="your-key-here"
uvicorn app.main:app --host 127.0.0.1 --port 8765
```

### Test health endpoint
```bash
curl http://127.0.0.1:8765/health
```

### Test review endpoint
```bash
curl -X POST http://127.0.0.1:8765/review \
  -H "Content-Type: application/json" \
  -d '{"repoPath":"."}'
```

### Test with auth token
If `REVIEW_API_TOKEN` is set in the backend environment, send:
```bash
curl -X POST http://127.0.0.1:8765/review \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{"repoPath":"."}'
```

## 6. How to Install the CLI

From the project root:
```powershell
cd cli
npm install
npm link
```

After linking, run:
```powershell
review
```

## 7. Environment Variables

### Backend
```powershell
$env:GEMINI_API_KEY="your-gemini-key"
# optional fallback
$env:GROQ_API_KEY="your-groq-key"
$env:HF_TOKEN="your-hf-token"
$env:REVIEW_API_TOKEN="your-shared-token"
$env:REVIEW_BACKEND_URL="http://127.0.0.1:8765/review"
```

### CLI
```powershell
$env:REVIEW_BACKEND_URL="http://127.0.0.1:8765/review"
$env:REVIEW_API_TOKEN="your-shared-token"
```

## 8. Running Tests

### Backend tests
```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest app/test_cli_architecture.py app/test_main.py
```

### CLI tests
```powershell
cd cli
npm test
```

## 9. Deployment Steps

### Local deployment
1. Install Python dependencies in backend.
2. Install Node dependencies in cli.
3. Start the backend with Uvicorn.
4. Link the CLI package.
5. Run `review` from a Git repository.

### Production deployment ideas
- Deploy the FastAPI backend to Render, Railway, Fly.io, or similar.
- Set environment variables securely in the hosting platform.
- Point the CLI to the deployed backend URL via `REVIEW_BACKEND_URL`.
- Optionally protect the endpoint with `REVIEW_API_TOKEN`.

## 10. Pending Work

### Immediate
- Add a real `.env.example` file for backend and CLI configuration.
- Add a more polished CLI output format with colors and summary sections.
- Add request timeout and retry handling for backend failures.

### Medium-term
- Add support for a dedicated review service hosted on Render.
- Add authentication and rate limiting to the backend.
- Add better error messages when the AI provider rejects the request.
- Add support for non-staged diff review modes.

### Nice to have
- Add package publishing for `npm install -g review-cli`.
- Add CI workflow for backend and CLI tests.
- Add Docker support for easier deployment.
