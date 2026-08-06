const { spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'review-cli-live-'));
const cwd = tempDir;
spawnSync('git', ['init'], { cwd, stdio: 'inherit' });
spawnSync('git', ['config', 'user.email', 'test@example.com'], { cwd, stdio: 'inherit' });
spawnSync('git', ['config', 'user.name', 'Test User'], { cwd, stdio: 'inherit' });
fs.writeFileSync(path.join(cwd, 'sample.txt'), 'const apiKey = "abc";\n');
spawnSync('git', ['add', 'sample.txt'], { cwd, stdio: 'inherit' });
spawnSync('git', ['commit', '-m', 'init'], { cwd, stdio: 'inherit' });
fs.appendFileSync(path.join(cwd, 'sample.txt'), '\n// staged change\n');
spawnSync('git', ['add', 'sample.txt'], { cwd, stdio: 'inherit' });
const reviewResult = spawnSync('node', ['D:\\AI-PreCommitReviewer\\cli\\bin\\review.js'], {
  cwd,
  encoding: 'utf8',
  env: { ...process.env, REVIEW_BACKEND_URL: 'https://ai-precommitreviewer.onrender.com/review' }
});
console.log('STDOUT:\n' + reviewResult.stdout);
console.log('STDERR:\n' + reviewResult.stderr);
console.log('STATUS:' + reviewResult.status);
