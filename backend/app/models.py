from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class Severity(str, Enum):
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"

class Finding(BaseModel):
    file:     str
    line:     Optional[int] = None
    severity: Severity
    category: str
    message:  str

class ReviewResult(BaseModel):
    riskScore:  float
    findings:   List[Finding]
    summary:    str
    commitMsg:  Optional[str] = None

class RepoContext(BaseModel):
    repoPath: str
    branch:   str
