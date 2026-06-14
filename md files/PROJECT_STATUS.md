# AI Pre-Commit Reviewer - Project Status

**Last Updated:** June 10, 2026 | **Current Phase:** 1 (Complete)

---

## 📊 Overall Progress

| Phase | Component | Status | Completion |
|-------|-----------|--------|------------|
| 1 | Project Structure & Setup | ✅ Complete | 100% |
| 2 | AI Model Integration | ⏳ Pending | 0% |
| 3 | Secret Scanner | ⏳ Pending | 0% |
| 4 | Webview UI Sidebar | ⏳ Pending | 0% |
| 5 | Pre-commit Hook | ⏳ Pending | 0% |
| 6 | Packaging & Deployment | ⏳ Pending | 0% |

---

## ✅ PHASE 1: PROJECT STRUCTURE & SETUP (COMPLETE)

### Completed Tasks

#### Backend Foundation
- ✅ **FastAPI Application** created (`backend/app/main.py`)
  - CORS middleware configured
  - 3 stub endpoints created:
    - `GET /health` — returns `{"status": "ok", "version": "0.1.0"}`
    - `POST /analyze/context` — gets git context (branch, staged diff, changed files)
    - `POST /analyze/review` — will analyze code (Phase 2)
    - `POST /analyze/hook` — will block commits (Phase 5)

#### Data Models
- ✅ **Pydantic models** (`backend/app/models.py`)
  - `Severity` enum (HIGH, MEDIUM, LOW)
  - `Finding` — individual issue with file, line, severity, category, message
  - `ReviewResult` — complete review with riskScore (0-10), findings, summary
  - `RepoContext` — repo path and branch info

#### Git Integration
- ✅ **GitAnalyzer class** (`backend/app/git_analyzer.py`)
  - Runs git commands via subprocess
  - `get_staged_diff()` — returns staged changes
  - `get_changed_files()` — lists modified files
  - `get_current_branch()` — gets current branch name
  - `get_context()` — combines all into one dict

#### Environment & Configuration
- ✅ **.gitignore** — excludes node_modules, .venv, dist, *.vsix, .env
- ✅ **requirements.txt** — all 6 Python dependencies listed
  - fastapi==0.115.0
  - uvicorn[standard]==0.30.0
  - httpx==0.27.0
  - python-dotenv==1.0.1
  - pydantic==2.7.0
  - gitpython==3.1.43
- ✅ **.env template** — placeholders for GROQ_API_KEY and HF_TOKEN

#### VS Code Extension
- ✅ **TypeScript extension scaffolded** via `yo code`
  - Webpack bundler configured
  - All dependencies installed (343 packages)
  - Ready for `src/extension.ts` modifications
  - `.vscode/` configs ready (launch, tasks, settings)

#### Python Environment
- ✅ **Python 3.12** installed via Windows Package Manager
- ✅ **Virtual environment** created at `backend/.venv`
- ✅ **All dependencies installed** successfully

#### Verification
- ✅ **Health endpoint tested** — returns correct JSON response
- ✅ **Git analyzer class** implemented and ready for integration

### Project Structure
```
d:\AI-PreCommitReviewer\
├── .gitignore
├── backend/
│   ├── .env                          # API keys (template)
│   ├── .venv/                        # Python 3.12 venv ✅ ACTIVE
│   ├── requirements.txt              # All dependencies ✅ INSTALLED
│   └── app/
│       ├── __init__.py               # Package marker
│       ├── models.py                 # Pydantic models ✅
│       ├── git_analyzer.py           # Git CLI wrapper ✅
│       └── main.py                   # FastAPI app ✅
└── extension/
    └── ai-pre-commit-reviewer/
        ├── src/
        │   └── extension.ts          # Main entry (stub)
        ├── package.json              # TypeScript + Webpack ✅
        ├── tsconfig.json             # TS config ✅
        ├── webpack.config.js         # Bundler config ✅
        └── node_modules/             # Dependencies ✅ INSTALLED
```

---

## ⏳ PHASE 2: AI MODEL INTEGRATION (PENDING)

### What Will Be Built

#### Groq API Integration
- [ ] Create `backend/app/ai_models.py` with `GroqClient` class
- [ ] Use **Groq's llama-3.1-70b** (fastest, free tier at console.groq.com)
- [ ] HTTP client using `httpx` for API calls
- [ ] Prompt engineering for code review context

#### HuggingFace Fallback
- [ ] **Qwen2.5-Coder-7B-Instruct** as fallback model
- [ ] HuggingFace Inference API integration
- [ ] Automatic retry logic if Groq fails

