"""Tests for analyzers module"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from agent_chat_analyze.analyzers import BaseAnalyzer, FeedbackAnalyzer, WorkflowAnalyzer
from agent_chat_analyze.models import Conversation, Message, AnalysisResult


class TestBaseAnalyzer:
    """Test BaseAnalyzer abstract class"""
    
    def test_base_analyzer_is_abstract(self):
        """Test that BaseAnalyzer cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseAnalyzer()


class TestFeedbackAnalyzer:
    """Test FeedbackAnalyzer class"""
    
    @pytest.fixture
    def mock_embedding_model(self):
        """Create mock embedding model"""
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_model.encode_single.return_value = [0.1, 0.2, 0.3]
        return mock_model
    
    @pytest.fixture
    def sample_conversations(self):
        """Create sample conversations for testing"""
        conversations = []
        
        # Positive feedback conversation
        conv1 = Conversation(
            id="conv1",
            messages=[
                Message("user", "Hello", datetime.now(), {}, [0.1, 0.2, 0.3]),
                Message("assistant", "Hi there!", datetime.now(), {}, [0.4, 0.5, 0.6]),
                Message("user", "素晴らしい実装です。完璧です。", datetime.now(), {}, [0.7, 0.8, 0.9])
            ],
            started_at=datetime.now() - timedelta(hours=1),
            ended_at=datetime.now(),
            outcome="success"
        )
        
        # Negative feedback conversation
        conv2 = Conversation(
            id="conv2",
            messages=[
                Message("user", "Help with code", datetime.now(), {}, [0.2, 0.3, 0.4]),
                Message("assistant", "Here's the code", datetime.now(), {}, [0.5, 0.6, 0.7]),
                Message("user", "これは不十分です。改善が必要です。", datetime.now(), {}, [0.8, 0.9, 1.0])
            ],
            started_at=datetime.now() - timedelta(hours=2),
            ended_at=datetime.now() - timedelta(hours=1),
            outcome="failure"
        )
        
        conversations.extend([conv1, conv2])
        return conversations
    
    def test_initialization(self, mock_embedding_model):
        """Test analyzer initialization"""
        analyzer = FeedbackAnalyzer(mock_embedding_model)
        assert analyzer.embedding_model == mock_embedding_model
        assert analyzer.vector_search is not None
        assert len(analyzer.positive_references) > 0
        assert len(analyzer.negative_references) > 0
        assert len(analyzer.request_references) > 0
    
    def test_analyze_empty_conversations(self, mock_embedding_model):
        """Test analyzing empty conversations"""
        analyzer = FeedbackAnalyzer(mock_embedding_model)
        result = analyzer.analyze([])
        
        assert isinstance(result, AnalysisResult)
        assert result.conversation_id == "all"
        assert result.analysis_type == "feedback"
        assert result.findings["total_messages"] == 0
        assert result.confidence == 0.0
    
    def test_analyze_with_conversations(self, mock_embedding_model, sample_conversations):
        """Test analyzing conversations with feedback"""
        analyzer = FeedbackAnalyzer(mock_embedding_model)
        result = analyzer.analyze(sample_conversations)
        
        assert isinstance(result, AnalysisResult)
        assert result.conversation_id == "all"
        assert result.analysis_type == "feedback"
        assert result.findings["total_messages"] > 0
        assert "sentiment_distribution" in result.findings
        assert "feedback_clusters" in result.findings
        assert "temporal_patterns" in result.findings
        assert len(result.recommendations) > 0
        assert result.confidence > 0.0
    
    def test_ensure_embeddings(self, mock_embedding_model):
        """Test ensuring messages have embeddings"""
        analyzer = FeedbackAnalyzer(mock_embedding_model)
        
        messages = [
            Message("user", "Test message", datetime.now(), {}, None),
            Message("user", "Another message", datetime.now(), {}, [0.1, 0.2, 0.3])
        ]
        
        analyzer._ensure_embeddings(messages)
        
        assert messages[0].embedding is not None
        assert messages[1].embedding == [0.1, 0.2, 0.3]  # Should not change
        mock_embedding_model.encode_single.assert_called_once_with("Test message")
    
    @patch('agent_chat_analyze.analyzers.feedback_analyzer.VectorSearchEngine')
    def test_analyze_sentiment_with_vectors(self, mock_vector_search, mock_embedding_model):
        """Test sentiment analysis with vectors"""
        mock_search_instance = Mock()
        mock_search_instance.calculate_cosine_similarity.return_value = 0.8
        mock_vector_search.return_value = mock_search_instance
        
        analyzer = FeedbackAnalyzer(mock_embedding_model)
        analyzer.vector_search = mock_search_instance
        
        messages = [
            Message("user", "Great work!", datetime.now(), {}, [0.1, 0.2, 0.3])
        ]
        
        positive_embeddings = [[0.4, 0.5, 0.6]]
        negative_embeddings = [[0.7, 0.8, 0.9]]
        request_embeddings = [[0.2, 0.3, 0.4]]
        
        result = analyzer._analyze_sentiment_with_vectors(
            messages, positive_embeddings, negative_embeddings, request_embeddings
        )
        
        assert "detailed" in result
        assert "distribution" in result
        assert "counts" in result
        assert len(result["detailed"]) == 1
        assert result["detailed"][0]["sentiment"] in ["positive", "negative", "request", "neutral"]
    
    def test_cluster_feedback(self, mock_embedding_model):
        """Test clustering feedback messages"""
        analyzer = FeedbackAnalyzer(mock_embedding_model)
        
        # Mock cluster_by_similarity to return clusters
        analyzer.vector_search.cluster_by_similarity = Mock(return_value=[
            [
                Message("user", "Great work!", datetime.now(), {}, [0.1, 0.2, 0.3]),
                Message("user", "Excellent job!", datetime.now(), {}, [0.1, 0.2, 0.3])
            ],
            [
                Message("user", "Not good", datetime.now(), {}, [0.4, 0.5, 0.6])
            ]
        ])
        
        messages = [
            Message("user", "Great work!", datetime.now(), {}, [0.1, 0.2, 0.3]),
            Message("user", "Excellent job!", datetime.now(), {}, [0.1, 0.2, 0.3]),
            Message("user", "Not good", datetime.now(), {}, [0.4, 0.5, 0.6])
        ]
        
        clusters = analyzer._cluster_feedback(messages)
        
        assert len(clusters) >= 1
        assert all("cluster_id" in cluster for cluster in clusters)
        assert all("message_count" in cluster for cluster in clusters)
        assert all("sample_messages" in cluster for cluster in clusters)
    
    def test_extract_common_themes(self, mock_embedding_model):
        """Test extracting common themes from message cluster"""
        analyzer = FeedbackAnalyzer(mock_embedding_model)
        
        messages = [
            Message("user", "code implementation test", datetime.now(), {}, [0.1, 0.2, 0.3]),
            Message("user", "test code quality", datetime.now(), {}, [0.4, 0.5, 0.6]),
            Message("user", "implementation quality", datetime.now(), {}, [0.7, 0.8, 0.9])
        ]
        
        themes = analyzer._extract_common_themes(messages)
        
        assert isinstance(themes, list)
        # Should find common words like "code", "test", "implementation", "quality"
        assert len(themes) > 0
    
    def test_calculate_confidence(self, mock_embedding_model):
        """Test calculating confidence score"""
        analyzer = FeedbackAnalyzer(mock_embedding_model)
        
        messages = [
            Message("user", "Test message", datetime.now(), {}, [0.1, 0.2, 0.3]),
            Message("user", "Another message", datetime.now(), {}, [0.4, 0.5, 0.6])
        ]
        
        sentiment_analysis = {
            "detailed": [
                {"positive_score": 0.8, "negative_score": 0.3, "request_score": 0.2},
                {"positive_score": 0.2, "negative_score": 0.9, "request_score": 0.1}
            ]
        }
        
        confidence = analyzer._calculate_confidence(messages, sentiment_analysis)
        
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0


