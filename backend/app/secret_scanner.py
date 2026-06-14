import re
from typing import List, Optional


class SecretScanner:
    PATTERNS = [
        {
            "name": "aws_access_key",
            "regex": r"\bAKIA[0-9A-Z]{16}\b",
            "message": "AWS access key detected in staged diff.",
        },
        {
            "name": "private_key",
            "regex": r"-----BEGIN (?:RSA|OPENSSH|EC|DSA) PRIVATE KEY-----",
            "message": "Private key material detected in staged diff.",
        },
        {
            "name": "jwt_token",
            "regex": r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b",
            "message": "JWT or token-looking string detected in staged diff.",
        },
        {
            "name": "db_password",
            "regex": r"(?i)\b(password|passwd)\s*[:=]\s*['\"][^'\"]+['\"]",
            "message": "Database password assignment detected in staged diff.",
        },
        {
            "name": "api_key_assignment",
            "regex": r"(?i)\b(api_key|apikey|API_KEY|secret|token)\s*[:=]\s*['\"][^'\"]+['\"]",
            "message": "API key or secret assignment detected in staged diff.",
        },
    ]

    @classmethod
    def scan(cls, diff_text: str) -> List[dict]:
        findings: List[dict] = []
        if not diff_text:
            return findings

        current_file = "staged diff"
        for line_number, line in enumerate(diff_text.splitlines(), start=1):
            if line.startswith("diff --git"):
                parts = line.split()
                if len(parts) >= 4:
                    path_b = parts[3]
                    if path_b.startswith("b/"):
                        current_file = path_b[2:]
                    else:
                        current_file = path_b
                continue

            for pattern in cls.PATTERNS:
                for match in re.finditer(pattern["regex"], line):
                    findings.append(
                        {
                            "file": current_file,
                            "line": line_number,
                            "severity": "high",
                            "category": "security",
                            "message": pattern["message"],
                        }
                    )
        return findings

    @classmethod
    def has_secrets(cls, diff_text: str) -> bool:
        return bool(cls.scan(diff_text))
