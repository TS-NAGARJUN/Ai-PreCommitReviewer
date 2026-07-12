const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

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
