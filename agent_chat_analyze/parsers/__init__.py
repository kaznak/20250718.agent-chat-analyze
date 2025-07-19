"""Parser module for different log formats"""

from .base import BaseParser
from .claude_code import ClaudeCodeParser

__all__ = ["BaseParser", "ClaudeCodeParser"]