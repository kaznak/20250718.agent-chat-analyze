"""Base parser class"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from ..models import Conversation


class BaseParser(ABC):
    """Abstract base class for log parsers"""
    
    @abstractmethod
    def parse(self, file_path: Path) -> List[Conversation]:
        """Parse log file and return conversations
        
        Args:
            file_path: Path to the log file
            
        Returns:
            List of Conversation objects
        """
        pass
    
    @abstractmethod
    def validate_format(self, file_path: Path) -> bool:
        """Validate if file is in correct format
        
        Args:
            file_path: Path to the log file
            
        Returns:
            True if file format is valid, False otherwise
        """
        pass