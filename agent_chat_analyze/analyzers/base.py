"""Base analyzer class"""

from abc import ABC, abstractmethod
from typing import List
from ..models import Conversation, AnalysisResult


class BaseAnalyzer(ABC):
    """Base class for conversation analyzers"""
    
    @abstractmethod
    def analyze(self, conversations: List[Conversation]) -> AnalysisResult:
        """Analyze conversations and return results
        
        Args:
            conversations: List of conversations to analyze
            
        Returns:
            Analysis result
        """
        pass