#### AI Review Logic
- [ ] Update `/analyze/review` endpoint to:
  1. Get git diff from `GitAnalyzer`
  2. Call Groq API with review prompt
  3. Parse response into `Finding` objects
  4. Calculate risk score (0-10) based on findings
  5. Return `ReviewResult` with findings, summary, suggested commit message

#### Setup Requirements
- [ ] Get **GROQ_API_KEY** from console.groq.com (free tier)
- [ ] Get **HF_TOKEN** from huggingface.co/settings/tokens (free tier)
- [ ] Store in `backend/.env`
- [ ] Test both APIs before proceeding

### Expected Endpoints After Phase 2
```
POST /analyze/review
{
  "repoPath": "d:/my-project"
}

Response:
{
  "riskScore": 7.5,
  "findings": [
    {
      "file": "src/auth.js",
      "line": 42,
      "severity": "high",
      "category": "security",
      "message": "Password exposed in console.log"
    }
  ],
  "summary": "2 critical issues, 3 medium issues detected",
  "commitMsg": "feat(auth): implement JWT token validation"
}
```

---

## ⏳ PHASE 3: SECRET SCANNER (PENDING)

### What Will Be Built

#### Regex-Based Secret Detection
- [ ] Create `backend/app/secret_scanner.py` with `SecretScanner` class
- [ ] No machine learning — pure regex patterns for:
  - AWS access keys (AKIA...)
  - Private SSH keys (-----BEGIN PRIVATE KEY-----)
  - JWT tokens (eyJ...)
  - Database passwords
  - API keys (common patterns)

#### Integration with Review
- [ ] Run **before** AI analysis to catch obvious secrets
- [ ] Add findings to results if secrets detected
- [ ] Mark as CRITICAL severity
- [ ] Block commits with secrets (Phase 5)

#### Patterns to Detect
- AWS: `AKIA[0-9A-Z]{16}`
- Private Keys: `-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----`
- JWT: `eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+`
- DB Passwords: `password\s*[=:]\s*['"](.*)['""]`
- API Keys: `(api_key|apikey|API_KEY)\s*[=:]\s*['"][^'"]+['""]`

---

## ⏳ PHASE 4: WEBVIEW UI SIDEBAR (PENDING)

### What Will Be Built

#### VS Code Sidebar Extension
- [ ] Create `WebviewViewProvider` in `src/extension.ts`
- [ ] Sidebar panel showing:
  - **Repository Overview** — branch, last commit, stats
  - **Risk Score Ring** — circular visualization (0-10)
  - **AI Findings** — high/medium/low severity issues
  - **Security Scan** — secret detections with critical badges
  - **Changed Files** — file tree with +/- line counts
  - **Commit Assistant** — AI-generated commit messages

#### HTML/CSS/JS Webview
- [ ] Create `src/webview.html` with VS Code's Codicon icons
- [ ] Match mockup design (provided in context)
- [ ] Responsive panels with tabs
- [ ] Modal dialogs for detailed findings

#### Communication
- [ ] `src/extension.ts` ↔ `src/webview.js` postMessage protocol
- [ ] Extension sends git context to backend
- [ ] Backend returns findings
- [ ] Webview displays results in real-time

---

## ⏳ PHASE 5: PRE-COMMIT HOOK (PENDING)

### What Will Be Built

#### Git Pre-commit Hook
- [ ] Create `backend/hooks/pre-commit` script
- [ ] Runs on every `git commit` attempt
- [ ] Calls FastAPI `/analyze/hook` endpoint
- [ ] Blocks commit if riskScore ≥ 8/10

#### VS Code SCM Command Intercept
- [ ] Hook into VS Code's Source Control commit command
- [ ] Show pre-commit modal:
  - Risk score (big red number)
  - List of issues found
  - "Review Issues" / "Commit Anyway" / "Cancel" buttons
- [ ] Track commits with risk ≥ 8 and warn user

#### Installation
- [ ] Auto-install hook to `.git/hooks/pre-commit` on extension activation
- [ ] Make executable on Unix-like systems
- [ ] Graceful fallback if hook fails

---

## ⏳ PHASE 6: PACKAGING & DEPLOYMENT (PENDING)

### What Will Be Built

#### Extension Packaging
- [ ] Build TypeScript → JavaScript with Webpack
- [ ] Run `vsce package` to generate `.vsix` file
- [ ] Test installation in fresh VS Code instance

#### Backend Distribution
- [ ] Bundle Python backend into extension package
- [ ] Auto-spawn uvicorn as child process on extension activation
- [ ] Port 8765 managed automatically (find free port if taken)

