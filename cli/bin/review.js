#!/usr/bin/env node
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const https = require('https');

function runGit(args, cwd) {
  const result = spawnSync('git', args, { cwd, encoding: 'utf8' });
  if (result.status !== 0) {
    throw new Error(result.stderr.trim() || `git ${args.join(' ')} failed`);
  }
  return result.stdout.trim();
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
  if (!detectRepo(cwd)) {
    console.error('This directory is not a Git repository.');
    process.exit(1);
  }

  const endpoint = process.env.REVIEW_BACKEND_URL || 'http://127.0.0.1:8765/review';
  const context = collectContext(cwd);
  if (!context.stagedDiff && !context.changedFiles.length) {
    console.log('No staged changes found.');
    return;
  }
  const result = await postReview(context, endpoint);
  renderReport(result);
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
