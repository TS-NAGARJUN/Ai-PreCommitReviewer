import pytest
from app.models import Finding, ReviewResult, Severity
from app.git_analyzer import GitAnalyzer
import tempfile
import os
import subprocess


class TestModels:
    """Test Pydantic data models"""

    def test_severity_enum(self):
        """Test Severity enum values"""
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"

    def test_finding_creation(self):
        """Test Finding model instantiation"""
        finding = Finding(
            file="test.py",
            line=42,
            severity=Severity.HIGH,
            category="security",
            message="Test finding"
        )
        assert finding.file == "test.py"
        assert finding.line == 42
        assert finding.severity == Severity.HIGH
        assert finding.category == "security"

    def test_finding_optional_line(self):
        """Test Finding with optional line number"""
        finding = Finding(
            file="config.json",
            severity=Severity.LOW,
            category="config",
            message="Missing config"
        )
        assert finding.line is None

    def test_review_result_creation(self):
        """Test ReviewResult model"""
        findings = [
            Finding(file="a.py", line=1, severity=Severity.HIGH, 
                   category="security", message="Issue 1")
        ]
        result = ReviewResult(
            riskScore=7.5,
            findings=findings,
            summary="1 high issue found"
        )
        assert result.riskScore == 7.5
        assert len(result.findings) == 1
        assert result.summary == "1 high issue found"


class TestGitAnalyzer:
    """Test Git analyzer functionality"""

    def test_git_analyzer_init(self):
        """Test GitAnalyzer initialization"""
        analyzer = GitAnalyzer(".")
        assert analyzer.path == "."

    def test_git_analyzer_methods_exist(self):
        """Test that GitAnalyzer has required methods"""
        analyzer = GitAnalyzer(".")
        assert hasattr(analyzer, "get_staged_diff")
        assert hasattr(analyzer, "get_changed_files")
        assert hasattr(analyzer, "get_current_branch")
        assert hasattr(analyzer, "get_context")
