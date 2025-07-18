"""SentenceTransformer-based embedding implementation"""

from typing import List, Optional
from sentence_transformers import SentenceTransformer
from .base import BaseEmbedding


class SentenceTransformerEmbedding(BaseEmbedding):
    """SentenceTransformer-based embedding implementation"""
    
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """Initialize SentenceTransformer embedding
        
        Args:
            model_name: Name of the SentenceTransformer model
        """
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self._dimension: Optional[int] = None
    
    def _load_model(self) -> SentenceTransformer:
        """Load model on first use"""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
        return self.model
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts into embeddings
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of 384-dimensional embedding vectors
        """
        if not texts:
            return []
        
        model = self._load_model()
        embeddings = model.encode(texts)
        return embeddings.tolist()
    
    def encode_single(self, text: str) -> List[float]:
        """Encode a single text into embedding
        
        Args:
            text: Text to encode
            
        Returns:
            384-dimensional embedding vector
        """
        if not text:
            return [0.0] * self.get_dimension()
        
        model = self._load_model()
        embedding = model.encode([text])[0]
        return embedding.tolist()
    
    def get_dimension(self) -> int:
        """Get embedding dimension
        
        Returns:
            384 (dimension of the multilingual MiniLM model)
        """
        if self._dimension is None:
            # Load model to get dimension
            model = self._load_model()
            self._dimension = model.get_sentence_embedding_dimension()
        return self._dimension