"""Claude Code log parser"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from .base import BaseParser
from ..models import Conversation, Message, Feedback


class ClaudeCodeParser(BaseParser):
    """Parser for Claude Code JSONL format logs"""
    
    def __init__(self):
        """Initialize parser with patterns"""
        # Feedback patterns
        self.positive_patterns = [
            r'素晴らしい|完璧|良い|ありがとう|感謝|最高|優秀|すごい|見事|申し分ない',
            r'great|excellent|perfect|amazing|wonderful|fantastic|outstanding|brilliant'
        ]
        
        self.negative_patterns = [
            r'不十分|足りない|だめ|悪い|間違|エラー|問題|困る|役に立たない|役に立ちません|使えない',
            r'insufficient|inadequate|bad|wrong|error|problem|useless|not helpful'
        ]
        
        self.request_patterns = [
            r'してください|お願い|欲しい|したい|必要|追加|修正|改善|変更',
            r'please|want|need|would like|could you|can you|add|modify|improve|change'
        ]
    
    def validate_format(self, file_path: Path) -> bool:
        """Validate if file is Claude Code JSONL format
        
        Args:
            file_path: Path to the log file
            
        Returns:
            True if file format is valid, False otherwise
        """
        try:
            if not file_path.exists():
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                # Try to parse first few lines as JSON
                for i, line in enumerate(f):
                    if i >= 3:  # Check first 3 lines
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        entry = json.loads(line)
                        # Check required fields
                        if not all(key in entry for key in ['sessionId', 'type', 'message', 'uuid', 'timestamp']):
                            return False
                        
                        # Check message structure
                        if 'role' not in entry['message']:
                            return False
                            
                    except json.JSONDecodeError:
                        return False
            
            return True
            
        except Exception:
            return False
    
    def parse(self, file_path: Path) -> List[Conversation]:
        """Parse Claude Code JSONL log file
        
        Args:
            file_path: Path to the log file
            
        Returns:
            List of Conversation objects
        """
        if not self.validate_format(file_path):
            raise ValueError(f"Invalid file format: {file_path}")
        
        # Read all JSON entries
        entries = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
        
        # Group entries by sessionId
        sessions = {}
        for entry in entries:
            session_id = entry.get('sessionId')
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(entry)
        
        # Convert each session to a Conversation
        conversations = []
        for session_id, session_entries in sessions.items():
            # Sort by timestamp
            session_entries.sort(key=lambda x: x.get('timestamp', ''))
            
            messages = []
            for entry in session_entries:
                message = self._parse_message_entry(entry)
                if message:
                    messages.append(message)
            
            if not messages:
                continue
            
            conversation = Conversation(
                id=session_id,
                messages=messages,
                started_at=messages[0].timestamp if messages else datetime.now(),
                ended_at=messages[-1].timestamp if messages else datetime.now(),
                topic=self._generate_conversation_topic(messages),
                outcome=self._determine_conversation_outcome(messages)
            )
            
            conversations.append(conversation)
        
        return conversations
    
    def _parse_message_entry(self, entry: Dict[str, Any]) -> Optional[Message]:
        """Parse a single message entry from JSONL
        
        Args:
            entry: JSON entry from log file
            
        Returns:
            Message object or None if parsing fails
        """
        try:
            message_data = entry.get('message', {})
            role = message_data.get('role')
            
            if role not in ['user', 'assistant']:
                return None
            
            # Extract content based on role
            if role == 'user':
                content = message_data.get('content', '')
            else:  # assistant
                content_list = message_data.get('content', [])
                if isinstance(content_list, list):
                    # Extract text from content array
                    text_parts = []
                    for item in content_list:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            text_parts.append(item.get('text', ''))
                    content = '\n'.join(text_parts)
                else:
                    content = str(content_list)
            
            # Parse timestamp
            timestamp_str = entry.get('timestamp', '')
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError:
                timestamp = datetime.now()
            
            return Message(
                role=role,
                content=content,
                timestamp=timestamp,
                metadata={
                    'uuid': entry.get('uuid'),
                    'parentUuid': entry.get('parentUuid'),
                    'cwd': entry.get('cwd'),
                    'version': entry.get('version')
                }
            )
            
        except Exception:
            return None
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp from ISO format string
        
        Args:
            timestamp_str: ISO timestamp string
            
        Returns:
            Datetime object or None if parsing fails
        """
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except Exception:
            return None
    
    
    def _extract_feedback(self, message_content: str) -> List[Feedback]:
        """Extract feedback from message content
        
        Args:
            message_content: Message content to analyze
            
        Returns:
            List of Feedback objects
        """
        feedbacks = []
        
        # Check for positive feedback
        for pattern in self.positive_patterns:
            if re.search(pattern, message_content, re.IGNORECASE):
                feedback = Feedback(
                    conversation_id="",  # Will be set later
                    message_id="",       # Will be set later
                    feedback_type="positive",
                    content=message_content,
                    timestamp=datetime.now()
                )
                feedbacks.append(feedback)
                break
        
        # Check for negative feedback
        for pattern in self.negative_patterns:
            if re.search(pattern, message_content, re.IGNORECASE):
                feedback = Feedback(
                    conversation_id="",  # Will be set later
                    message_id="",       # Will be set later
                    feedback_type="negative",
                    content=message_content,
                    timestamp=datetime.now()
                )
                feedbacks.append(feedback)
                break
        
        # Check for request feedback
        for pattern in self.request_patterns:
            if re.search(pattern, message_content, re.IGNORECASE):
                feedback = Feedback(
                    conversation_id="",  # Will be set later
                    message_id="",       # Will be set later
                    feedback_type="request",
                    content=message_content,
                    timestamp=datetime.now()
                )
                feedbacks.append(feedback)
                break
        
        return feedbacks
    
    def _determine_conversation_outcome(self, messages: List[Message]) -> str:
        """Determine conversation outcome based on messages
        
        Args:
            messages: List of messages in the conversation
            
        Returns:
            Outcome string: "success", "partial", or "failure"
        """
        if not messages:
            return "failure"
        
        # Get last few user messages for analysis
        user_messages = [m for m in messages if m.role == "user"]
        if not user_messages:
            return "partial"
        
        last_user_messages = user_messages[-2:] if len(user_messages) >= 2 else user_messages
        
        positive_count = 0
        negative_count = 0
        
        for message in last_user_messages:
            content = message.content
            
            # Check positive patterns
            for pattern in self.positive_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    positive_count += 1
                    break
            
            # Check negative patterns
            for pattern in self.negative_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    negative_count += 1
                    break
        
        if positive_count > negative_count:
            return "success"
        elif negative_count > positive_count:
            return "failure"
        else:
            return "partial"
    
    def _generate_conversation_topic(self, messages: List[Message]) -> Optional[str]:
        """Generate conversation topic based on messages
        
        Args:
            messages: List of messages in the conversation
            
        Returns:
            Topic string or None
        """
        if not messages:
            return None
        
        # Use first user message to determine topic
        user_messages = [m for m in messages if m.role == "user"]
        if not user_messages:
            return None
        
        first_message = user_messages[0].content
        
        # Extract key terms (simplified topic generation)
        topic_keywords = []
        
        # Japanese keywords
        ja_keywords = [
            'プロジェクト', 'データ分析', 'Python', 'テスト', 'コード', 'アプリケーション',
            '開発', 'システム', 'ツール', 'プログラム', 'ウェブ', 'API', 'データベース'
        ]
        
        # English keywords
        en_keywords = [
            'project', 'data analysis', 'python', 'test', 'code', 'application',
            'development', 'system', 'tool', 'program', 'web', 'api', 'database'
        ]
        
        for keyword in ja_keywords + en_keywords:
            if keyword.lower() in first_message.lower():
                topic_keywords.append(keyword)
        
        if topic_keywords:
            return " / ".join(topic_keywords[:3])  # Limit to 3 keywords
        
        # Fallback: use first 50 characters of first message
        return first_message[:50] + "..." if len(first_message) > 50 else first_message