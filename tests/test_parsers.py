"""Tests for log parsers"""

import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path
from agent_chat_analyze.parsers import BaseParser, ClaudeCodeParser
from agent_chat_analyze.models import Conversation, Message, Feedback


class TestBaseParser:
    """Test BaseParser abstract class"""
    
    def test_base_parser_is_abstract(self):
        """Test that BaseParser cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseParser()


class TestClaudeCodeParser:
    """Test ClaudeCodeParser class"""
    
    @pytest.fixture
    def parser(self):
        """Create ClaudeCodeParser instance"""
        return ClaudeCodeParser()
    
    @pytest.fixture
    def sample_claude_code_log(self):
        """Create sample Claude Code log file in JSONL format"""
        log_content = """{"parentUuid":null,"isSidechain":false,"userType":"external","cwd":"/home/test/project","sessionId":"test-session-001","version":"1.0.53","type":"user","message":{"role":"user","content":"こんにちは。新しいプロジェクトを作成したいです。"},"uuid":"user-msg-001","timestamp":"2024-01-15T10:00:00.000Z"}
{"parentUuid":"user-msg-001","isSidechain":false,"userType":"external","cwd":"/home/test/project","sessionId":"test-session-001","version":"1.0.53","type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"こんにちは！新しいプロジェクトの作成をお手伝いします。どのようなプロジェクトを作成したいですか？"}]},"uuid":"assistant-msg-001","timestamp":"2024-01-15T10:00:01.000Z"}
{"parentUuid":"assistant-msg-001","isSidechain":false,"userType":"external","cwd":"/home/test/project","sessionId":"test-session-001","version":"1.0.53","type":"user","message":{"role":"user","content":"Pythonでデータ分析ツールを作りたいです。"},"uuid":"user-msg-002","timestamp":"2024-01-15T10:00:02.000Z"}
{"parentUuid":"user-msg-002","isSidechain":false,"userType":"external","cwd":"/home/test/project","sessionId":"test-session-001","version":"1.0.53","type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"Pythonでデータ分析ツールを作成しましょう。まずプロジェクトの基本構造を作成します。\\n\\n```python\\n# data_analyzer.py\\nimport pandas as pd\\nimport numpy as np\\n\\nclass DataAnalyzer:\\n    def __init__(self, data_file):\\n        self.data = pd.read_csv(data_file)\\n    \\n    def analyze(self):\\n        return self.data.describe()\\n```\\n\\nこのコードでデータ分析の基本機能を実装できます。"}]},"uuid":"assistant-msg-002","timestamp":"2024-01-15T10:00:03.000Z"}
{"parentUuid":"assistant-msg-002","isSidechain":false,"userType":"external","cwd":"/home/test/project","sessionId":"test-session-001","version":"1.0.53","type":"user","message":{"role":"user","content":"素晴らしい！このコードは完璧です。ありがとうございます。"},"uuid":"user-msg-003","timestamp":"2024-01-15T10:00:04.000Z"}
{"parentUuid":"user-msg-003","isSidechain":false,"userType":"external","cwd":"/home/test/project","sessionId":"test-session-002","version":"1.0.53","type":"user","message":{"role":"user","content":"今度はテストを追加したいです。"},"uuid":"user-msg-004","timestamp":"2024-01-15T11:00:00.000Z"}
{"parentUuid":"user-msg-004","isSidechain":false,"userType":"external","cwd":"/home/test/project","sessionId":"test-session-002","version":"1.0.53","type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"テストを追加しましょう。pytestを使用してテストを作成します。\\n\\n```python\\n# test_data_analyzer.py\\nimport pytest\\nfrom data_analyzer import DataAnalyzer\\n\\ndef test_data_analyzer_creation():\\n    analyzer = DataAnalyzer(\\"test_data.csv\\")\\n    assert analyzer is not None\\n```"}]},"uuid":"assistant-msg-003","timestamp":"2024-01-15T11:00:01.000Z"}
{"parentUuid":"assistant-msg-003","isSidechain":false,"userType":"external","cwd":"/home/test/project","sessionId":"test-session-002","version":"1.0.53","type":"user","message":{"role":"user","content":"このテストでは不十分です。もっと包括的なテストが必要です。"},"uuid":"user-msg-005","timestamp":"2024-01-15T11:00:02.000Z"}
{"parentUuid":"user-msg-005","isSidechain":false,"userType":"external","cwd":"/home/test/project","sessionId":"test-session-002","version":"1.0.53","type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"おっしゃる通りです。より包括的なテストを作成しましょう。\\n\\n```python\\n# test_data_analyzer.py\\nimport pytest\\nimport pandas as pd\\nfrom data_analyzer import DataAnalyzer\\n\\nclass TestDataAnalyzer:\\n    def test_initialization(self):\\n        analyzer = DataAnalyzer(\\"test_data.csv\\")\\n        assert analyzer.data is not None\\n    \\n    def test_analyze_method(self):\\n        analyzer = DataAnalyzer(\\"test_data.csv\\")\\n        result = analyzer.analyze()\\n        assert isinstance(result, pd.DataFrame)\\n```"}]},"uuid":"assistant-msg-004","timestamp":"2024-01-15T11:00:03.000Z"}
{"parentUuid":"assistant-msg-004","isSidechain":false,"userType":"external","cwd":"/home/test/project","sessionId":"test-session-002","version":"1.0.53","type":"user","message":{"role":"user","content":"完璧です。ありがとうございました。"},"uuid":"user-msg-006","timestamp":"2024-01-15T11:00:04.000Z"}
"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(log_content)
            return f.name
    
    def test_parser_creation(self, parser):
        """Test parser creation"""
        assert parser is not None
        assert isinstance(parser, ClaudeCodeParser)
    
    def test_validate_format_valid_file(self, parser, sample_claude_code_log):
        """Test format validation for valid Claude Code log"""
        result = parser.validate_format(Path(sample_claude_code_log))
        assert result is True
        
        # Cleanup
        os.unlink(sample_claude_code_log)
    
    def test_validate_format_invalid_file(self, parser):
        """Test format validation for invalid file"""
        # Create invalid file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write("This is not a valid JSONL file")
            invalid_file = f.name
        
        result = parser.validate_format(Path(invalid_file))
        assert result is False
        
        # Cleanup
        os.unlink(invalid_file)
    
    def test_validate_format_nonexistent_file(self, parser):
        """Test format validation for nonexistent file"""
        result = parser.validate_format(Path("nonexistent_file.md"))
        assert result is False
    
    def test_parse_conversations(self, parser, sample_claude_code_log):
        """Test parsing conversations from Claude Code log"""
        conversations = parser.parse(Path(sample_claude_code_log))
        
        assert len(conversations) == 2
        
        # Test first conversation (session test-session-001)
        conv1 = conversations[0]
        assert conv1.id == "test-session-001"
        assert len(conv1.messages) == 5  # 3 user + 2 assistant messages
        assert conv1.started_at is not None
        assert conv1.ended_at is not None
        
        # Test message content
        assert conv1.messages[0].role == "user"
        assert "こんにちは" in conv1.messages[0].content
        assert conv1.messages[1].role == "assistant"
        assert "新しいプロジェクトの作成" in conv1.messages[1].content
        
        # Test second conversation (session test-session-002)
        conv2 = conversations[1]
        assert conv2.id == "test-session-002"
        assert len(conv2.messages) == 5  # 3 user + 2 assistant messages
        
        # Cleanup
        os.unlink(sample_claude_code_log)
    
    def test_extract_feedback_positive(self, parser):
        """Test extracting positive feedback"""
        message_content = "素晴らしい！このコードは完璧です。ありがとうございます。"
        feedbacks = parser._extract_feedback(message_content)
        
        assert len(feedbacks) >= 1
        # Should contain positive feedback
        positive_feedback = [f for f in feedbacks if f.feedback_type == "positive"]
        assert len(positive_feedback) >= 1
        assert "素晴らしい" in positive_feedback[0].content
    
    def test_extract_feedback_negative(self, parser):
        """Test extracting negative feedback"""
        message_content = "このテストでは不十分です。もっと包括的なテストが必要です。"
        feedbacks = parser._extract_feedback(message_content)
        
        assert len(feedbacks) >= 1
        # Should contain negative feedback
        negative_feedback = [f for f in feedbacks if f.feedback_type == "negative"]
        assert len(negative_feedback) >= 1
        assert "不十分" in negative_feedback[0].content
    
    def test_extract_feedback_request(self, parser):
        """Test extracting request feedback"""
        message_content = "テストを追加したいです。もっと詳細な説明をお願いします。"
        feedbacks = parser._extract_feedback(message_content)
        
        assert len(feedbacks) >= 1
        # Should contain request feedback
        request_feedback = [f for f in feedbacks if f.feedback_type == "request"]
        assert len(request_feedback) >= 1
        assert "追加したい" in request_feedback[0].content or "お願いします" in request_feedback[0].content
    
    def test_extract_feedback_neutral(self, parser):
        """Test extracting neutral message (no feedback)"""
        message_content = "データ分析ツールを作成する方法について教えてください。"
        feedbacks = parser._extract_feedback(message_content)
        
        # Should not extract any feedback from neutral message
        assert len(feedbacks) == 0
    
    def test_parse_timestamp(self, parser):
        """Test parsing timestamp from log"""
        timestamp_str = "### 2024-01-15 10:00:00"
        result = parser._parse_timestamp(timestamp_str)
        
        assert result == datetime(2024, 1, 15, 10, 0, 0)
    
    def test_parse_invalid_timestamp(self, parser):
        """Test parsing invalid timestamp"""
        timestamp_str = "### Invalid timestamp"
        result = parser._parse_timestamp(timestamp_str)
        
        assert result is None
    
    def test_determine_conversation_outcome(self, parser):
        """Test determining conversation outcome"""
        # Success case
        messages = [
            Message("user", "データを分析してください", datetime.now(), {}),
            Message("assistant", "解決方法を提案します", datetime.now(), {}),
            Message("user", "完璧です！ありがとうございます", datetime.now(), {})
        ]
        outcome = parser._determine_conversation_outcome(messages)
        assert outcome == "success"
        
        # Partial success case
        messages = [
            Message("user", "データを分析してください", datetime.now(), {}),
            Message("assistant", "分析結果を提示します", datetime.now(), {}),
            Message("user", "普通の結果ですね", datetime.now(), {})
        ]
        outcome = parser._determine_conversation_outcome(messages)
        assert outcome == "partial"
        
        # Failure case
        messages = [
            Message("user", "データを分析してください", datetime.now(), {}),
            Message("assistant", "分析結果を提示します", datetime.now(), {}),
            Message("user", "これは全く役に立ちません", datetime.now(), {})
        ]
        outcome = parser._determine_conversation_outcome(messages)
        assert outcome == "failure"
    
    def test_generate_conversation_topic(self, parser):
        """Test generating conversation topic"""
        messages = [
            Message("user", "Pythonでデータ分析ツールを作りたいです", datetime.now(), {}),
            Message("assistant", "データ分析ツールを作成しましょう", datetime.now(), {}),
            Message("user", "テストを追加したいです", datetime.now(), {})
        ]
        topic = parser._generate_conversation_topic(messages)
        assert topic is not None
        assert "データ分析" in topic or "Python" in topic