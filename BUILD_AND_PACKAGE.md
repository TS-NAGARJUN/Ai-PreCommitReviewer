# Build and Package Guide

## Quick Start: Build .vsix Package

```bash
cd d:\AI-PreCommitReviewer\extension\ai-pre-commit-reviewer

# 1. Install/Update dependencies
npm install

# 2. Compile TypeScript
npm run compile

# 3. Create .vsix package
npm run package:vsix
```

**Output:** `ai-pre-commit-reviewer-0.0.1.vsix` (ready to distribute)

---

## Installation Methods

### Method 1: VS Code GUI
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Click "..." menu → "Install from VSIX"
4. Select the .vsix file
5. Reload VS Code

### Method 2: Command Line
```bash
code --install-extension ai-pre-commit-reviewer-0.0.1.vsix
```

### Method 3: Distribution to Others
Share `ai-pre-commit-reviewer-0.0.1.vsix` file via:
- GitHub releases
- Email
- File storage
- etc.

---

## Publish to VS Code Marketplace

### Prerequisites
- GitHub account (for authentication)
- VS Code Marketplace account (free)
- Personal Access Token (PAT)

### Step 1: Create Publisher

Go to: https://marketplace.visualstudio.com/manage

Sign in with GitHub → Create New Publisher

Name: `TS-NAGARJUN` (or your preferred name)

### Step 2: Get Personal Access Token

1. Go to: https://dev.azure.com/
2. Create new organization (or use existing)
3. User Settings → Personal access tokens → New Token
4. **Scopes:** Check "Marketplace" → "Manage"
5. **Expiration:** 1 year (or longer)
6. Create → Copy token

### Step 3: Install vsce

```bash
npm install -g @vscode/vsce
```

### Step 4: Login to Publisher

```bash
vsce login TS-NAGARJUN
# Paste your Personal Access Token when prompted
```

### Step 5: Publish

```bash
cd d:\AI-PreCommitReviewer\extension\ai-pre-commit-reviewer

# First time:
vsce publish

# Or with PAT directly:
vsce publish -p YOUR_PAT_HERE
```

**Output:**
```
 INFO  Packaged: ai-pre-commit-reviewer-0.0.1.vsix
 INFO  The operation completed successfully
```

Visit: https://marketplace.visualstudio.com/manage to verify!

---

## Version Bumping

Edit `package.json`:

```json
{
  "version": "0.0.2",  // Increment this
  "name": "ai-pre-commit-reviewer",
  "displayName": "AI Pre-commit Reviewer",
  // ...
}
```

Then:
```bash
npm run compile
npm run package:vsix
vsce publish  # Will use new version from package.json
```

---

## Package.json Fields

Customize the marketplace listing:

```json
{
  "name": "ai-pre-commit-reviewer",
  "displayName": "AI Pre-commit Reviewer",
  "description": "AI-powered code review for Git commits with secret detection",
  "version": "0.0.1",
  "publisher": "TS-NAGARJUN",
  "icon": "icon.png",
  "repository": {
    "type": "git",
    "url": "https://github.com/TS-NAGARJUN/AI-PreCommitReviewer"
  },
  "bugs": {
    "url": "https://github.com/TS-NAGARJUN/AI-PreCommitReviewer/issues"
  },
  "homepage": "https://github.com/TS-NAGARJUN/AI-PreCommitReviewer",
  "license": "MIT",
  "keywords": [
    "git",
    "code-review",
    "ai",
    "pre-commit",
    "security",
    "testing"
  ],
  "engines": {
    "vscode": "^1.120.0"
  }
}
```

---

## Marketplace Listing Tips

### Icons
- Icon size: 128x128 PNG
- Should be recognizable at small sizes
- Put in: `extension/ai-pre-commit-reviewer/icon.png`

### README
Make attractive with:
- 📸 Screenshots (Webview sidebar)
- 🎥 GIFs of workflow
- 💡 Feature highlights
- ⚡ Quick start guide
- 📋 Requirements section

### Keywords
Help discoverability:
```
git, code-review, ai, pre-commit, security, 
testing, groq, huggingface, ai-analysis, 
commit-validation, code-quality
```

### Categories
- Linters
- Other
- SCM Providers

---

## CI/CD Integration (GitHub Actions)

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to VS Code Marketplace

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - run: cd extension/ai-pre-commit-reviewer && npm install
      
      - run: cd extension/ai-pre-commit-reviewer && npm run compile
      
      - run: npm install -g @vscode/vsce
      
      - run: cd extension/ai-pre-commit-reviewer && vsce publish -p ${{ secrets.VSCE_TOKEN }}
```

Then tag releases:
```bash
git tag v0.0.2
git push origin v0.0.2
# GitHub Actions automatically publishes!
```

---

## Troubleshooting

### "vsce not found"
```bash
npm install -g @vscode/vsce
```

### "Cannot publish because publisher is not verified"
Verify your publisher on marketplace.visualstudio.com

### "Your extension version is already published"
Bump version in `package.json`:
```json
"version": "0.0.2"  // Was 0.0.1
```

### "Extension failed to install"
Check `package.json`:
- All required fields present
- No syntax errors
- `engines.vscode` version compatible

---

## Testing Before Publish

### Test .vsix Installation

```bash
# Create test environment
mkdir test-install
cd test-install

# Install extension
code --install-extension path/to/ai-pre-commit-reviewer-0.0.1.vsix

# Load VS Code
code

# Verify:
# 1. Extension appears in Extensions panel
# 2. Sidebar view loads
# 3. "Run Review" button works
# 4. Backend connection shows status
```

### Test in Development Mode

```bash
cd extension/ai-pre-commit-reviewer
code . --extensionDevelopmentPath=.
# Press F5 or Ctrl+F5 to debug
```

---

## File Checklist Before Publishing

- [x] `package.json` — All fields filled
- [x] `tsconfig.json` — TS config correct
- [x] `webpack.config.js` — Build config complete
- [x] `src/extension.ts` — Main code working
- [x] `README.md` — Attractive documentation
- [x] `CHANGELOG.md` — Version history
- [x] `icon.png` — 128x128 PNG
- [x] `.vscodeignore` — Excludes unnecessary files
- [x] `LICENSE` — MIT or other license

---

## After Publishing

### Share & Promote
- Tweet about release
- Share on GitHub discussions
- Ask for feedback
- Monitor ratings/reviews

### Gather Feedback
- GitHub Issues for bugs
- Feature requests
- User testimonials

### Continuous Updates
- Fix bugs promptly
- Add requested features
- Keep documentation current
- Release updates regularly

---

## Support & Troubleshooting

For users:
- GitHub Issues: Bug reports, feature requests
- GitHub Discussions: Q&A, general help
- Email: Include your contact

For development:
- README.md: Installation + basic usage
- CONTRIBUTING.md: How to extend
- Code comments: Implementation details

---

## Success Metrics

Track after publishing:
- 📊 Installation count
- ⭐ Star rating
- 📝 Reviews and feedback
- 🐛 Bug reports
- 🎯 Feature requests
- 📈 Weekly active users

---

**Status: READY TO PUBLISH** ✅

All phases complete. Extension is production-ready!
