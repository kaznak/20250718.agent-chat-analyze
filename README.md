# Agent Chat Analyze

AIエージェント（特にClaude Code）との対話内容を分析し、新しい洞察を得るためのツールです。

## 概要

このツールは、AIエージェントとの対話ログを分析し、以下の情報を提供します：

- **ベクトル埋め込みベースの意味的分析**: 単純な正規表現ではなく、文脈を理解したフィードバック分析
- **ユーザーフィードバックの傾向分析**: ポジティブ・ネガティブ・リクエストの分布と時系列変化
- **作業の進展を促進する要因の特定**: 成功パターンの抽出
- **作業を阻害する要因の分析**: 失敗要因の特定と対策提案
- **改善されたプロンプトの提案**: 分析結果に基づく具体的な改善案

## 機能

- **Claude Code JSONL形式**の対話ログ解析
- **384次元ベクトル埋め込み**による意味的類似性分析
- **多言語対応**（日本語・英語）のテキスト処理
- **フィードバック傾向**の分析とクラスタリング
- **ワークフロー効率性**の測定
- **インタラクティブなCLI**インターフェース
- **マークダウン形式**の詳細レポート生成

## 技術スタック

- Python 3.9+
- DuckDB (分析用データベース、ベクトル対応)
- SentenceTransformers (多言語ベクトル埋め込み)
- scikit-learn (機械学習・クラスタリング)
- Click (CLI)
- Pydantic (データモデル)

## インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd agent-chat-analyze

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows

# 依存関係をインストール
pip install -e .
```

## 使用方法

### 1. コマンドライン（推奨）

```bash
# 基本的な分析
agent-chat-analyze analyze --input path/to/session.jsonl --output report.md

# 特定の分析タイプのみ実行
agent-chat-analyze analyze --input session.jsonl --analysis-type feedback
agent-chat-analyze analyze --input session.jsonl --analysis-type workflow

# インタラクティブモード（自動でClaude Codeログを検出）
agent-chat-analyze interactive

# データベース操作
agent-chat-analyze db init          # データベース初期化
agent-chat-analyze db status        # データベース状態確認
agent-chat-analyze db cleanup       # データベース削除
```

### 2. Pythonスクリプト

```python
from agent_chat_analyze.parsers import ClaudeCodeParser
from agent_chat_analyze.embeddings import SentenceTransformerEmbedding
from agent_chat_analyze.analyzers import FeedbackAnalyzer, WorkflowAnalyzer
from agent_chat_analyze.reporters import MarkdownReporter

# ログファイルを解析
parser = ClaudeCodeParser()
conversations = parser.parse("session.jsonl")

# 埋め込みモデルを初期化
embedding_model = SentenceTransformerEmbedding()

# フィードバック分析
feedback_analyzer = FeedbackAnalyzer(embedding_model)
feedback_result = feedback_analyzer.analyze(conversations)

# ワークフロー分析
workflow_analyzer = WorkflowAnalyzer()
workflow_result = workflow_analyzer.analyze(conversations)

# レポート生成
reporter = MarkdownReporter()
report = reporter.generate_report(conversations, [feedback_result, workflow_result])
```

### 3. 使用例スクリプト

```bash
# 対話的な使用例を実行
python example_usage.py
```

## Claude Codeログファイルの場所

Claude Codeの対話ログは以下の場所に保存されています：

```
~/.claude/projects/[プロジェクト名]/[セッションID].jsonl
```

例：
```
/home/user/.claude/projects/my-project/session-abc123.jsonl
```

## 分析結果の読み方

### フィードバック分析
- **感情分布**: ポジティブ・ネガティブ・リクエスト・中立の割合
- **フィードバッククラスター**: 似たような内容のフィードバックをグループ化
- **時系列パターン**: 感情の変化傾向

### ワークフロー分析
- **効率性指標**: 成功率、平均対話時間、メッセージ数
- **成功要因**: 成功につながる行動・発言パターン
- **阻害要因**: 失敗や停滞を引き起こす要因

## 応用例

1. **個人の対話スキル向上**
   ```bash
   # 自分の過去の対話を分析
   agent-chat-analyze analyze --input ~/.claude/projects/my-work/session-*.jsonl
   ```

2. **チームの作業パターン分析**
   ```bash
   # 複数メンバーの対話パターンを比較
   for session in team_sessions/*.jsonl; do
     agent-chat-analyze analyze --input "$session" --output "analysis_$(basename $session .jsonl).md"
   done
   ```

3. **プロジェクト振り返り**
   ```bash
   # プロジェクト全体の対話を総合分析
   agent-chat-analyze analyze --input project_sessions/ --analysis-type all
   ```

## 特徴

### ベクトル埋め込みの利点
- **文脈理解**: 「素晴らしい」と「great」を同じポジティブ感情として認識
- **意味的類似性**: 表現は異なるが同じ意味のフィードバックをクラスタリング
- **多言語対応**: 日本語と英語が混在した対話でも正確に分析

### 実用的な洞察
- **具体的な改善提案**: 単なる分析結果ではなく、実行可能な改善案を提供
- **定量的な評価**: 信頼度スコアによる分析結果の妥当性評価
- **時系列分析**: 対話の進行に伴う感情や効率性の変化を追跡

## ライセンス

MIT License