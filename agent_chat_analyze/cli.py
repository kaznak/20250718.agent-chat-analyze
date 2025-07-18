"""Command Line Interface for Agent Chat Analyze"""

import click
import os
from pathlib import Path
from typing import Optional

from .database import DatabaseManager
from .parsers import ClaudeCodeParser
from .reporters import MarkdownReporter

# Conditional imports for ML dependencies
try:
    from .embeddings import SentenceTransformerEmbedding
    from .analyzers import FeedbackAnalyzer, WorkflowAnalyzer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


@click.group()
@click.version_option()
def main():
    """Agent Chat Analyze - AIエージェントとの対話ログを分析するツール"""
    pass


@main.command()
@click.option('--input', '-i', 'input_path', required=True, 
              help='Claude Code JSONLログファイルのパス')
@click.option('--output', '-o', 'output_path', default='analysis_report.md',
              help='出力レポートファイルのパス')
@click.option('--analysis-type', '-t', 'analysis_type', 
              type=click.Choice(['feedback', 'workflow', 'all']), default='all',
              help='分析タイプを選択')
@click.option('--db-path', default='agent_chat_analyze.db',
              help='データベースファイルのパス')
def analyze(input_path: str, output_path: str, analysis_type: str, db_path: str):
    """Claude Code対話ログを分析する"""
    
    input_file = Path(input_path)
    if not input_file.exists():
        click.echo(f"エラー: ファイル '{input_path}' が見つかりません。", err=True)
        return
    
    click.echo(f"対話ログを分析しています: {input_path}")
    
    try:
        # データベース初期化
        click.echo("データベースを初期化しています...")
        db_manager = DatabaseManager(db_path)
        db_manager.initialize_database()
        
        # パーサーで対話ログを解析
        click.echo("対話ログを解析しています...")
        parser = ClaudeCodeParser()
        conversations = parser.parse(input_file)
        click.echo(f"✓ {len(conversations)} 個の対話を解析しました")
        
        # ML依存関係の確認
        if not EMBEDDINGS_AVAILABLE and analysis_type in ['feedback', 'all']:
            click.echo("⚠️ 機械学習ライブラリが利用できません。", err=True)
            click.echo("フィードバック分析には sentence-transformers と scikit-learn が必要です。", err=True)
            click.echo("インストールコマンド: pip install sentence-transformers scikit-learn", err=True)
            if analysis_type == 'feedback':
                return
            else:
                click.echo("ワークフロー分析のみ実行します...")
                analysis_type = 'workflow'
        
        # 埋め込みモデルを初期化
        if analysis_type in ['feedback', 'all']:
            click.echo("埋め込みモデルを読み込んでいます...")
            embedding_model = SentenceTransformerEmbedding()
        
        # メッセージに埋め込みを生成
        click.echo("ベクトル埋め込みを生成しています...")
        total_messages = sum(len(conv.messages) for conv in conversations)
        processed = 0
        
        for conversation in conversations:
            for message in conversation.messages:
                if message.role == "user" and not message.embedding:
                    message.embedding = embedding_model.encode_single(message.content)
                    processed += 1
                    if processed % 10 == 0:
                        click.echo(f"  {processed}/{total_messages} メッセージを処理済み")
        
        click.echo(f"✓ {processed} 個のメッセージの埋め込みを生成しました")
        
        # 分析実行
        results = []
        
        if analysis_type in ['feedback', 'all']:
            click.echo("フィードバック分析を実行しています...")
            feedback_analyzer = FeedbackAnalyzer(embedding_model)
            feedback_result = feedback_analyzer.analyze(conversations)
            results.append(feedback_result)
            click.echo(f"✓ フィードバック分析完了 (信頼度: {feedback_result.confidence:.3f})")
        
        if analysis_type in ['workflow', 'all']:
            click.echo("ワークフロー分析を実行しています...")
            workflow_analyzer = WorkflowAnalyzer()
            workflow_result = workflow_analyzer.analyze(conversations)
            results.append(workflow_result)
            click.echo(f"✓ ワークフロー分析完了 (信頼度: {workflow_result.confidence:.3f})")
        
        # レポート生成
        click.echo("レポートを生成しています...")
        reporter = MarkdownReporter()
        report_content = reporter.generate_report(conversations, results)
        
        # レポート保存
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        click.echo(f"✅ 分析完了! レポートを保存しました: {output_path}")
        
    except Exception as e:
        click.echo(f"エラーが発生しました: {str(e)}", err=True)
        raise click.Abort()


