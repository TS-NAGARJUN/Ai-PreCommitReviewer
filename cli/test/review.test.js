const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const { loadEnvironmentVariables } = require('../bin/review.js');

test('review command exits when run outside a git repo', () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'review-cli-test-'));
  const result = spawnSync('node', [path.join(__dirname, '..', 'bin', 'review.js')], {
    cwd: tempDir,
    encoding: 'utf8',
    env: { ...process.env, REVIEW_BACKEND_URL: 'http://127.0.0.1:8765/review' }
  });
  assert.notStrictEqual(result.status, 0);
  assert.match(result.stderr, /not a Git repository/i);
  fs.rmSync(tempDir, { recursive: true, force: true });
});

test('loadEnvironmentVariables reads values from .env files', () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'review-cli-env-'));
  fs.writeFileSync(path.join(tempDir, '.env'), 'REVIEW_BACKEND_URL=https://example.test/review\nREVIEW_API_TOKEN=abc123\n');

  const result = loadEnvironmentVariables({ cwd: tempDir, existingEnv: {} });

  assert.equal(result.REVIEW_BACKEND_URL, 'https://example.test/review');
  assert.equal(result.REVIEW_API_TOKEN, 'abc123');
  fs.rmSync(tempDir, { recursive: true, force: true });
});

test('review command reports when the current directory does not exist', () => {
  const missingDir = path.join(os.tmpdir(), 'review-cli-missing-dir');
  fs.mkdirSync(missingDir, { recursive: true });
  const originalCwd = process.cwd();
  process.chdir(missingDir);

  try {
    const result = spawnSync('node', [path.join(__dirname, '..', 'bin', 'review.js')], {
      cwd: missingDir,
      encoding: 'utf8',
      env: { ...process.env, REVIEW_BACKEND_URL: 'http://127.0.0.1:8765/review' }
    });

    assert.notStrictEqual(result.status, 0);
    assert.match(`${result.stdout}\n${result.stderr}`, /not a Git repository/i);
  } finally {
    process.chdir(originalCwd);
  }
});
