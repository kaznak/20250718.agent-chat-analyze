"""Conversation and Message data models"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class Message:
    """Individual message in a conversation"""
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: datetime
    metadata: dict[str, Any]
    embedding: Optional[list[float]] = None  # 384-dimensional vector


@dataclass
class Conversation:
    """Conversation containing multiple messages"""
    id: str
    messages: list[Message]
    started_at: datetime
    ended_at: datetime
    topic: Optional[str] = None
    outcome: Optional[str] = None  # "success" | "failure" | "partial"