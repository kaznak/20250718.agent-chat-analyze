"""Feedback data model"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Feedback:
    """User feedback on a specific message"""
    conversation_id: str
    message_id: str
    feedback_type: str  # "positive" | "negative" | "request"
    content: str
    timestamp: datetime