"""Analysis result data model"""

from dataclasses import dataclass
from typing import Any


@dataclass
class AnalysisResult:
    """Result of conversation analysis"""
    conversation_id: str
    analysis_type: str  # "feedback" | "workflow"
    findings: list[dict[str, Any]]
    recommendations: list[str]
    confidence: float