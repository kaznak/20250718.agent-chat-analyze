#!/usr/bin/env python3
"""
Agent Chat Analyze 使用例

このスクリプトは、Agent Chat Analyzeツールの基本的な使い方を示します。
"""

import os
from pathlib import Path
from agent_chat_analyze.database import DatabaseManager
from agent_chat_analyze.parsers import ClaudeCodeParser
from agent_chat_analyze.embeddings import SentenceTransformerEmbedding
from agent_chat_analyze.analyzers import FeedbackAnalyzer, WorkflowAnalyzer
from agent_chat_analyze.reporters import MarkdownReporter


def main():
    print("🤖 Agent Chat Analyze 使用例")
    print()
    
    # 1. Claude Codeログファイルのパスを指定
    claude_log_path = input("Claude Code JSONLログファイルのパスを入力してください: ").strip()
    
    if not claude_log_path:
        # デフォルトパス例
        home_dir = Path.home()
        claude_dir = home_dir / ".claude" / "projects"
        print(f"\nClaude Codeプロジェクトディレクトリ: {claude_dir}")
        
        if claude_dir.exists():
            projects = [d for d in claude_dir.iterdir() if d.is_dir()]
            if projects:
                print("\n利用可能なプロジェクト:")
                for i, project in enumerate(projects):
                    print(f"  {project.name}")
                    session_files = list(project.glob("*.jsonl"))
                    for session_file in session_files[:3]:  # 最初の3つだけ表示
                        print(f"    └── {session_file.name}")
        
        print("\nClaude Codeのログファイルは通常以下の場所にあります:")
        print(f"  {home_dir}/.claude/projects/[プロジェクト名]/[セッションID].jsonl")
        return
    
    log_file = Path(claude_log_path)
    if not log_file.exists():
        print(f"❌ ファイルが見つかりません: {claude_log_path}")
        return
    
    print(f"✅ ログファイルを確認しました: {log_file}")
    print()
    
    try:
        # 2. データベース初期化
        print("📁 データベースを初期化しています...")
        db_manager = DatabaseManager("example_analysis.db")
        db_manager.initialize()
        print("✅ データベース初期化完了")
        
        # 3. ログファイルの解析
        print("📖 Claude Codeログを解析しています...")
        parser = ClaudeCodeParser()
        conversations = parser.parse(log_file)
        print(f"✅ {len(conversations)}個の対話を解析しました")
        
        if not conversations:
            print("❌ 対話が見つかりませんでした。ファイル形式を確認してください。")
            return
        
        # 4. 埋め込みモデルの初期化
        print("🧠 埋め込みモデルを読み込んでいます...")
        print("   (初回実行時はモデルのダウンロードが必要です)")
        embedding_model = SentenceTransformerEmbedding()
        print("✅ 埋め込みモデル準備完了")
        
        # 5. ベクトル埋め込みの生成
        print("🔢 ベクトル埋め込みを生成しています...")
        total_user_messages = 0
        for conversation in conversations:
            for message in conversation.messages:
                if message.role == "user":
                    if not message.embedding:
                        message.embedding = embedding_model.encode_single(message.content)
                        total_user_messages += 1
        
        print(f"✅ {total_user_messages}個のユーザーメッセージの埋め込みを生成しました")
        
        # 6. フィードバック分析
        print("💬 フィードバック分析を実行しています...")
        feedback_analyzer = FeedbackAnalyzer(embedding_model)
        feedback_result = feedback_analyzer.analyze(conversations)
        print(f"✅ フィードバック分析完了 (信頼度: {feedback_result.confidence:.3f})")
        
        # 7. ワークフロー分析
        print("⚙️ ワークフロー分析を実行しています...")
        workflow_analyzer = WorkflowAnalyzer()
        workflow_result = workflow_analyzer.analyze(conversations)
        print(f"✅ ワークフロー分析完了 (信頼度: {workflow_result.confidence:.3f})")
        
        # 8. レポート生成
        print("📄 レポートを生成しています...")
        reporter = MarkdownReporter()
        report_content = reporter.generate_report(
            conversations, 
            [feedback_result, workflow_result]
        )
        
        # 9. レポート保存
        output_file = Path("analysis_report.md")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ 分析完了! レポートを保存しました: {output_file}")
        print()
        
        # 10. 簡単なサマリー表示
        print("📊 分析サマリー:")
        print(f"  • 分析した対話数: {len(conversations)}")
        
        # フィードバック分析結果
        if "sentiment_distribution" in feedback_result.findings:
            distribution = feedback_result.findings["sentiment_distribution"]
            print(f"  • ポジティブフィードバック: {distribution.get('positive', 0):.1f}%")
            print(f"  • ネガティブフィードバック: {distribution.get('negative', 0):.1f}%")
        
        # ワークフロー分析結果
        if "efficiency_metrics" in workflow_result.findings:
            metrics = workflow_result.findings["efficiency_metrics"]
            print(f"  • 成功率: {metrics.get('success_rate', 0):.1%}")
            print(f"  • 平均対話時間: {metrics.get('average_duration_minutes', 0):.1f}分")
        
        print()
        print(f"📖 詳細な分析結果は {output_file} をご確認ください。")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        print("デバッグ情報:")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()