@main.command()
def interactive():
    """対話モードで分析を実行"""
    click.echo("🤖 Agent Chat Analyze - 対話モード")
    click.echo()
    
    # Claude Codeログディレクトリを探す
    claude_dir = Path.home() / ".claude" / "projects"
    if claude_dir.exists():
        click.echo(f"Claude Codeプロジェクトディレクトリが見つかりました: {claude_dir}")
        
        # プロジェクト一覧を表示
        projects = [d for d in claude_dir.iterdir() if d.is_dir()]
        if projects:
            click.echo("\n利用可能なプロジェクト:")
            for i, project in enumerate(projects, 1):
                click.echo(f"  {i}. {project.name}")
            
            # プロジェクト選択
            while True:
                try:
                    choice = click.prompt("\n分析するプロジェクト番号を選択してください", type=int)
                    if 1 <= choice <= len(projects):
                        selected_project = projects[choice - 1]
                        break
                    else:
                        click.echo("無効な番号です。")
                except ValueError:
                    click.echo("数字を入力してください。")
            
            # セッションファイル一覧
            session_files = list(selected_project.glob("*.jsonl"))
            if session_files:
                click.echo(f"\n'{selected_project.name}' の対話セッション:")
                for i, session_file in enumerate(session_files, 1):
                    click.echo(f"  {i}. {session_file.name}")
                
                # セッション選択
                while True:
                    try:
                        choice = click.prompt("\n分析するセッション番号を選択してください", type=int)
                        if 1 <= choice <= len(session_files):
                            selected_session = session_files[choice - 1]
                            break
                        else:
                            click.echo("無効な番号です。")
                    except ValueError:
                        click.echo("数字を入力してください。")
                
                # 分析タイプ選択
                click.echo("\n分析タイプを選択してください:")
                click.echo("  1. フィードバック分析のみ")
                click.echo("  2. ワークフロー分析のみ")
                click.echo("  3. 両方")
                
                analysis_types = ['feedback', 'workflow', 'all']
                while True:
                    try:
                        choice = click.prompt("選択", type=int)
                        if 1 <= choice <= 3:
                            selected_analysis = analysis_types[choice - 1]
                            break
                        else:
                            click.echo("無効な番号です。")
                    except ValueError:
                        click.echo("数字を入力してください。")
                
                # 出力ファイル名
                default_output = f"analysis_{selected_project.name}_{selected_session.stem}.md"
                output_path = click.prompt(f"\n出力ファイル名", default=default_output)
                
                # 分析実行
                click.echo(f"\n🚀 分析を開始します...")
                
                from click.testing import CliRunner
                runner = CliRunner()
                result = runner.invoke(analyze, [
                    '--input', str(selected_session),
                    '--output', output_path,
                    '--analysis-type', selected_analysis
                ])
                
                if result.exit_code == 0:
                    click.echo(result.output)
                else:
                    click.echo(f"エラー: {result.output}", err=True)
            
            else:
                click.echo(f"プロジェクト '{selected_project.name}' にJSONLファイルが見つかりません。")
        else:
            click.echo("Claude Codeプロジェクトが見つかりません。")
    else:
        click.echo("Claude Codeディレクトリが見つかりません。")
        click.echo("手動でファイルパスを指定してください:")
        
        input_path = click.prompt("Claude Code JSONLファイルのパス")
        if Path(input_path).exists():
            output_path = click.prompt("出力ファイル名", default="analysis_report.md")
            
            # 分析実行
            from click.testing import CliRunner
            runner = CliRunner()
            result = runner.invoke(analyze, [
                '--input', input_path,
                '--output', output_path,
                '--analysis-type', 'all'
            ])
            
            if result.exit_code == 0:
                click.echo(result.output)
            else:
                click.echo(f"エラー: {result.output}", err=True)
        else:
            click.echo("ファイルが見つかりません。")


@main.group()
def db():
    """データベース操作"""
    pass


@db.command()
@click.option('--db-path', default='agent_chat_analyze.db',
              help='データベースファイルのパス')
def init(db_path: str):
    """データベースを初期化"""
    try:
        db_manager = DatabaseManager(db_path)
        db_manager.initialize_database()
        click.echo(f"✅ データベースを初期化しました: {db_path}")
    except Exception as e:
        click.echo(f"エラー: {str(e)}", err=True)


@db.command()
@click.option('--db-path', default='agent_chat_analyze.db',
              help='データベースファイルのパス')
def status(db_path: str):
    """データベースの状態を確認"""
    db_file = Path(db_path)
    if db_file.exists():
        click.echo(f"✅ データベースファイル: {db_path}")
        click.echo(f"   サイズ: {db_file.stat().st_size / 1024:.1f} KB")
        
        try:
            db_manager = DatabaseManager(db_path)
            conn = db_manager.get_connection()
            
            # テーブル情報取得
            tables = conn.execute("SHOW TABLES").fetchall()
            click.echo(f"   テーブル数: {len(tables)}")
            
            for table in tables:
                table_name = table[0]
                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                click.echo(f"   - {table_name}: {count} レコード")
                
        except Exception as e:
            click.echo(f"データベース読み込みエラー: {str(e)}", err=True)
    else:
        click.echo(f"❌ データベースファイルが見つかりません: {db_path}")


@db.command()
@click.option('--db-path', default='agent_chat_analyze.db',
              help='データベースファイルのパス')
@click.confirmation_option(prompt='データベースを削除しますか？')
def cleanup(db_path: str):
    """データベースをクリーンアップ"""
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()
        click.echo(f"✅ データベースを削除しました: {db_path}")
    else:
        click.echo(f"データベースファイルが見つかりません: {db_path}")


if __name__ == '__main__':
    main()