#### Marketplace Submission
- [ ] Create VS Code Marketplace account
- [ ] Upload `.vsix` to Microsoft VS Code Marketplace
- [ ] Add repository link, license, documentation

#### Release Checklist
- [ ] Test on Windows, macOS, Linux
- [ ] Verify git hook installation
- [ ] Test with sample repos (good & bad code)
- [ ] Documentation complete (README.md, CONTRIBUTING.md)

---

## 🎯 IMMEDIATE NEXT STEPS

### 1. Get API Keys (5 mins)
```
Groq (fastest free tier):
  - Go to console.groq.com
  - Sign up free
  - Copy API key

HuggingFace:
  - Go to huggingface.co/settings/tokens
  - Create free token
  - Copy token
```

### 2. Fill in .env
```bash
# Edit: d:\AI-PreCommitReviewer\backend\.env
GROQ_API_KEY=gsk_... (your key)
HF_TOKEN=hf_... (your token)
```

### 3. Test Health Endpoint
```powershell
cd d:\AI-PreCommitReviewer\backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8765

# In another terminal:
curl http://127.0.0.1:8765/health
```

### 4. Request Phase 2 Prompt
Tell me once the health check passes, and I'll provide the complete **Phase 2 prompt** to wire in Groq + HuggingFace AI models.

---

## 📋 File Checklist

### Backend Files (Complete ✅)
- ✅ `backend/app/__init__.py` — Package marker
- ✅ `backend/app/models.py` — Pydantic schemas
- ✅ `backend/app/git_analyzer.py` — Git context extraction
- ✅ `backend/app/main.py` — FastAPI endpoints
- ✅ `backend/requirements.txt` — Dependencies list
- ✅ `backend/.env` — API key template
- ✅ `.gitignore` — Repository excludes

### Extension Files (Scaffolded ✅)
- ✅ `extension/ai-pre-commit-reviewer/src/extension.ts` — Main stub
- ✅ `extension/ai-pre-commit-reviewer/package.json` — Metadata
- ✅ `extension/ai-precommit-reviewer/tsconfig.json` — TypeScript config
- ✅ `extension/ai-precommit-reviewer/webpack.config.js` — Bundler

### Pending Files
- ⏳ `backend/app/ai_models.py` — Groq + HuggingFace clients (Phase 2)
- ⏳ `backend/app/secret_scanner.py` — Regex secret detection (Phase 3)
- ⏳ `src/webview.html` — Sidebar HTML (Phase 4)
- ⏳ `src/webview.js` — Webview communication (Phase 4)
- ⏳ `backend/hooks/pre-commit` — Git hook script (Phase 5)

---

## 🔗 Quick Reference Commands

### Run Backend
```powershell
cd d:\AI-PreCommitReviewer\backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8765
```

### Test Endpoints
```powershell
# Health check
curl http://127.0.0.1:8765/health

# Get git context (replace path)
curl -X POST http://127.0.0.1:8765/analyze/context -H "Content-Type: application/json" -d '{"repoPath": "."}'
```

### Build Extension
```powershell
cd d:\AI-PreCommitReviewer\extension\ai-pre-commit-reviewer
npm run compile
```

### Package Extension
```powershell
cd d:\AI-PreCommitReviewer\extension\ai-pre-commit-reviewer
vsce package
```

---

## 🚀 Success Criteria

### Phase 1 (✅ DONE)
- [x] Project structure created
- [x] Backend FastAPI working
- [x] Git analyzer implemented
- [x] VS Code extension scaffolded
- [x] Dependencies installed
- [x] Health endpoint verified

### Phase 2 (Next)
- [ ] Groq API integration working
- [ ] HuggingFace fallback ready
- [ ] /analyze/review endpoint returns real findings
- [ ] Risk score calculation implemented

### Phase 3
- [ ] Secret scanner detects 5+ secret patterns
- [ ] Findings marked as CRITICAL
- [ ] Tested with sample secrets

### Phase 4
- [ ] Sidebar shows findings in real-time
- [ ] Modal displays on pre-commit
- [ ] All tabs functional (Overview, Findings, Commit)

### Phase 5
- [ ] Pre-commit hook blocks high-risk commits
- [ ] Hook installs automatically on extension activation
- [ ] Can be disabled in settings

### Phase 6
- [ ] Extension packaged as .vsix
- [ ] Runs on Windows, macOS, Linux
- [ ] Listed on VS Code Marketplace

---

## 📞 Ready for Phase 2?

Once you've:
1. ✅ Gotten Groq API key
2. ✅ Gotten HuggingFace token
3. ✅ Filled in `.env`
4. ✅ Verified health endpoint works

**Tell me and I'll generate the Phase 2 prompt** to add AI model integration! 🚀
