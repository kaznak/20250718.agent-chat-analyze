"""Tests for database operations"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime
from agent_chat_analyze.database import DatabaseManager, Repository
from agent_chat_analyze.models import Conversation, Message, Feedback, AnalysisResult


class TestDatabaseManager:
    """Test DatabaseManager class"""
    
    def test_database_manager_creation(self):
        """Test database manager creation with in-memory database"""
        db_manager = DatabaseManager(":memory:")
        assert db_manager.db_path == ":memory:"
        assert db_manager.connection is None
    
    def test_database_connection(self):
        """Test database connection"""
        db_manager = DatabaseManager(":memory:")
        conn = db_manager.get_connection()
        assert conn is not None
        
        # Test connection reuse
        conn2 = db_manager.get_connection()
        assert conn is conn2
    
    def test_database_initialization(self):
        """Test database schema initialization"""
        db_manager = DatabaseManager(":memory:")
        db_manager.initialize_database()
        
        conn = db_manager.get_connection()
        # Check if tables exist
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [table[0] for table in tables]
        
        assert 'conversations' in table_names
        assert 'messages' in table_names
        assert 'feedbacks' in table_names
        assert 'analysis_results' in table_names
    
    def test_database_close(self):
        """Test database connection close"""
        db_manager = DatabaseManager(":memory:")
        conn = db_manager.get_connection()
        assert conn is not None
        
        db_manager.close()
        assert db_manager.connection is None
    
    def test_database_context_manager(self):
        """Test database manager as context manager"""
        with DatabaseManager(":memory:") as db_manager:
            conn = db_manager.get_connection()
            assert conn is not None
        
        # Connection should be closed after context
        assert db_manager.connection is None


class TestRepository:
    """Test Repository class"""
    
    @pytest.fixture
    def repository(self):
        """Create repository with in-memory database"""
        db_manager = DatabaseManager(":memory:")
        db_manager.initialize_database()
        return Repository(db_manager)
    
    def test_repository_creation(self, repository):
        """Test repository creation"""
        assert repository.db_manager is not None
    
    def test_insert_conversation(self, repository):
        """Test inserting a conversation"""
        conversation = Conversation(
            id="conv_001",
            messages=[],
            started_at=datetime.now(),
            ended_at=datetime.now(),
            topic="Test conversation",
            outcome="success"
        )
        
        repository.insert_conversation(conversation)
        
        # Verify insertion
        saved_conversation = repository.get_conversation("conv_001")
        assert saved_conversation is not None
        assert saved_conversation.id == "conv_001"
        assert saved_conversation.topic == "Test conversation"
        assert saved_conversation.outcome == "success"
    
    def test_insert_message(self, repository):
        """Test inserting a message"""
        # First insert conversation
        conversation = Conversation(
            id="conv_001",
            messages=[],
            started_at=datetime.now(),
            ended_at=datetime.now(),
            topic="Test conversation",
            outcome="success"
        )
        repository.insert_conversation(conversation)
        
        # Insert message
        message = Message(
            role="user",
            content="Hello, world!",
            timestamp=datetime.now(),
            metadata={"source": "test"}
        )
        
        message_id = repository.insert_message("conv_001", message)
        assert message_id is not None
        
        # Verify insertion
        saved_message = repository.get_message(message_id)
        assert saved_message is not None
        assert saved_message.role == "user"
        assert saved_message.content == "Hello, world!"
    
    def test_insert_feedback(self, repository):
        """Test inserting feedback"""
        # Setup conversation and message
        conversation = Conversation(
            id="conv_001",
            messages=[],
            started_at=datetime.now(),
            ended_at=datetime.now(),
            topic="Test conversation",
            outcome="success"
        )
        repository.insert_conversation(conversation)
        
        message = Message(
            role="user",
            content="Hello",
            timestamp=datetime.now(),
            metadata={}
        )
        message_id = repository.insert_message("conv_001", message)
        
        # Insert feedback
        feedback = Feedback(
            conversation_id="conv_001",
            message_id=message_id,
            feedback_type="positive",
            content="Great response!",
            timestamp=datetime.now()
        )
        
        feedback_id = repository.insert_feedback(feedback)
        assert feedback_id is not None
        
        # Verify insertion
        saved_feedback = repository.get_feedback(feedback_id)
        assert saved_feedback is not None
        assert saved_feedback.feedback_type == "positive"
        assert saved_feedback.content == "Great response!"
    
    def test_insert_analysis_result(self, repository):
        """Test inserting analysis result"""
        # Setup conversation
        conversation = Conversation(
            id="conv_001",
            messages=[],
            started_at=datetime.now(),
            ended_at=datetime.now(),
            topic="Test conversation",
            outcome="success"
        )
        repository.insert_conversation(conversation)
        
        # Insert analysis result
        analysis_result = AnalysisResult(
            conversation_id="conv_001",
            analysis_type="feedback",
            findings=[{"pattern": "positive_trend", "count": 5}],
            recommendations=["Continue current approach"],
            confidence=0.85
        )
        
        result_id = repository.insert_analysis_result(analysis_result)
        assert result_id is not None
        
        # Verify insertion
        saved_result = repository.get_analysis_result(result_id)
        assert saved_result is not None
        assert saved_result.analysis_type == "feedback"
        assert len(saved_result.findings) == 1
        assert abs(saved_result.confidence - 0.85) < 0.001
    
    def test_get_conversations_by_date_range(self, repository):
        """Test getting conversations by date range"""
        # Insert test conversations
        date1 = datetime(2024, 1, 1, 10, 0, 0)
        date2 = datetime(2024, 1, 2, 10, 0, 0)
        date3 = datetime(2024, 1, 3, 10, 0, 0)
        
        conversations = [
            Conversation(
                id="conv_001",
                messages=[],
                started_at=date1,
                ended_at=date1,
                topic="First conversation",
                outcome="success"
            ),
            Conversation(
                id="conv_002",
                messages=[],
                started_at=date2,
                ended_at=date2,
                topic="Second conversation",
                outcome="success"
            ),
            Conversation(
                id="conv_003",
                messages=[],
                started_at=date3,
                ended_at=date3,
                topic="Third conversation",
                outcome="success"
            )
        ]
        
        for conv in conversations:
            repository.insert_conversation(conv)
        
        # Test date range query
        results = repository.get_conversations_by_date_range(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2, 23, 59, 59)
        )
        
        assert len(results) == 2
        assert results[0].id in ["conv_001", "conv_002"]
        assert results[1].id in ["conv_001", "conv_002"]
    
    def test_get_feedbacks_by_type(self, repository):
        """Test getting feedbacks by type"""
        # Setup conversation and message
        conversation = Conversation(
            id="conv_001",
            messages=[],
            started_at=datetime.now(),
            ended_at=datetime.now(),
            topic="Test conversation",
            outcome="success"
        )
        repository.insert_conversation(conversation)
        
        message = Message(
            role="user",
            content="Hello",
            timestamp=datetime.now(),
            metadata={}
        )
        message_id = repository.insert_message("conv_001", message)
        
        # Insert different types of feedback
        feedbacks = [
            Feedback("conv_001", message_id, "positive", "Good", datetime.now()),
            Feedback("conv_001", message_id, "negative", "Bad", datetime.now()),
            Feedback("conv_001", message_id, "positive", "Great", datetime.now())
        ]
        
        for feedback in feedbacks:
            repository.insert_feedback(feedback)
        
        # Test filtering by type
        positive_feedbacks = repository.get_feedbacks_by_type("positive")
        assert len(positive_feedbacks) == 2
        
        negative_feedbacks = repository.get_feedbacks_by_type("negative")
        assert len(negative_feedbacks) == 1