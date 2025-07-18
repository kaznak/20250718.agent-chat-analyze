"""Tests for embeddings module"""

import pytest
from unittest.mock import Mock, patch
from agent_chat_analyze.embeddings import BaseEmbedding, SentenceTransformerEmbedding, VectorSearchEngine
from agent_chat_analyze.models import Message
from datetime import datetime


class TestBaseEmbedding:
    """Test BaseEmbedding abstract class"""
    
    def test_base_embedding_is_abstract(self):
        """Test that BaseEmbedding cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseEmbedding()


class TestSentenceTransformerEmbedding:
    """Test SentenceTransformerEmbedding class"""
    
    def test_initialization(self):
        """Test embedding model initialization"""
        embedding = SentenceTransformerEmbedding()
        assert embedding.model_name == "paraphrase-multilingual-MiniLM-L12-v2"
        assert embedding.model is None
        assert embedding._dimension is None
    
    def test_initialization_with_custom_model(self):
        """Test embedding model initialization with custom model"""
        model_name = "custom-model"
        embedding = SentenceTransformerEmbedding(model_name=model_name)
        assert embedding.model_name == model_name
    
    @patch('agent_chat_analyze.embeddings.sentence_transformer.SentenceTransformer')
    def test_load_model(self, mock_sentence_transformer):
        """Test model loading"""
        mock_model = Mock()
        mock_sentence_transformer.return_value = mock_model
        
        embedding = SentenceTransformerEmbedding()
        model = embedding._load_model()
        
        assert model == mock_model
        assert embedding.model == mock_model
        mock_sentence_transformer.assert_called_once_with("paraphrase-multilingual-MiniLM-L12-v2")
    
    @patch('agent_chat_analyze.embeddings.sentence_transformer.SentenceTransformer')
    def test_encode_single(self, mock_sentence_transformer):
        """Test encoding single text"""
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_sentence_transformer.return_value = mock_model
        
        embedding = SentenceTransformerEmbedding()
        result = embedding.encode_single("test text")
        
        assert result == [0.1, 0.2, 0.3]
        mock_model.encode.assert_called_once_with(["test text"])
    
    @patch('agent_chat_analyze.embeddings.sentence_transformer.SentenceTransformer')
    def test_encode_single_empty_text(self, mock_sentence_transformer):
        """Test encoding empty text"""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_sentence_transformer.return_value = mock_model
        
        embedding = SentenceTransformerEmbedding()
        result = embedding.encode_single("")
        
        assert result == [0.0] * 384
        mock_model.encode.assert_not_called()
    
    @patch('agent_chat_analyze.embeddings.sentence_transformer.SentenceTransformer')
    def test_encode_multiple(self, mock_sentence_transformer):
        """Test encoding multiple texts"""
        mock_model = Mock()
        mock_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_model.encode.return_value = Mock()
        mock_model.encode.return_value.tolist.return_value = mock_embeddings
        mock_sentence_transformer.return_value = mock_model
        
        embedding = SentenceTransformerEmbedding()
        result = embedding.encode(["text1", "text2"])
        
        assert result == mock_embeddings
        mock_model.encode.assert_called_once_with(["text1", "text2"])
    
    @patch('agent_chat_analyze.embeddings.sentence_transformer.SentenceTransformer')
    def test_encode_empty_list(self, mock_sentence_transformer):
        """Test encoding empty list"""
        embedding = SentenceTransformerEmbedding()
        result = embedding.encode([])
        
        assert result == []
    
    @patch('agent_chat_analyze.embeddings.sentence_transformer.SentenceTransformer')
    def test_get_dimension(self, mock_sentence_transformer):
        """Test getting embedding dimension"""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_sentence_transformer.return_value = mock_model
        
        embedding = SentenceTransformerEmbedding()
        dimension = embedding.get_dimension()
        
        assert dimension == 384
        assert embedding._dimension == 384


class TestVectorSearchEngine:
    """Test VectorSearchEngine class"""
    
    def test_initialization(self):
        """Test vector search engine initialization"""
        engine = VectorSearchEngine()
        assert engine.repository is None
        
        mock_repo = Mock()
        engine_with_repo = VectorSearchEngine(mock_repo)
        assert engine_with_repo.repository == mock_repo
    
    def test_calculate_cosine_similarity(self):
        """Test cosine similarity calculation"""
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
        engine = VectorSearchEngine()
        
        similarity = engine.calculate_cosine_similarity([], [1.0, 0.0])
        assert similarity == 0.0
        
        similarity = engine.calculate_cosine_similarity([1.0, 0.0], [])
        assert similarity == 0.0
    
    def test_find_similar_messages(self):
        """Test finding similar messages"""
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
        engine = VectorSearchEngine()
        
        results = engine.find_similar_messages([1.0, 0.0], [], threshold=0.8)
        assert results == []
        
        results = engine.find_similar_messages([], [Mock()], threshold=0.8)
        assert results == []
    
    def test_cluster_by_similarity(self):
        """Test clustering messages by similarity"""
        engine = VectorSearchEngine()
        
        # Create test messages with embeddings
        messages = [
            Message("user", "Hello", datetime.now(), {}, [1.0, 0.0, 0.0]),
            Message("user", "Hi", datetime.now(), {}, [0.9, 0.1, 0.0]),
            Message("user", "Goodbye", datetime.now(), {}, [0.0, 0.0, 1.0]),
            Message("user", "Bye", datetime.now(), {}, [0.1, 0.0, 0.9])
        ]
        
        clusters = engine.cluster_by_similarity(messages, threshold=0.8)
        
        assert len(clusters) >= 1  # Should create at least one cluster
        assert all(isinstance(cluster, list) for cluster in clusters)
        assert all(isinstance(msg, Message) for cluster in clusters for msg in cluster)
    
    def test_cluster_by_similarity_empty_input(self):
        """Test clustering with empty input"""
        engine = VectorSearchEngine()
        
        clusters = engine.cluster_by_similarity([], threshold=0.8)
        assert clusters == []
    
    def test_cluster_by_similarity_single_message(self):
        """Test clustering with single message"""
        engine = VectorSearchEngine()
        
        message = Message("user", "Hello", datetime.now(), {}, [1.0, 0.0, 0.0])
        clusters = engine.cluster_by_similarity([message], threshold=0.8)
        
        assert len(clusters) == 1
        assert len(clusters[0]) == 1
        assert clusters[0][0] == message
    
    def test_find_sentiment_similar_messages(self):
        """Test finding sentiment similar messages"""
        engine = VectorSearchEngine()
        
        # Create test messages and reference embeddings
        messages = [
            Message("user", "Great job!", datetime.now(), {}, [1.0, 0.0, 0.0]),
            Message("user", "Not good", datetime.now(), {}, [0.0, 1.0, 0.0]),
            Message("user", "Excellent work", datetime.now(), {}, [0.9, 0.1, 0.0])
        ]
        
        positive_references = [[1.0, 0.0, 0.0], [0.8, 0.2, 0.0]]
        
        results = engine.find_sentiment_similar_messages(
            positive_references, messages, threshold=0.7
        )
        
        assert len(results) >= 1  # Should find at least one similar message
        assert all(isinstance(result, tuple) and len(result) == 2 for result in results)
        assert all(isinstance(result[0], Message) for result in results)
        assert all(isinstance(result[1], float) for result in results)
    
    def test_find_sentiment_similar_messages_empty_input(self):
        """Test finding sentiment similar messages with empty input"""
        engine = VectorSearchEngine()
        
        results = engine.find_sentiment_similar_messages([], [Mock()], threshold=0.7)
        assert results == []
        
        results = engine.find_sentiment_similar_messages([[1.0, 0.0]], [], threshold=0.7)
        assert results == []