#!/usr/bin/env python3
"""Install or uninstall the AI pre-commit hook into a local git repository.

Usage:
  install_hook.py install /path/to/repo [--force]
  install_hook.py uninstall /path/to/repo

If no path is provided, the current working directory is used.
"""
import sys
import os
import shutil
from pathlib import Path


def usage():
    print(__doc__)


def install(repo_root: Path, force: bool = False):
    hooks_dir = repo_root / '.git' / 'hooks'
    if not hooks_dir.exists():
        print('No .git/hooks directory found at', hooks_dir)
        return 1

    is_windows = os.name == 'nt'
    source = Path(__file__).parent.parent / 'hooks' / ('pre-commit.ps1' if is_windows else 'pre-commit')
    target = hooks_dir / (source.name)

    if not source.exists():
        print('Source hook not found at', source)
        return 1

    if target.exists() and not force:
        print('Target hook already exists at', target, '- use --force to overwrite')
        return 1

    shutil.copy2(source, target)
    if not is_windows:
        target.chmod(0o755)

    print('Installed hook to', target)
    return 0


def uninstall(repo_root: Path):
    hooks_dir = repo_root / '.git' / 'hooks'
    if not hooks_dir.exists():
        print('No .git/hooks directory found at', hooks_dir)
        return 1

    # try both names
    removed = False
    for name in ('pre-commit', 'pre-commit.ps1'):
        t = hooks_dir / name
        if t.exists():
            t.unlink()
            print('Removed', t)
            removed = True
    if not removed:
        print('No installed hook found to remove')
    return 0


def main(argv):
    if len(argv) < 2:
        usage()
        return 1

    cmd = argv[1]
    repo = Path(argv[2]) if len(argv) >= 3 else Path.cwd()
    repo = repo.resolve()
    force = '--force' in argv

    if cmd == 'install':
        return install(repo, force)
    if cmd == 'uninstall':
        return uninstall(repo)

    usage()
    return 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