class TestWorkflowAnalyzer:
    """Test WorkflowAnalyzer class"""
    
    @pytest.fixture
    def sample_conversations(self):
        """Create sample conversations for testing"""
        conversations = []
        
        # Successful conversation
        conv1 = Conversation(
            id="conv1",
            messages=[
                Message("user", "実装してください", datetime.now() - timedelta(hours=1), {}),
                Message("assistant", "実装します", datetime.now() - timedelta(minutes=50), {}),
                Message("user", "テストを追加してください", datetime.now() - timedelta(minutes=30), {}),
                Message("assistant", "テストを作成しました", datetime.now() - timedelta(minutes=20), {}),
                Message("user", "完了しました。素晴らしいです。", datetime.now() - timedelta(minutes=10), {})
            ],
            started_at=datetime.now() - timedelta(hours=1),
            ended_at=datetime.now() - timedelta(minutes=10),
            outcome="success"
        )
        
        # Failed conversation
        conv2 = Conversation(
            id="conv2",
            messages=[
                Message("user", "バグを修正してください", datetime.now() - timedelta(hours=2), {}),
                Message("assistant", "修正します", datetime.now() - timedelta(minutes=110), {}),
                Message("user", "エラーが発生しています", datetime.now() - timedelta(minutes=80), {}),
                Message("assistant", "確認します", datetime.now() - timedelta(minutes=70), {}),
                Message("user", "まだ問題があります", datetime.now() - timedelta(minutes=60), {})
            ],
            started_at=datetime.now() - timedelta(hours=2),
            ended_at=datetime.now() - timedelta(minutes=60),
            outcome="failure"
        )
        
        conversations.extend([conv1, conv2])
        return conversations
    
    def test_initialization(self):
        """Test analyzer initialization"""
        analyzer = WorkflowAnalyzer()
        assert len(analyzer.success_indicators) > 0
        assert len(analyzer.blocking_indicators) > 0
        assert len(analyzer.progress_indicators) > 0
    
    def test_analyze_empty_conversations(self):
        """Test analyzing empty conversations"""
        analyzer = WorkflowAnalyzer()
        result = analyzer.analyze([])
        
        assert isinstance(result, AnalysisResult)
        assert result.conversation_id == "all"
        assert result.analysis_type == "workflow"
        assert result.findings["total_conversations"] == 0
        assert result.confidence == 0.0
    
    def test_analyze_with_conversations(self, sample_conversations):
        """Test analyzing conversations with workflow patterns"""
        analyzer = WorkflowAnalyzer()
        result = analyzer.analyze(sample_conversations)
        
        assert isinstance(result, AnalysisResult)
        assert result.conversation_id == "all"
        assert result.analysis_type == "workflow"
        assert result.findings["total_conversations"] == 2
        assert "success_factors" in result.findings
        assert "blocking_factors" in result.findings
        assert "efficiency_metrics" in result.findings
        assert len(result.recommendations) > 0
        assert result.confidence > 0.0
    
    def test_analyze_conversation(self, sample_conversations):
        """Test analyzing single conversation"""
        analyzer = WorkflowAnalyzer()
        conversation = sample_conversations[0]  # Successful conversation
        
        analysis = analyzer._analyze_conversation(conversation)
        
        assert analysis["conversation_id"] == conversation.id
        assert analysis["outcome"] == conversation.outcome
        assert "duration" in analysis
        assert "message_count" in analysis
        assert "success_signals" in analysis
        assert "blocking_signals" in analysis
        assert "progress_signals" in analysis
        assert "workflow_stages" in analysis
        
        # Should find some success signals
        assert len(analysis["success_signals"]) > 0
    
    def test_calculate_duration(self, sample_conversations):
        """Test calculating conversation duration"""
        analyzer = WorkflowAnalyzer()
        conversation = sample_conversations[0]
        
        duration = analyzer._calculate_duration(conversation)
        
        assert "total_minutes" in duration
        assert "active_periods" in duration
        assert "start_time" in duration
        assert "end_time" in duration
        assert isinstance(duration["total_minutes"], float)
        assert isinstance(duration["active_periods"], int)
        assert duration["active_periods"] >= 1
    
    def test_identify_workflow_stages(self, sample_conversations):
        """Test identifying workflow stages"""
        analyzer = WorkflowAnalyzer()
        conversation = sample_conversations[0]
        
        stages = analyzer._identify_workflow_stages(conversation)
        
        assert isinstance(stages, list)
        assert len(stages) > 0
        for stage in stages:
            assert "stage" in stage
            assert "start_time" in stage
            assert "end_time" in stage
            assert "duration_minutes" in stage
            assert stage["stage"] in ["requirements", "implementation", "testing", "deployment", "discussion"]
    
    def test_aggregate_success_factors(self, sample_conversations):
        """Test aggregating success factors"""
        analyzer = WorkflowAnalyzer()
        
        # Create conversation analyses
        conversation_analyses = []
        for conv in sample_conversations:
            analysis = analyzer._analyze_conversation(conv)
            conversation_analyses.append(analysis)
        
        success_factors = analyzer._aggregate_success_factors(conversation_analyses)
        
        assert isinstance(success_factors, list)
        for factor in success_factors:
            assert "indicator" in factor
            assert "role" in factor
            assert "frequency" in factor
            assert "success_rate" in factor
            assert 0.0 <= factor["success_rate"] <= 1.0
    
    def test_calculate_efficiency_metrics(self, sample_conversations):
        """Test calculating efficiency metrics"""
        analyzer = WorkflowAnalyzer()
        
        conversation_analyses = []
        for conv in sample_conversations:
            analysis = analyzer._analyze_conversation(conv)
            conversation_analyses.append(analysis)
        
        metrics = analyzer._calculate_efficiency_metrics(sample_conversations, conversation_analyses)
        
        assert "total_conversations" in metrics
        assert "success_rate" in metrics
        assert "failure_rate" in metrics
        assert "partial_rate" in metrics
        assert "average_duration_minutes" in metrics
        assert "average_message_count" in metrics
        assert "outcome_distribution" in metrics
        
        assert metrics["total_conversations"] == len(sample_conversations)
        assert 0.0 <= metrics["success_rate"] <= 1.0
        assert 0.0 <= metrics["failure_rate"] <= 1.0
        assert 0.0 <= metrics["partial_rate"] <= 1.0
    
    def test_generate_workflow_recommendations(self):
        """Test generating workflow recommendations"""
        analyzer = WorkflowAnalyzer()
        
        success_factors = [
            {"indicator": "完了", "role": "user", "frequency": 5, "success_rate": 0.8}
        ]
        
        blocking_factors = [
            {"indicator": "エラー", "role": "user", "frequency": 3, "failure_rate": 0.7}
        ]
        
        efficiency_metrics = {
            "success_rate": 0.6,
            "average_duration_minutes": 45,
            "short_conversation_success_rate": 0.8,
            "long_conversation_success_rate": 0.5
        }
        
        recommendations = analyzer._generate_workflow_recommendations(
            success_factors, blocking_factors, efficiency_metrics
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)
    
    def test_calculate_confidence(self, sample_conversations):
        """Test calculating confidence score"""
        analyzer = WorkflowAnalyzer()
        
        conversation_analyses = []
        for conv in sample_conversations:
            analysis = analyzer._analyze_conversation(conv)
            conversation_analyses.append(analysis)
        
        confidence = analyzer._calculate_confidence(sample_conversations, conversation_analyses)
        
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0