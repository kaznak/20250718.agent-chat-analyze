"""Base reporter class"""

from abc import ABC, abstractmethod
from typing import List
from ..models import Conversation, AnalysisResult


class BaseReporter(ABC):
    """Base class for analysis report generators"""
    
    @abstractmethod
    def generate_report(self, 
                       conversations: List[Conversation], 
                       analysis_results: List[AnalysisResult]) -> str:
        """Generate analysis report
        
        Args:
            conversations: List of analyzed conversations
            analysis_results: List of analysis results
            
        Returns:
            Generated report content
        """
        pass