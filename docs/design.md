# Agent Chat Analyze システム設計書

## 1. システムアーキテクチャ

### 1.1 全体構成

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Interface │    │  Analysis Core  │    │   DuckDB        │
│                 │    │                 │    │                 │
│ - Command       │───▶│ - Log Parser    │───▶│ - Conversation  │
│ - Interactive   │    │ - Analyzer      │    │ - Feedback      │
│ - Help          │    │ - Report Gen    │    │ - Actions       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Output         │
                       │                 │
                       │ - Markdown      │
                       │ - Console       │
                       └─────────────────┘
```

### 1.2 レイヤ構成

- **Presentation Layer**: CLI インターフェース
- **Business Logic Layer**: 分析ロジック、レポート生成
- **Data Access Layer**: DuckDB操作、データモデル
- **Data Layer**: 構造化された対話データ

## 2. モジュール設計

### 2.1 パッケージ構成

```
agent_chat_analyze/
├── __init__.py
├── cli.py                    # CLI エントリーポイント
├── models/
│   ├── __init__.py
│   ├── conversation.py       # 対話データモデル
│   ├── feedback.py          # フィードバックデータモデル
│   └── analysis.py          # 分析結果モデル
├── parsers/
│   ├── __init__.py
│   ├── base.py              # パーサーベースクラス
│   └── claude_code.py       # Claude Code JSONL形式パーサー
├── database/
│   ├── __init__.py
│   ├── connection.py        # DuckDB接続管理
│   ├── schema.py           # データベーススキーマ
│   └── repository.py       # データアクセス層
├── analyzers/
│   ├── __init__.py
│   ├── base.py              # 分析ベースクラス
│   ├── feedback_analyzer.py # フィードバック分析
│   └── workflow_analyzer.py # ワークフロー分析
├── reporters/
│   ├── __init__.py
│   ├── base.py              # レポーターベースクラス
│   └── markdown_reporter.py # マークダウンレポート
└── utils/
    ├── __init__.py
    ├── config.py            # 設定管理
    └── logging.py           # ログ設定
```

### 2.2 主要クラス設計

#### 2.2.1 データモデル (models/)

```python
# models/conversation.py
@dataclass
class Message:
    role: str              # "user" | "assistant" | "system"
    content: str
    timestamp: datetime
    metadata: dict[str, Any]

@dataclass
class Conversation:
    id: str
    messages: list[Message]
    started_at: datetime
    ended_at: datetime
    topic: str | None
    outcome: str | None     # "success" | "failure" | "partial"

# models/feedback.py
@dataclass
class Feedback:
    conversation_id: str
    message_id: str
    feedback_type: str      # "positive" | "negative" | "request"
    content: str
    timestamp: datetime

# models/analysis.py
@dataclass
class AnalysisResult:
    conversation_id: str
    analysis_type: str      # "feedback" | "workflow"
    findings: list[dict[str, Any]]
    recommendations: list[str]
    confidence: float
```

#### 2.2.2 パーサー (parsers/)

```python
# parsers/base.py
class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> list[Conversation]:
        pass
    
    @abstractmethod
    def validate_format(self, file_path: Path) -> bool:
        pass

# parsers/claude_code.py
class ClaudeCodeParser(BaseParser):
    def parse(self, file_path: Path) -> list[Conversation]:
        # Claude Code JSONL形式の対話ログを解析
        # sessionIdでグループ化してConversationオブジェクトを作成
        pass
    
    def _parse_message_entry(self, entry: dict) -> Optional[Message]:
        # 個々のJSONLエントリからMessageオブジェクトを作成
        pass
    
    def _extract_feedback(self, message: str) -> list[Feedback]:
        # フィードバック要素を抽出
        pass
```

#### 2.2.3 分析器 (analyzers/)

```python
# analyzers/base.py
class BaseAnalyzer(ABC):
    @abstractmethod
    def analyze(self, conversations: list[Conversation]) -> AnalysisResult:
        pass

# analyzers/feedback_analyzer.py
class FeedbackAnalyzer(BaseAnalyzer):
    def analyze(self, conversations: list[Conversation]) -> AnalysisResult:
        # フィードバック傾向を分析
        pass
    
    def _identify_patterns(self, feedbacks: list[Feedback]) -> list[dict]:
        # パターンを識別
        pass
    
    def _generate_recommendations(self, patterns: list[dict]) -> list[str]:
        # 推奨事項を生成
        pass

