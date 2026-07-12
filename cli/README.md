# review-cli

A lightweight cross-platform CLI that reads staged Git changes from the current repository and sends them to a review backend for structured feedback.

## Install locally

```bash
npm install
npm link
```

## Usage

```bash
review
```

Set the backend endpoint and token before running:

```bash
export REVIEW_BACKEND_URL=http://127.0.0.1:8765/review
export REVIEW_API_TOKEN=your-token
review
```
