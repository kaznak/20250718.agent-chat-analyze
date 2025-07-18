"""Embeddings module for text vectorization"""

from .base import BaseEmbedding
from .vector_search import VectorSearchEngine

# Conditional import for SentenceTransformerEmbedding
try:
    from .sentence_transformer import SentenceTransformerEmbedding
    __all__ = ["BaseEmbedding", "SentenceTransformerEmbedding", "VectorSearchEngine"]
except ImportError:
    # sentence_transformers not available
    __all__ = ["BaseEmbedding", "VectorSearchEngine"]