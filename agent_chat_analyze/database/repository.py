"""Data repository for database operations"""

import uuid
import json
from datetime import datetime
from typing import List, Optional
from .connection import DatabaseManager
from ..models import Conversation, Message, Feedback, AnalysisResult


class Repository:
    """Repository for database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize repository
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
    def insert_conversation(self, conversation: Conversation) -> None:
        """Insert a conversation into the database
        
        Args:
            conversation: Conversation object to insert
        """
        conn = self.db_manager.get_connection()
        conn.execute("""
            INSERT INTO conversations (id, started_at, ended_at, topic, outcome, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            conversation.id,
            conversation.started_at,
            conversation.ended_at,
            conversation.topic,
            conversation.outcome,
            json.dumps({})  # metadata placeholder
        ))
        conn.commit()
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation object or None if not found
        """
        conn = self.db_manager.get_connection()
        result = conn.execute("""
            SELECT id, started_at, ended_at, topic, outcome, metadata
            FROM conversations
            WHERE id = ?
        """, (conversation_id,)).fetchone()
        
        if result is None:
            return None
        
        return Conversation(
            id=result[0],
            messages=[],  # Messages loaded separately
            started_at=result[1],
            ended_at=result[2],
            topic=result[3],
            outcome=result[4]
        )
    
    def insert_message(self, conversation_id: str, message: Message) -> str:
        """Insert a message into the database
        
        Args:
            conversation_id: ID of the conversation
            message: Message object to insert
            
        Returns:
            Generated message ID
        """
        message_id = str(uuid.uuid4())
        conn = self.db_manager.get_connection()
        conn.execute("""
            INSERT INTO messages (id, conversation_id, role, content, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            message_id,
            conversation_id,
            message.role,
            message.content,
            message.timestamp,
            json.dumps(message.metadata)
        ))
        conn.commit()
        return message_id
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """Get a message by ID
        
        Args:
            message_id: Message ID
            
        Returns:
            Message object or None if not found
        """
        conn = self.db_manager.get_connection()
        result = conn.execute("""
            SELECT role, content, timestamp, metadata
            FROM messages
            WHERE id = ?
        """, (message_id,)).fetchone()
        
        if result is None:
            return None
        
        return Message(
            role=result[0],
            content=result[1],
            timestamp=result[2],
            metadata=json.loads(result[3])
        )
    
    def insert_feedback(self, feedback: Feedback) -> str:
        """Insert feedback into the database
        
        Args:
            feedback: Feedback object to insert
            
        Returns:
            Generated feedback ID
        """
        feedback_id = str(uuid.uuid4())
        conn = self.db_manager.get_connection()
        conn.execute("""
            INSERT INTO feedbacks (id, conversation_id, message_id, feedback_type, content, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            feedback_id,
            feedback.conversation_id,
            feedback.message_id,
            feedback.feedback_type,
            feedback.content,
            feedback.timestamp
        ))
        conn.commit()
        return feedback_id
    
    def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """Get feedback by ID
        
        Args:
            feedback_id: Feedback ID
            
        Returns:
            Feedback object or None if not found
        """
        conn = self.db_manager.get_connection()
        result = conn.execute("""
            SELECT conversation_id, message_id, feedback_type, content, timestamp
            FROM feedbacks
            WHERE id = ?
        """, (feedback_id,)).fetchone()
        
        if result is None:
            return None
        
        return Feedback(
            conversation_id=result[0],
            message_id=result[1],
            feedback_type=result[2],
            content=result[3],
            timestamp=result[4]
        )
    
    def insert_analysis_result(self, analysis_result: AnalysisResult) -> str:
        """Insert analysis result into the database
        
        Args:
            analysis_result: AnalysisResult object to insert
            
        Returns:
            Generated analysis result ID
        """
        result_id = str(uuid.uuid4())
        conn = self.db_manager.get_connection()
        conn.execute("""
            INSERT INTO analysis_results (id, conversation_id, analysis_type, findings, recommendations, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            result_id,
            analysis_result.conversation_id,
            analysis_result.analysis_type,
            json.dumps(analysis_result.findings),
            json.dumps(analysis_result.recommendations),
            analysis_result.confidence,
            datetime.now()
        ))
        conn.commit()
        return result_id
    
    def get_analysis_result(self, result_id: str) -> Optional[AnalysisResult]:
        """Get analysis result by ID
        
        Args:
            result_id: Analysis result ID
            
        Returns:
            AnalysisResult object or None if not found
        """
        conn = self.db_manager.get_connection()
        result = conn.execute("""
            SELECT conversation_id, analysis_type, findings, recommendations, confidence
            FROM analysis_results
            WHERE id = ?
        """, (result_id,)).fetchone()
        
        if result is None:
            return None
        
        return AnalysisResult(
            conversation_id=result[0],
            analysis_type=result[1],
            findings=json.loads(result[2]),
            recommendations=json.loads(result[3]),
            confidence=result[4]
        )
    
    def get_conversations_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Conversation]:
        """Get conversations within date range
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of Conversation objects
        """
        conn = self.db_manager.get_connection()
        results = conn.execute("""
            SELECT id, started_at, ended_at, topic, outcome, metadata
            FROM conversations
            WHERE started_at >= ? AND started_at <= ?
            ORDER BY started_at
        """, (start_date, end_date)).fetchall()
        
        conversations = []
        for result in results:
            conversations.append(Conversation(
                id=result[0],
                messages=[],  # Messages loaded separately
                started_at=result[1],
                ended_at=result[2],
                topic=result[3],
                outcome=result[4]
            ))
        
        return conversations
    
    def get_feedbacks_by_type(self, feedback_type: str) -> List[Feedback]:
        """Get feedbacks by type
        
        Args:
            feedback_type: Type of feedback to filter by
            
        Returns:
            List of Feedback objects
        """
        conn = self.db_manager.get_connection()
        results = conn.execute("""
            SELECT conversation_id, message_id, feedback_type, content, timestamp
            FROM feedbacks
            WHERE feedback_type = ?
            ORDER BY timestamp
        """, (feedback_type,)).fetchall()
        
        feedbacks = []
        for result in results:
            feedbacks.append(Feedback(
                conversation_id=result[0],
                message_id=result[1],
                feedback_type=result[2],
                content=result[3],
                timestamp=result[4]
            ))
        
        return feedbacks