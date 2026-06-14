# AI-PreCommitReviewer

This repository contains a VS Code extension and a Python backend for performing AI-assisted pre-commit code review.

## Installing Git Hooks (Manual)

You can install the pre-commit hook into a local repository using the provided installer script.

Usage:

```bash
# from repository root
python backend/scripts/install_hook.py install /path/to/your/repo
# to force overwrite
python backend/scripts/install_hook.py install /path/to/your/repo --force
# to uninstall
python backend/scripts/install_hook.py uninstall /path/to/your/repo
```

The extension also attempts to auto-install the hook on activation when opening a workspace folder that contains a `.git` directory. If a hook already exists, it will not overwrite it.

## Running the backend

Create and activate a virtual environment, then install dependencies and start the server:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --port 8765
```

## Using the extension

- Open VS Code on the workspace folder.
- Start the backend server (see above).
- Activate the extension sidebar: `AI Pre-commit Review` from the Activity Bar.
- Click `Run Review` to analyze staged changes.

## Running tests

The repository includes an end-to-end hook test that starts the backend and performs a git commit in a temporary repository.

On Windows PowerShell:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python scripts/test_hook_e2e.py
```

On macOS/Linux:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python scripts/test_hook_e2e.py
```

## Continuous integration

A GitHub Actions workflow runs the backend hook test and compiles the extension on push and pull request.

