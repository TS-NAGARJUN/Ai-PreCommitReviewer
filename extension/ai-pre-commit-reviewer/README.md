# AI Pre-commit Reviewer

A VS Code extension that integrates with a Python backend to perform AI-assisted pre-commit code review and secret scanning.

## Features

- Sidebar UI to run AI review on staged Git changes.
- Secret-only scan support.
- Optional git hook installation to block risky commits.
- Backend health and review status are shown in the sidebar.

## Requirements

- Visual Studio Code 1.120.0 or later.
- Node.js 20.x for building the extension.
- Python 3.12+ for the backend.
- The backend server must be running for analysis features.

## Local install via VSIX

1. Build the extension:

```bash
cd extension/ai-pre-commit-reviewer
npm install
npm run package
```

2. Install the generated VSIX in VS Code:

- Open the Extensions view.
- Click the ellipsis menu (...) and choose `Install from VSIX...`.
- Select `ai-pre-commit-reviewer-0.0.1.vsix`.

## Publish to Marketplace

1. Update `package.json` with your publisher name:

```json
"publisher": "your-publisher-name"
```

2. Install dependencies and package:

```bash
cd extension/ai-pre-commit-reviewer
npm install
npx vsce package
```

3. Publish:

```bash
cd extension/ai-pre-commit-reviewer
npx vsce publish
```

> Replace `your-publisher-name` with your actual Marketplace publisher ID before publishing.

## Usage

1. Start the backend server:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --port 8765
```

2. Open the workspace in VS Code.
3. Run `AI Pre-commit Review: Show Sidebar`.
4. Click `Run Review`.

## Hook Installer

The extension can prompt to install a git hook for blocking high-risk commits. Hook scripts are stored in `backend/hooks/pre-commit` and `backend/hooks/pre-commit.ps1`.

## Release Notes

### 0.0.1

- Initial publishable extension package.
- Added sidebar review UI and backend integration.
- Added git hook installation support.
