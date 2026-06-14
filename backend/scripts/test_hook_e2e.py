#!/usr/bin/env python3
"""End-to-end test: start backend, create temp git repo, install hook, run commit.

This script starts a uvicorn server for the FastAPI app, creates a temporary
git repository, copies the hook into .git/hooks, performs a commit, and
reports whether the hook blocked or permitted the commit.

Run from repo root with the backend venv active, or run via the venv python:

On Windows:
python backend/.venv/Scripts/python.exe scripts/test_hook_e2e.py
"""
import subprocess
import tempfile
import time
import socket
import os
import shutil
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).parent
REPO_ROOT = BACKEND_DIR.parent

HOST = '127.0.0.1'
PORT = 8765


def wait_for_port(host, port, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except Exception:
            time.sleep(0.2)
    return False


def run():
    python = sys.executable
    print('Using python:', python)

    # Start uvicorn
    uvicorn_proc = subprocess.Popen([python, '-m', 'uvicorn', 'app.main:app', '--port', str(PORT)], cwd=str(REPO_ROOT))
    try:
        if not wait_for_port(HOST, PORT, timeout=15.0):
            print('Backend did not become ready on port', PORT)
            uvicorn_proc.terminate()
            uvicorn_proc.wait()
            return 2
        print('Backend is up')

        with tempfile.TemporaryDirectory(dir=str(REPO_ROOT)) as tmpdir:
            tmp = Path(tmpdir)
            print('Creating temp repo at', tmp)
            # git init
            subprocess.run(['git', 'init'], cwd=str(tmp), check=True)
            # minimal config
            subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=str(tmp), check=True)
            subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=str(tmp), check=True)

            # install hook by copying
            hooks_dir = tmp / '.git' / 'hooks'
            hooks_dir.mkdir(parents=True, exist_ok=True)
            src_hook = REPO_ROOT / 'hooks' / 'pre-commit'
            if not src_hook.exists():
                print('Source hook not found at', src_hook)
                return 3
            dest = hooks_dir / 'pre-commit'
            shutil.copy2(str(src_hook), str(dest))
            dest.chmod(0o755)
            print('Copied hook to', dest)

            # create a file and commit
            f = tmp / 'file.txt'
            f.write_text('hello')
            subprocess.run(['git', 'add', 'file.txt'], cwd=str(tmp), check=True)

            # run commit
            print('Running git commit (this will invoke the hook which calls backend)')
            proc = subprocess.run(['git', 'commit', '-m', 'test commit'], cwd=str(tmp), capture_output=True, text=True)
            print('git commit returncode:', proc.returncode)
            print('stdout:\n', proc.stdout)
            print('stderr:\n', proc.stderr)
            return proc.returncode
    finally:
        try:
            uvicorn_proc.terminate()
            uvicorn_proc.wait(timeout=5)
        except Exception:
            pass


if __name__ == '__main__':
    rc = run()
    print('Test finished with exit code', rc)
    sys.exit(rc)
