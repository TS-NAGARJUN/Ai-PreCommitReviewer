#!/usr/bin/env node
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const https = require('https');

function loadEnvironmentVariables({ cwd = process.cwd(), existingEnv = process.env } = {}) {
  const env = { ...existingEnv };
  const envFiles = [path.join(cwd, '.env'), path.join(cwd, '..', '.env')];

  for (const envFile of envFiles) {
    if (!fs.existsSync(envFile)) continue;

    const content = fs.readFileSync(envFile, 'utf8');
    for (const rawLine of content.split(/\r?\n/)) {
      const line = rawLine.trim();
      if (!line || line.startsWith('#')) continue;
      const separatorIndex = line.indexOf('=');
      if (separatorIndex === -1) continue;
      const key = line.slice(0, separatorIndex).trim();
      const value = line.slice(separatorIndex + 1).trim().replace(/^['"]|['"]$/g, '');
      if (!key) continue;
      if (!env[key]) {
        env[key] = value;
      }
    }
  }

  return env;
}

function runGit(args, cwd) {
  const result = spawnSync('git', args, { cwd, encoding: 'utf8' });
  if (result.status !== 0) {
    throw new Error(result.stderr.trim() || `git ${args.join(' ')} failed`);
  }
  return result.stdout.trim();
}

function validateWorkingDirectory(cwd) {
  if (!cwd || !fs.existsSync(cwd)) {
    throw new Error(`The directory does not exist: ${cwd}`);
  }
  if (!fs.statSync(cwd).isDirectory()) {
    throw new Error(`The path is not a directory: ${cwd}`);
  }
}

function detectRepo(cwd) {
  try {
    runGit(['rev-parse', '--is-inside-work-tree'], cwd);
    return true;
  } catch (_error) {
    return false;
  }
}

function collectContext(cwd) {
  return {
    repoPath: cwd,
    branch: runGit(['branch', '--show-current'], cwd),
    repoName: path.basename(cwd),
    commitHash: runGit(['rev-parse', 'HEAD'], cwd),
    stagedDiff: runGit(['diff', '--cached'], cwd),
    changedFiles: runGit(['status', '--porcelain'], cwd).split('\n').filter(Boolean).map((line) => line.slice(3))
  };
}

function postReview(payload, endpoint) {
  const body = JSON.stringify(payload);
  const url = new URL(endpoint);
  const options = {
    hostname: url.hostname,
    port: url.port || (url.protocol === 'https:' ? 443 : 80),
    path: `${url.pathname}${url.search}`,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(body),
      ...(process.env.REVIEW_API_TOKEN ? { Authorization: `Bearer ${process.env.REVIEW_API_TOKEN}` } : {})
    }
  };

  return new Promise((resolve, reject) => {
    const req = (url.protocol === 'https:' ? https : require('http')).request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        if (res.statusCode && res.statusCode >= 400) {
          reject(new Error(`Backend request failed with ${res.statusCode}: ${data}`));
          return;
        }
        try {
          resolve(JSON.parse(data));
        } catch (error) {
          reject(new Error(`Invalid JSON from backend: ${data}`));
        }
      });
    });

    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

function renderReport(result) {
  console.log('\nReview Summary');
  console.log('-------------');
  console.log(`Severity: ${result.severity || 'low'}`);
  console.log(`Explanation: ${result.explanation || 'No explanation provided.'}`);
  console.log('');
  if (!result.issues || result.issues.length === 0) {
    console.log('No issues found.');
    return;
  }
  console.log(`Issues (${result.issues.length}):`);
  result.issues.forEach((issue, index) => {
    const location = issue.line ? `${issue.file}:${issue.line}` : issue.file;
    console.log(`${index + 1}. [${issue.category || 'other'}] ${location}`);
    console.log(`   ${issue.message}`);
  });
  if (result.suggestedFixes && result.suggestedFixes.length) {
    console.log('');
    console.log('Suggested fixes:');
    result.suggestedFixes.forEach((fix, index) => {
      console.log(`${index + 1}. ${fix}`);
    });
  }
}

async function main() {
  const cwd = process.cwd();
  const env = loadEnvironmentVariables({ cwd });
  const localBackendUrl = 'http://127.0.0.1:8765/review';
  const remoteBackendUrl = 'https://ai-precommitreviewer.onrender.com/review';

  process.env.REVIEW_BACKEND_URL = env.REVIEW_BACKEND_URL || process.env.REVIEW_BACKEND_URL || localBackendUrl;
  process.env.REVIEW_API_TOKEN = env.REVIEW_API_TOKEN || process.env.REVIEW_API_TOKEN;

  try {
    validateWorkingDirectory(cwd);
  } catch (error) {
    console.error(error.message);
    process.exit(1);
  }

  if (!detectRepo(cwd)) {
    console.error(`This directory is not a Git repository: ${cwd}`);
    console.error('Run review from a folder that contains a Git repository, for example:');
    console.error('  cd path/to/your/repo');
    console.error('  review');
    process.exit(1);
  }

  const endpoint = process.env.REVIEW_BACKEND_URL || localBackendUrl || remoteBackendUrl;
  const context = collectContext(cwd);
  if (!context.stagedDiff && !context.changedFiles.length) {
    console.log('No staged changes found.');
    return;
  }
  const result = await postReview(context, endpoint);
  renderReport(result);
}

if (require.main === module) {
  main().catch((error) => {
    console.error(error.message);
    process.exit(1);
  });
}

module.exports = {
  loadEnvironmentVariables,
};