# analyzers/workflow_analyzer.py
class WorkflowAnalyzer(BaseAnalyzer):
    def analyze(self, conversations: list[Conversation]) -> AnalysisResult:
        # ワークフロー分析
        pass
    
    def _identify_success_factors(self, conversations: list[Conversation]) -> list[dict]:
        # 成功要因を識別
        pass
    
    def _identify_blocking_factors(self, conversations: list[Conversation]) -> list[dict]:
        # 阻害要因を識別
        pass
```

## 3. データベース設計

### 3.1 テーブル設計

```sql
-- 対話テーブル (sessionIdベースで管理)
CREATE TABLE conversations (
    id VARCHAR PRIMARY KEY,           -- sessionId
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    topic VARCHAR,
    outcome VARCHAR,                  -- "success" | "failure" | "partial"
    metadata JSON
);

-- メッセージテーブル (Claude Code JSONLエントリから抽出)
CREATE TABLE messages (
    id VARCHAR PRIMARY KEY,           -- 自動生成UUID
    conversation_id VARCHAR,          -- sessionId
    role VARCHAR,                     -- "user" | "assistant"
    content TEXT,                     -- 抽出されたテキスト内容
    timestamp TIMESTAMP,              -- ISO8601形式から変換
    metadata JSON,                    -- uuid, parentUuid, cwd, version等
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- フィードバックテーブル
CREATE TABLE feedbacks (
    id VARCHAR PRIMARY KEY,
    conversation_id VARCHAR,
    message_id VARCHAR,
    feedback_type VARCHAR,
    content TEXT,
    timestamp TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (message_id) REFERENCES messages(id)
);

-- 分析結果テーブル
CREATE TABLE analysis_results (
    id VARCHAR PRIMARY KEY,
    conversation_id VARCHAR,
    analysis_type VARCHAR,
    findings JSON,
    recommendations JSON,
    confidence FLOAT,
    created_at TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
```

### 3.2 インデックス設計

```sql
-- パフォーマンス最適化のためのインデックス
CREATE INDEX idx_conversations_started_at ON conversations(started_at);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
CREATE INDEX idx_feedbacks_conversation_id ON feedbacks(conversation_id);
CREATE INDEX idx_feedbacks_type ON feedbacks(feedback_type);
CREATE INDEX idx_analysis_results_type ON analysis_results(analysis_type);
```

### 3.3 Claude Code JSONLデータ構造

実際のClaude Code JSONLエントリの構造例：

```json
{
  "parentUuid": "user-msg-001",
  "isSidechain": false,
  "userType": "external",
  "cwd": "/home/project",
  "sessionId": "session-123",
  "version": "1.0.53",
  "type": "assistant",
  "message": {
    "role": "assistant",
    "content": [
      {
        "type": "text",
        "text": "実際のレスポンステキスト"
      }
    ]
  },
  "uuid": "assistant-msg-001",
  "timestamp": "2024-01-15T10:00:01.000Z"
}
```

**解析時の処理**:
1. `sessionId`でグループ化してConversationを作成
2. `message.content`配列から`type: "text"`のテキストを抽出
3. `timestamp`をISO8601形式からdatetimeに変換
4. `uuid`, `parentUuid`, `cwd`, `version`をmetadataとして保存

## 4. CLI設計

### 4.1 コマンド構成

```bash
# 基本的な使用方法
agent-chat-analyze --help

# 対話ログの解析
agent-chat-analyze analyze --input chat.log --output report.md

# インタラクティブモード
agent-chat-analyze interactive

# 特定の分析のみ実行
agent-chat-analyze analyze --input chat.log --analysis-type feedback
agent-chat-analyze analyze --input chat.log --analysis-type workflow

# データベース操作
agent-chat-analyze db --init        # データベース初期化
agent-chat-analyze db --status      # データベース状態確認
agent-chat-analyze db --cleanup     # データベースクリーンアップ
```

### 4.2 対話フロー

```
1. ファイル選択
   └─ 対話ログファイルの指定
   
2. 解析タイプ選択
   ├─ フィードバック分析
   ├─ ワークフロー分析
   └─ 両方

3. 分析実行
   ├─ 進捗表示
   └─ エラーハンドリング

4. 結果出力
   ├─ マークダウンレポート生成
   └─ コンソール結果表示
```

## 5. 分析アルゴリズム設計

### 5.1 フィードバック分析

```python
def analyze_feedback_patterns(feedbacks: list[Feedback]) -> dict:
    """
    フィードバックパターンの分析
    
    1. 感情分析（positive/negative/neutral）
    2. 頻出キーワード抽出
    3. 時系列パターン分析
    4. 改善提案生成
    """
    patterns = {
        'sentiment_distribution': analyze_sentiment(feedbacks),
        'keyword_frequency': extract_keywords(feedbacks),
        'temporal_patterns': analyze_temporal_patterns(feedbacks),
        'improvement_suggestions': generate_improvements(feedbacks)
    }
    return patterns
```

### 5.2 ワークフロー分析

```python
def analyze_workflow_patterns(conversations: list[Conversation]) -> dict:
    """
    ワークフロー分析
    
    1. 成功/失敗パターンの識別
    2. 作業効率の測定
    3. 阻害要因の特定
    4. 最適化提案
    """
    patterns = {
        'success_factors': identify_success_patterns(conversations),
        'blocking_factors': identify_blocking_patterns(conversations),
        'efficiency_metrics': calculate_efficiency(conversations),
        'optimization_suggestions': generate_optimizations(conversations)
    }
    return patterns
```

## 6. レポート設計

### 6.1 マークダウンレポート構成

```markdown
# 対話分析レポート

## 概要
- 分析期間: {period}
- 対話数: {conversation_count}
- 分析タイプ: {analysis_types}

## フィードバック分析結果
### 感情分析
- ポジティブ: {positive_percentage}%
- ネガティブ: {negative_percentage}%
- 中立: {neutral_percentage}%

### 主要パターン
{patterns}

### 改善提案
{recommendations}

## ワークフロー分析結果
### 成功要因
{success_factors}

### 阻害要因
{blocking_factors}

### 最適化提案
{optimization_suggestions}

## 推奨プロンプト
{generated_prompts}
```

## 7. エラーハンドリング設計

### 7.1 エラー分類

- **入力エラー**: ファイル形式不正、ファイル未存在
- **解析エラー**: パース失敗、データ不整合
- **データベースエラー**: 接続失敗、クエリエラー
- **分析エラー**: 分析失敗、メモリ不足

### 7.2 エラー処理方針

```python
class AnalysisError(Exception):
    """分析エラーの基底クラス"""
    pass

class ParseError(AnalysisError):
    """パース関連エラー"""
    pass

class DatabaseError(AnalysisError):
    """データベース関連エラー"""
    pass
```

## 8. テスト設計

### 8.1 テスト戦略

- **単体テスト**: 各モジュールの機能テスト
- **統合テスト**: モジュール間の連携テスト
- **E2Eテスト**: CLI全体のテスト
- **パフォーマンステスト**: 大量データでの性能テスト

### 8.2 テストデータ

```python
# tests/fixtures/sample_conversations.py
SAMPLE_CONVERSATIONS = [
    {
        "id": "conv_001",
        "messages": [...],
        "expected_feedback_count": 3,
        "expected_outcome": "success"
    },
    # ... more test data
]
```

## 9. 設定管理

### 9.1 設定ファイル

```python
# config/default.py
DATABASE_URL = "duckdb:///agent_chat_analyze.db"
LOG_LEVEL = "INFO"
REPORT_TEMPLATE = "templates/report.md"
MAX_CONVERSATIONS = 1000
ANALYSIS_TIMEOUT = 300  # seconds
```

## 10. 性能設計

### 10.1 パフォーマンス目標

- 1000件の対話ログを10秒以内で処理
- メモリ使用量を1GB以下に抑制
- 同時実行時の競合回避

### 10.2 最適化戦略

- DuckDBの列指向ストレージ活用
- バッチ処理による効率化
- インデックスの適切な配置
- メモリ効率的なデータ構造の使用