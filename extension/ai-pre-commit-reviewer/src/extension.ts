import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

const BACKEND_BASE_URL = 'http://127.0.0.1:8765';

export async function activate(context: vscode.ExtensionContext) {
	const provider = new AIPreCommitReviewSidebarProvider(context);

	context.subscriptions.push(
		vscode.window.registerWebviewViewProvider('aiPreCommitReviewer.sidebar', provider),
	);

	context.subscriptions.push(
		vscode.commands.registerCommand('ai-pre-commit-reviewer.showSidebar', async () => {
			await vscode.commands.executeCommand('workbench.view.extension.aiPreCommitReviewer');
		}),
	);

	// Prompt user to install git hook for the workspace repository
	try {
		const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
		if (workspaceFolder) {
			const repoRoot = workspaceFolder.uri.fsPath;
			const choice = await vscode.window.showInformationMessage(
				'Install AI pre-commit hook into this repository?',
				'Install Hook',
				'Skip'
			);
			if (choice === 'Install Hook') {
				installGitHook(repoRoot);
			}
		}
	} catch (err) {
		console.error('Failed to offer git hook installation:', err);
	}
}

export function deactivate() {}

class AIPreCommitReviewSidebarProvider implements vscode.WebviewViewProvider {
	private view?: vscode.WebviewView;

	constructor(private readonly extensionContext: vscode.ExtensionContext) {}

	public resolveWebviewView(webviewView: vscode.WebviewView) {
		this.view = webviewView;
		webviewView.webview.options = {
			enableScripts: true,
		};

		webviewView.webview.html = this.getHtmlForWebview(webviewView.webview);

		webviewView.webview.onDidReceiveMessage(async (message) => {
			switch (message.type) {
				case 'refresh':
					await this.postStatus();
					break;
				case 'runReview':
					await this.runReview();
					break;
			}
		});

		this.postStatus();
	}

	private getWorkspaceRepoPath(): string | undefined {
		const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
		return workspaceFolder?.uri.fsPath;
	}

	private async postStatus() {
		if (!this.view) {
			return;
		}

		const repoPath = this.getWorkspaceRepoPath();
		if (!repoPath) {
			this.view.webview.postMessage({
				type: 'status',
				status: 'noWorkspace',
				message: 'Open a folder in VS Code to enable AI review.',
			});
			return;
		}

		try {
			const response = await fetch(`${BACKEND_BASE_URL}/health`);
			if (!response.ok) {
				throw new Error(`Backend responded with ${response.status}`);
			}

			this.view.webview.postMessage({
				type: 'status',
				status: 'ready',
				message: 'Backend available. Ready to analyze staged changes.',
			});
		} catch (error) {
			this.view.webview.postMessage({
				type: 'status',
				status: 'backendUnavailable',
				message: 'Backend is not running at http://127.0.0.1:8765.',
			});
		}
	}

