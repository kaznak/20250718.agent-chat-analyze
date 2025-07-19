"""Tests for data models"""

import pytest
from datetime import datetime
from agent_chat_analyze.models import Conversation, Message, Feedback, AnalysisResult


class TestMessage:
    """Test Message model"""
    
    def test_message_creation(self):
        """Test basic message creation"""
        timestamp = datetime.now()
        message = Message(
            role="user",
            content="Hello, how are you?",
            timestamp=timestamp,
            metadata={"source": "test"}
        )
        
        assert message.role == "user"
        assert message.content == "Hello, how are you?"
        assert message.timestamp == timestamp
        assert message.metadata == {"source": "test"}
    
    def test_message_roles(self):
        """Test different message roles"""
        timestamp = datetime.now()
        
        user_message = Message(
            role="user",
            content="User message",
            timestamp=timestamp,
            metadata={}
        )
        
        assistant_message = Message(
            role="assistant",
            content="Assistant message",
            timestamp=timestamp,
            metadata={}
        )
        
        system_message = Message(
            role="system",
            content="System message",
            timestamp=timestamp,
            metadata={}
        )
        
        assert user_message.role == "user"
        assert assistant_message.role == "assistant"
        assert system_message.role == "system"


class TestConversation:
    """Test Conversation model"""
    
    def test_conversation_creation(self):
        """Test basic conversation creation"""
        started_at = datetime.now()
        ended_at = datetime.now()
        
        conversation = Conversation(
            id="conv_001",
            messages=[],
            started_at=started_at,
            ended_at=ended_at,
            topic="Test conversation",
            outcome="success"
        )
        
        assert conversation.id == "conv_001"
        assert conversation.messages == []
        assert conversation.started_at == started_at
        assert conversation.ended_at == ended_at
        assert conversation.topic == "Test conversation"
        assert conversation.outcome == "success"
    
    def test_conversation_with_messages(self):
        """Test conversation with messages"""
        timestamp = datetime.now()
        message = Message(
            role="user",
            content="Hello",
            timestamp=timestamp,
            metadata={}
        )
        
        conversation = Conversation(
            id="conv_002",
            messages=[message],
            started_at=timestamp,
            ended_at=timestamp,
            topic="Test with message",
            outcome="success"
        )
        
        assert len(conversation.messages) == 1
        assert conversation.messages[0].content == "Hello"


class TestFeedback:
    """Test Feedback model"""
    
    def test_feedback_creation(self):
        """Test basic feedback creation"""
        timestamp = datetime.now()
        feedback = Feedback(
            conversation_id="conv_001",
            message_id="msg_001",
            feedback_type="positive",
            content="Great response!",
            timestamp=timestamp
        )
        
        assert feedback.conversation_id == "conv_001"
        assert feedback.message_id == "msg_001"
        assert feedback.feedback_type == "positive"
        assert feedback.content == "Great response!"
        assert feedback.timestamp == timestamp
    
    def test_feedback_types(self):
        """Test different feedback types"""
        timestamp = datetime.now()
        
        positive_feedback = Feedback(
            conversation_id="conv_001",
            message_id="msg_001",
            feedback_type="positive",
            content="Good",
            timestamp=timestamp
        )
        
        negative_feedback = Feedback(
            conversation_id="conv_001",
            message_id="msg_002",
            feedback_type="negative",
            content="Bad",
            timestamp=timestamp
        )
        
        request_feedback = Feedback(
            conversation_id="conv_001",
            message_id="msg_003",
            feedback_type="request",
            content="Please improve",
            timestamp=timestamp
        )
        
        assert positive_feedback.feedback_type == "positive"
        assert negative_feedback.feedback_type == "negative"
        assert request_feedback.feedback_type == "request"


class TestAnalysisResult:
    """Test AnalysisResult model"""
    
    def test_analysis_result_creation(self):
        """Test basic analysis result creation"""
        analysis_result = AnalysisResult(
            conversation_id="conv_001",
            analysis_type="feedback",
            findings=[{"pattern": "positive_trend", "count": 5}],
            recommendations=["Continue current approach"],
            confidence=0.85
        )
        
        assert analysis_result.conversation_id == "conv_001"
        assert analysis_result.analysis_type == "feedback"
        assert len(analysis_result.findings) == 1
        assert analysis_result.findings[0]["pattern"] == "positive_trend"
        assert len(analysis_result.recommendations) == 1
        assert analysis_result.confidence == 0.85
    
    def test_analysis_types(self):
        """Test different analysis types"""
        feedback_analysis = AnalysisResult(
            conversation_id="conv_001",
            analysis_type="feedback",
            findings=[],
            recommendations=[],
            confidence=0.8
        )
        
        workflow_analysis = AnalysisResult(
            conversation_id="conv_001",
            analysis_type="workflow",
            findings=[],
            recommendations=[],
            confidence=0.9
        )
        
        assert feedback_analysis.analysis_type == "feedback"
        assert workflow_analysis.analysis_type == "workflow"