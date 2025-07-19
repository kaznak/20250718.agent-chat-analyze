"""Base class for embedding models"""

from abc import ABC, abstractmethod
from typing import List


class BaseEmbedding(ABC):
    """Base class for embedding models"""
    
    @abstractmethod
    def encode(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts into embeddings
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    def encode_single(self, text: str) -> List[float]:
        """Encode a single text into embedding
        
        Args:
            text: Text to encode
            
        Returns:
            Embedding vector
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension
        
        Returns:
            Dimension of the embedding vectors
        """
        pass