	private async runReview() {
		if (!this.view) {
			return;
		}

		const repoPath = this.getWorkspaceRepoPath();
		if (!repoPath) {
			this.view.webview.postMessage({
				type: 'reviewResult',
				error: 'Open a folder in VS Code to run a review.',
			});
			return;
		}

		this.view.webview.postMessage({ type: 'loading' });

		try {
			const response = await fetch(`${BACKEND_BASE_URL}/analyze/review`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ repoPath }),
			});

			if (!response.ok) {
				throw new Error(`Backend returned ${response.status}`);
			}

			const result = await response.json();
			this.view.webview.postMessage({
				type: 'reviewResult',
				result,
			});
		} catch (error) {
			this.view.webview.postMessage({
				type: 'reviewResult',
				error: error instanceof Error ? error.message : String(error),
			});
		}
	}

	private getHtmlForWebview(webview: vscode.Webview): string {
		const nonce = this.getNonce();
		return `<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8" />
	<meta name="viewport" content="width=device-width, initial-scale=1.0" />
	<title>AI Review</title>
	<style>
		body {
			font-family: var(--vscode-font-family);
			color: var(--vscode-editor-foreground);
			background-color: var(--vscode-editor-background);
			margin: 0;
			padding: 16px;
		}
		.header {
			display: flex;
			justify-content: space-between;
			align-items: center;
			margin-bottom: 16px;
		}
		.button {
			border: none;
			padding: 10px 14px;
			border-radius: 6px;
			cursor: pointer;
			font-weight: 600;
			background-color: var(--vscode-button-background);
			color: var(--vscode-button-foreground);
		}
		.button:hover {
			background-color: var(--vscode-button-hoverBackground);
		}
		.card {
			border: 1px solid var(--vscode-editorWidget-border);
			border-radius: 12px;
			padding: 16px;
			margin-bottom: 16px;
		}
		.score {
			font-size: 48px;
			font-weight: 700;
			margin: 0;
		}
		.summary {
			margin: 8px 0 0;
			color: var(--vscode-editorCodeLens-foreground);
		}
		.issue-list {
			list-style: none;
			padding: 0;
			margin: 0;
		}
		.issue-item {
			padding: 12px;
			border: 1px solid var(--vscode-editorWidget-border);
			border-radius: 8px;
			margin-bottom: 10px;
		}
		.issue-item strong {
			display: block;
			margin-bottom: 4px;
		}
		.issue-meta {
			font-size: 0.9em;
			color: var(--vscode-editorCodeLens-foreground);
		}
		.empty-state {
			color: var(--vscode-editorHint-foreground);
		}
		#error {
			color: var(--vscode-editorError-foreground);
			margin-top: 12px;
		}
	</style>
</head>
<body>
	<div class="header">
		<div>
			<h2>AI Pre-commit Review</h2>
			<p id="statusText">Initializing...</p>
		</div>
		<button class="button" id="reviewButton">Run Review</button>
	</div>

	<div class="card">
		<p class="summary" id="repoPath">Workspace: <em>not detected</em></p>
		<p class="summary" id="resultSummary">No review results yet.</p>
	</div>

	<div class="card">
		<p class="score" id="riskScore">—</p>
		<p class="summary" id="riskLabel">Risk score</p>
	</div>

	<div class="card">
		<h3>Findings</h3>
		<ul class="issue-list" id="findingsList">
			<li class="empty-state">Run a review to see findings here.</li>
		</ul>
	</div>

	<div id="error"></div>

	<script nonce="${nonce}">
		const vscodeApi = acquireVsCodeApi();
		const statusText = document.getElementById('statusText');
		const repoPathText = document.getElementById('repoPath');
		const resultSummary = document.getElementById('resultSummary');
		const riskScore = document.getElementById('riskScore');
		const findingsList = document.getElementById('findingsList');
		const errorElement = document.getElementById('error');
		const reviewButton = document.getElementById('reviewButton');

		if (reviewButton) {
			reviewButton.addEventListener('click', () => {
				vscodeApi.postMessage({ type: 'runReview' });
			});
		}

		window.addEventListener('message', (event) => {
			const message = event.data;
			if (errorElement) {
				errorElement.textContent = '';
			}

			switch (message.type) {
				case 'status':
					if (statusText) {
						statusText.textContent = message.message;
					}
					if (reviewButton) {
						reviewButton.disabled = message.status === 'backendUnavailable';
					}
					break;
				case 'loading':
					if (statusText) {
						statusText.textContent = 'Running review…';
					}
					if (reviewButton) {
						reviewButton.disabled = true;
					}
					break;
				case 'reviewResult':
					if (message.error) {
						if (statusText) {
							statusText.textContent = 'Review failed';
						}
						if (reviewButton) {
							reviewButton.disabled = false;
						}
						if (errorElement) {
							errorElement.textContent = message.error;
						}
						return;
					}
					const result = message.result;
					if (statusText) {
						statusText.textContent = result.summary || 'Review complete';
					}
					if (riskScore) {
						riskScore.textContent = String(result.riskScore ?? 0.0);
					}
					if (resultSummary) {
						resultSummary.textContent = result.commitMsg || result.summary || 'No summary available.';
					}
					if (findingsList) {
						findingsList.innerHTML = '';
						if (Array.isArray(result.findings) && result.findings.length > 0) {
							for (const finding of result.findings) {
								const item = document.createElement('li');
								item.className = 'issue-item';
								item.innerHTML = '<strong>' +
									finding.category.toUpperCase() + ' — ' +
									finding.severity +
									'</strong><div class="issue-meta">' +
									finding.file + ':' +
									(finding.line ?? '-') +
									' ' +
									finding.message +
									'</div>';
								findingsList.appendChild(item);
							}
						} else {
							findingsList.innerHTML = '<li class="empty-state">No findings detected.</li>';
						}
					}
					if (reviewButton) {
						reviewButton.disabled = false;
					}
					break;
			}
		});

		vscodeApi.postMessage({ type: 'refresh' });
	</script>
</body>
</html>`;
	}

	private getNonce(): string {
		let text = '';
		const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
		for (let i = 0; i < 32; i++) {
			text += possible.charAt(Math.floor(Math.random() * possible.length));
		}
		return text;
	}
}

function installGitHook(repoRoot: string) {
	try {
		const gitHooksDir = path.join(repoRoot, '.git', 'hooks');
		if (!fs.existsSync(gitHooksDir)) {
			console.warn('.git/hooks not found, skipping hook installation');
			return;
		}

		const isWindows = process.platform === 'win32';
		const sourceHook = isWindows
			? path.join(repoRoot, 'backend', 'hooks', 'pre-commit.ps1')
			: path.join(repoRoot, 'backend', 'hooks', 'pre-commit');

		const targetHook = path.join(gitHooksDir, isWindows ? 'pre-commit.ps1' : 'pre-commit');

		if (!fs.existsSync(sourceHook)) {
			console.warn('Source hook not found at', sourceHook);
			return;
		}

		// Do not overwrite existing hooks unless they were installed by us
		if (fs.existsSync(targetHook)) {
			console.log('Git hook already exists at', targetHook);
			return;
		}

		fs.copyFileSync(sourceHook, targetHook);
		if (!isWindows) {
			fs.chmodSync(targetHook, 0o755);
		}

		console.log('Installed git hook to', targetHook);
		vscode.window.showInformationMessage('AI pre-commit hook installed.');
	} catch (err) {
		console.error('installGitHook error:', err);
	}
}
