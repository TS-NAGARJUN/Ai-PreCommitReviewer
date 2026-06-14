import subprocess
from typing import List

class GitAnalyzer:
    def __init__(self, repo_path: str):
        self.path = repo_path

    def _run(self, cmd: List[str]) -> str:
        result = subprocess.run(
            cmd, cwd=self.path,
            capture_output=True, text=True
        )
        return result.stdout.strip()

    def get_staged_diff(self) -> str:
        return self._run(["git", "diff", "--cached"])

    def get_changed_files(self) -> List[str]:
        out = self._run(["git", "status", "--porcelain"])
        return [line[3:] for line in out.splitlines() if line]

    def get_current_branch(self) -> str:
        return self._run(["git", "branch", "--show-current"])

    def get_context(self) -> dict:
        return {
            "branch":       self.get_current_branch(),
            "stagedDiff":   self.get_staged_diff(),
            "changedFiles": self.get_changed_files(),
        }
