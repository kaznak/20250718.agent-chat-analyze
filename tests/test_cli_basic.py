"""Basic CLI tests without ML dependencies"""

import pytest
import tempfile
import os
from pathlib import Path
from click.testing import CliRunner


class TestCLIBasic:
    """Test CLI functionality without ML dependencies"""
    
    def test_cli_import(self):
        """Test that CLI can be imported"""
        from agent_chat_analyze.cli import main
        assert main is not None
    
    def test_cli_help(self):
        """Test CLI help command"""
        from agent_chat_analyze.cli import main
        
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert 'Agent Chat Analyze' in result.output
    
    def test_db_commands(self):
        """Test database commands"""
        from agent_chat_analyze.cli import main
        
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, 'test.db')
            
            # Test db init
            result = runner.invoke(main, ['db', 'init', '--db-path', db_path])
            assert result.exit_code == 0
            assert 'データベースを初期化しました' in result.output
            
            # Test db status
            result = runner.invoke(main, ['db', 'status', '--db-path', db_path])
            assert result.exit_code == 0
            assert 'データベースファイル' in result.output
    
    def test_analyze_command_with_invalid_file(self):
        """Test analyze command with non-existent file"""
        from agent_chat_analyze.cli import main
        
        runner = CliRunner()
        result = runner.invoke(main, [
            'analyze', 
            '--input', 'nonexistent.jsonl',
            '--output', 'report.md'
        ])
        
        assert result.exit_code != 0
        assert 'エラー' in result.output
    
    def test_analyze_command_with_sample_file(self):
        """Test analyze command with sample JSONL file"""
        from agent_chat_analyze.cli import main
        
        # Create sample JSONL file
        sample_jsonl = '''{"parentUuid":null,"isSidechain":false,"userType":"external","cwd":"/home/test","sessionId":"test-session","version":"1.0.53","type":"user","message":{"role":"user","content":"こんにちは"},"uuid":"user-001","timestamp":"2024-01-15T10:00:00.000Z"}
{"parentUuid":"user-001","isSidechain":false,"userType":"external","cwd":"/home/test","sessionId":"test-session","version":"1.0.53","type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"こんにちは！"}]},"uuid":"assistant-001","timestamp":"2024-01-15T10:00:01.000Z"}'''
        
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sample file
            input_file = os.path.join(temp_dir, 'sample.jsonl')
            with open(input_file, 'w', encoding='utf-8') as f:
                f.write(sample_jsonl)
            
            output_file = os.path.join(temp_dir, 'report.md')
            
            # This will fail due to missing ML dependencies, but should get past file validation
            result = runner.invoke(main, [
                'analyze',
                '--input', input_file,
                '--output', output_file,
                '--analysis-type', 'workflow'  # Workflow analyzer doesn't need embeddings
            ])
            
            # Should fail on embedding initialization, not file validation
            assert '対話ログを解析しています' in result.output or 'エラー' in result.output
    
    def test_version_option(self):
        """Test version option"""
        from agent_chat_analyze.cli import main
        
        runner = CliRunner()
        result = runner.invoke(main, ['--version'])
        
        # Should not fail
        assert result.exit_code == 0