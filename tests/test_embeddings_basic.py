"""Basic tests for embeddings module without external dependencies"""

import pytest
from unittest.mock import Mock, patch
from agent_chat_analyze.models import Message
from datetime import datetime


class TestVectorSearchEngineBasic:
    """Test VectorSearchEngine without external dependencies"""
    
    def test_vector_search_engine_initialization(self):
        """Test vector search engine can be initialized"""
        # Import here to avoid dependency issues
        from agent_chat_analyze.embeddings.vector_search import VectorSearchEngine
        
        engine = VectorSearchEngine()
        assert engine.repository is None
        
        mock_repo = Mock()
        engine_with_repo = VectorSearchEngine(mock_repo)
        assert engine_with_repo.repository == mock_repo
    
    def test_calculate_cosine_similarity_basic(self):
        """Test basic cosine similarity calculation"""
        from agent_chat_analyze.embeddings.vector_search import VectorSearchEngine
        
        engine = VectorSearchEngine()
        
        # Test identical vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = engine.calculate_cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.001
        
        # Test orthogonal vectors
        vec3 = [1.0, 0.0, 0.0]
        vec4 = [0.0, 1.0, 0.0]
        similarity = engine.calculate_cosine_similarity(vec3, vec4)
        assert abs(similarity - 0.0) < 0.001
    
    def test_calculate_cosine_similarity_empty_vectors(self):
        """Test cosine similarity with empty vectors"""
        from agent_chat_analyze.embeddings.vector_search import VectorSearchEngine
        
        engine = VectorSearchEngine()
        
        similarity = engine.calculate_cosine_similarity([], [1.0, 0.0])
        assert similarity == 0.0
        
        similarity = engine.calculate_cosine_similarity([1.0, 0.0], [])
        assert similarity == 0.0
    
    def test_find_similar_messages_basic(self):
        """Test finding similar messages with mock data"""
        from agent_chat_analyze.embeddings.vector_search import VectorSearchEngine
        
        engine = VectorSearchEngine()
        
        # Create test messages with embeddings
        messages = [
            Message("user", "Hello", datetime.now(), {}, [1.0, 0.0, 0.0]),
            Message("user", "Hi", datetime.now(), {}, [0.9, 0.1, 0.0]),
            Message("user", "Goodbye", datetime.now(), {}, [0.0, 0.0, 1.0]),
            Message("user", "No embedding", datetime.now(), {}, None)
        ]
        
        query_embedding = [1.0, 0.0, 0.0]
        results = engine.find_similar_messages(query_embedding, messages, threshold=0.8)
        
        assert len(results) == 2  # Should find 2 similar messages
        assert results[0][1] >= results[1][1]  # Should be sorted by similarity
        assert results[0][1] >= 0.8  # Should meet threshold
    
    def test_find_similar_messages_empty_input(self):
        """Test finding similar messages with empty input"""
        from agent_chat_analyze.embeddings.vector_search import VectorSearchEngine
        
        engine = VectorSearchEngine()
        
        results = engine.find_similar_messages([1.0, 0.0], [], threshold=0.8)
        assert results == []
        
        results = engine.find_similar_messages([], [Mock()], threshold=0.8)
        assert results == []


class TestBaseEmbeddingInterface:
    """Test BaseEmbedding interface"""
    
    def test_base_embedding_is_abstract(self):
        """Test that BaseEmbedding cannot be instantiated directly"""
        from agent_chat_analyze.embeddings.base import BaseEmbedding
        
        with pytest.raises(TypeError):
            BaseEmbedding()


class MockEmbeddingModel:
    """Mock embedding model for testing"""
    
    def encode(self, texts):
        # Return mock embeddings based on text length
        return [[len(text) / 10.0, 0.5, 0.3] for text in texts]
    
    def encode_single(self, text):
        return [len(text) / 10.0, 0.5, 0.3]
    
    def get_dimension(self):
        return 3


class TestEmbeddingIntegration:
    """Test embedding functionality with mock models"""
    
    def test_mock_embedding_functionality(self):
        """Test that embedding interface works with mock model"""
        mock_model = MockEmbeddingModel()
        
        # Test single encoding
        text = "Hello world"
        embedding = mock_model.encode_single(text)
        assert len(embedding) == 3
        assert embedding[0] == len(text) / 10.0
        
        # Test batch encoding
        texts = ["Hello", "World", "Test"]
        embeddings = mock_model.encode(texts)
        assert len(embeddings) == 3
        assert all(len(emb) == 3 for emb in embeddings)
    
    def test_vector_search_with_mock_embeddings(self):
        """Test vector search with mock embeddings"""
        from agent_chat_analyze.embeddings.vector_search import VectorSearchEngine
        
        engine = VectorSearchEngine()
        mock_model = MockEmbeddingModel()
        
        # Create messages with mock embeddings
        messages = []
        for text in ["Hello world", "Hi there", "Goodbye"]:
            embedding = mock_model.encode_single(text)
            message = Message("user", text, datetime.now(), {}, embedding)
            messages.append(message)
        
        # Search for similar messages
        query_text = "Hello earth"
        query_embedding = mock_model.encode_single(query_text)
        
        results = engine.find_similar_messages(
            query_embedding, messages, threshold=0.7, limit=2
        )
        
        assert len(results) <= 2
        assert all(isinstance(result[0], Message) for result in results)
        assert all(isinstance(result[1], float) for result in results)
        
        # Results should be sorted by similarity
        if len(results) > 1:
            assert results[0][1] >= results[1][1]