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

## Install on another machine

If you want to share the CLI without publishing to npm, package it locally and install the tarball on the target machine:

```bash
cd cli
npm pack
```

On the other machine:

```bash
npm install -g review-cli-1.0.0.tgz
```

If you want it available to anyone through npm, publish it once and install it with:

```bash
cd cli
npm login
npm publish --access public
```

Then on any machine:

```bash
npm install -g review-cli
```
