"""Base types for analyzers."""
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AnalysisResult:
    rag_status: str             # green | amber | red | na | skipped
    evidence: str               # Human-readable summary of what was found
    confidence: float = 1.0     # 0.0 - 1.0
    files_checked: list[str] = field(default_factory=list)
    skip_reason: Optional[str] = None
    evidence_hint: Optional[str] = None
    audit_payload: Optional[dict[str, Any]] = None
