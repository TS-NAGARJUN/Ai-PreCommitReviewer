#!/usr/bin/env node
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const https = require('https');
const chalk = require('chalk').default || require('chalk');
const ora = require('ora').default || require('ora');
const Table = require('cli-table3');
const boxen = require('boxen').default || require('boxen');
const logSymbols = require('log-symbols');

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
          let parsed;
          try {
            parsed = JSON.parse(data);
          } catch (_error) {
            parsed = null;
          }

          const message = parsed && parsed.message
            ? parsed.message
            : `Backend request failed with ${res.statusCode}: ${data}`;
          const error = new Error(message);
          error.issues = Array.isArray(parsed && parsed.issues) ? parsed.issues : [];
          reject(error);
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

function getSeverityColor(severity) {
  const normalizedSeverity = String(severity || 'low').toLowerCase();
  if (normalizedSeverity === 'medium') {
    return chalk.yellow;
  }
  if (normalizedSeverity === 'high' || normalizedSeverity === 'critical') {
    return chalk.red.bold;
  }
  return chalk.green;
}

function getIssueLocation(issue) {
  return issue.line ? `${issue.file}:${issue.line}` : issue.file;
}

function summarizeChangedFiles(context = {}) {
  const changedFiles = Array.isArray(context.changedFiles) ? context.changedFiles : [];
  const diffText = context.stagedDiff || '';
  const lines = diffText.split(/\r?\n/);
  const summaries = [];
  let currentFile = null;
  let additions = 0;
  let deletions = 0;

  const flushCurrentFile = () => {
    if (!currentFile) return;
    summaries.push({ file: currentFile, additions, deletions });
  };

  lines.forEach((line) => {
    const fileMatch = line.match(/^diff --git a\/([^\s]+) b\/([^\s]+)$/);
    if (fileMatch) {
      flushCurrentFile();
      currentFile = fileMatch[2];
      additions = 0;
      deletions = 0;
      return;
    }

    if (!currentFile) return;
    if (line.startsWith('+') && !line.startsWith('+++')) {
      additions += 1;
    } else if (line.startsWith('-') && !line.startsWith('---')) {
      deletions += 1;
    }
  });

  flushCurrentFile();

  if (!summaries.length && changedFiles.length) {
    return changedFiles.map((file) => ({ file, additions: 0, deletions: 0 }));
  }

  return summaries.filter(({ file }) => changedFiles.includes(file));
}

function renderReport(result, context = {}) {
  const severity = String(result.severity || 'low');
  const explanation = result.explanation || 'No explanation provided.';
  const summaryPanel = boxen(
    `${chalk.bold('Review Summary')}\n${chalk.bold('Severity')}: ${getSeverityColor(severity)(severity)}\n${chalk.dim(explanation)}`,
    {
      padding: 1,
      borderStyle: 'round',
      borderColor: 'cyan',
    }
  );

  console.log(summaryPanel);

  const changedFiles = summarizeChangedFiles(context);
  if (changedFiles.length) {
    console.log('');
    console.log(chalk.bold('Changed files:'));
    changedFiles.forEach(({ file, additions, deletions }) => {
      const changeSummary = `${chalk.green(`+${additions}`)} ${chalk.red(`-${deletions}`)}`;
      console.log(`- ${chalk.cyan(file)} (${changeSummary})`);
    });
  }

  const issues = Array.isArray(result.issues) ? result.issues : [];
  if (issues.length === 0) {
    console.log('');
    console.log(`${logSymbols.success} ${chalk.green('No issues found.')}`);
    return;
  }

  const table = new Table({
    head: ['#', 'Category', 'Location', 'Message'],
    style: { head: ['cyan'] },
    wordWrap: true,
  });

  issues.forEach((issue, index) => {
    const location = getIssueLocation(issue);
    table.push([
      index + 1,
      chalk.magenta(issue.category || 'other'),
      location,
      issue.message || ''
    ]);
  });

  console.log('');
  console.log(table.toString());

  if (result.suggestedFixes && result.suggestedFixes.length) {
    console.log('');
    console.log(chalk.bold.underline('Suggested fixes:'));
    result.suggestedFixes.forEach((fix, index) => {
      console.log(`${chalk.cyan(`${index + 1}.`)} ${fix}`);
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
    console.log(`${logSymbols.info} ${chalk.dim('No staged changes found.')}`);
    return;
  }

  const spinner = ora({ text: 'Reviewing staged changes...', color: 'cyan' }).start();
  try {
    const result = await postReview(context, endpoint);
    spinner.succeed('Review complete');
    renderReport(result, context);
  } catch (error) {
    spinner.fail('Review failed');
    if (Array.isArray(error.issues) && error.issues.length) {
      const locations = error.issues.map((issue) => getIssueLocation(issue)).join(', ');
      error.message = `${error.message} (${locations})`;
    }
    throw error;
  }
}

if (require.main === module) {
  main().catch((error) => {
    console.error(chalk.red(`${logSymbols.error} ${error.message}`));
    process.exit(1);
  });
}

module.exports = {
  loadEnvironmentVariables,
  renderReport,
};
