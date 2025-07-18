"""Markdown report generator"""

from typing import List, Dict, Any
from datetime import datetime
from .base import BaseReporter
from ..models import Conversation, AnalysisResult


class MarkdownReporter(BaseReporter):
    """Markdown format report generator"""
    
    def generate_report(self, 
                       conversations: List[Conversation], 
                       analysis_results: List[AnalysisResult]) -> str:
        """Generate markdown analysis report
        
        Args:
            conversations: List of analyzed conversations
            analysis_results: List of analysis results
            
        Returns:
            Markdown formatted report
        """
        report = []
        
        # Header
        report.append("# Agent Chat Analyze - 対話分析レポート")
        report.append("")
        report.append(f"**生成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        report.append("")
        
        # Overview
        report.append("## 📊 概要")
        report.append("")
        report.append(f"- **分析対象対話数**: {len(conversations)}")
        report.append(f"- **分析タイプ**: {', '.join([r.analysis_type for r in analysis_results])}")
        
        if conversations:
            total_messages = sum(len(conv.messages) for conv in conversations)
            user_messages = sum(len([m for m in conv.messages if m.role == 'user']) for conv in conversations)
            assistant_messages = sum(len([m for m in conv.messages if m.role == 'assistant']) for conv in conversations)
            
            report.append(f"- **総メッセージ数**: {total_messages}")
            report.append(f"  - ユーザーメッセージ: {user_messages}")
            report.append(f"  - アシスタントメッセージ: {assistant_messages}")
            
            # 期間
            start_time = min(conv.started_at for conv in conversations)
            end_time = max(conv.ended_at for conv in conversations)
            report.append(f"- **分析期間**: {start_time.strftime('%Y-%m-%d %H:%M')} ～ {end_time.strftime('%Y-%m-%d %H:%M')}")
        
        report.append("")
        
        # 各分析結果を処理
        for result in analysis_results:
            if result.analysis_type == "feedback":
                report.extend(self._generate_feedback_section(result))
            elif result.analysis_type == "workflow":
                report.extend(self._generate_workflow_section(result))
        
        # 推奨事項
        report.append("## 🎯 総合推奨事項")
        report.append("")
        
        all_recommendations = []
        for result in analysis_results:
            all_recommendations.extend(result.recommendations)
        
        if all_recommendations:
            for i, rec in enumerate(all_recommendations, 1):
                report.append(f"{i}. {rec}")
        else:
            report.append("特に推奨事項はありません。現在のアプローチを継続してください。")
        
        report.append("")
        
        # フッター
        report.append("---")
        report.append("")
        report.append("*このレポートは Agent Chat Analyze により自動生成されました。*")
        report.append("")
        
        return "\n".join(report)
    
    def _generate_feedback_section(self, result: AnalysisResult) -> List[str]:
        """Generate feedback analysis section"""
        section = []
        findings = result.findings
        
        section.append("## 💬 フィードバック分析結果")
        section.append("")
        section.append(f"**信頼度**: {result.confidence:.1%}")
        section.append("")
        
        # 感情分布
        if "sentiment_distribution" in findings:
            section.append("### 感情分布")
            section.append("")
            
            distribution = findings["sentiment_distribution"]
            section.append("| 感情タイプ | 割合 |")
            section.append("|----------|------|")
            
            sentiment_labels = {
                "positive": "ポジティブ 😊",
                "negative": "ネガティブ 😟", 
                "request": "リクエスト 🙏",
                "neutral": "中立 😐"
            }
            
            for sentiment, percentage in distribution.items():
                label = sentiment_labels.get(sentiment, sentiment)
                section.append(f"| {label} | {percentage:.1f}% |")
            
            section.append("")
            
            # 感情分布の解釈
            if distribution.get("positive", 0) > 50:
                section.append("✅ **良好**: ポジティブなフィードバックが多く、ユーザー満足度が高いです。")
            elif distribution.get("negative", 0) > 30:
                section.append("⚠️ **注意**: ネガティブなフィードバックが多く、改善の余地があります。")
            elif distribution.get("request", 0) > 40:
                section.append("📝 **改善点**: リクエストが多く、初期提案の完成度向上が必要かもしれません。")
            
            section.append("")
        
        # フィードバッククラスター
        if "feedback_clusters" in findings and findings["feedback_clusters"]:
            section.append("### 主要なフィードバックパターン")
            section.append("")
            
            for i, cluster in enumerate(findings["feedback_clusters"][:5], 1):  # 上位5つ
                section.append(f"#### パターン {i}")
                section.append(f"- **メッセージ数**: {cluster['message_count']}")
                section.append(f"- **共通テーマ**: {', '.join(cluster['common_themes'][:5])}")
                section.append("")
                section.append("**サンプルメッセージ**:")
                for msg in cluster["sample_messages"][:3]:
                    section.append(f"> {msg['content']}")
                section.append("")
        
        # 時系列パターン
        if "temporal_patterns" in findings and findings["temporal_patterns"]:
            temporal = findings["temporal_patterns"]
            section.append("### 時系列パターン")
            section.append("")
            
            if "sentiment_trend" in temporal and temporal["sentiment_trend"]:
                section.append("**感情の変化傾向**:")
                section.append("")
                
                trend = temporal["sentiment_trend"]
                if len(trend) >= 2:
                    early_negative = sum(t["sentiment_counts"]["negative"] for t in trend[:len(trend)//2])
                    late_negative = sum(t["sentiment_counts"]["negative"] for t in trend[len(trend)//2:])
                    
                    if late_negative > early_negative * 1.5:
                        section.append("📈 時間の経過とともにネガティブフィードバックが増加しています。")
                    elif early_negative > late_negative * 1.5:
                        section.append("📉 時間の経過とともにフィードバックが改善しています。")
                    else:
                        section.append("➡️ 感情の変化に明確な傾向は見られません。")
                
                section.append("")
        
        return section
    
    def _generate_workflow_section(self, result: AnalysisResult) -> List[str]:
        """Generate workflow analysis section"""
        section = []
        findings = result.findings
        
        section.append("## ⚙️ ワークフロー分析結果")
        section.append("")
        section.append(f"**信頼度**: {result.confidence:.1%}")
        section.append("")
        
        # 効率性指標
        if "efficiency_metrics" in findings:
            metrics = findings["efficiency_metrics"]
            section.append("### 効率性指標")
            section.append("")
            section.append("| 指標 | 値 |")
            section.append("|------|----:|")
            section.append(f"| 成功率 | {metrics.get('success_rate', 0):.1%} |")
            section.append(f"| 失敗率 | {metrics.get('failure_rate', 0):.1%} |")
            section.append(f"| 部分成功率 | {metrics.get('partial_rate', 0):.1%} |")
            section.append(f"| 平均対話時間 | {metrics.get('average_duration_minutes', 0):.1f}分 |")
            section.append(f"| 平均メッセージ数 | {metrics.get('average_message_count', 0):.1f} |")
            section.append("")
            
            # 効率性の評価
            success_rate = metrics.get('success_rate', 0)
            if success_rate >= 0.8:
                section.append("🎉 **優秀**: 非常に高い成功率を達成しています。")
            elif success_rate >= 0.6:
                section.append("✅ **良好**: 適切な成功率を維持しています。")
            elif success_rate >= 0.4:
                section.append("⚠️ **改善要**: 成功率の向上が必要です。")
            else:
                section.append("❌ **要注意**: 成功率が低く、大幅な改善が必要です。")
            
            section.append("")
        
        # 成功要因
        if "success_factors" in findings and findings["success_factors"]:
            section.append("### 🌟 主要な成功要因")
            section.append("")
            section.append("| 要因 | 出現回数 | 成功率 | 関連ロール |")
            section.append("|------|--------:|-------:|----------|")
            
            for factor in findings["success_factors"][:10]:  # 上位10要因
                section.append(f"| {factor['indicator']} | {factor['frequency']} | {factor['success_rate']:.1%} | {factor['role']} |")
            
            section.append("")
        
        # 阻害要因
        if "blocking_factors" in findings and findings["blocking_factors"]:
            section.append("### ⚠️ 主要な阻害要因")
            section.append("")
            section.append("| 要因 | 出現回数 | 失敗率 | 関連ロール |")
            section.append("|------|--------:|-------:|----------|")
            
            for factor in findings["blocking_factors"][:10]:  # 上位10要因
                section.append(f"| {factor['indicator']} | {factor['frequency']} | {factor['failure_rate']:.1%} | {factor['role']} |")
            
            section.append("")
        
        # 結果分布
        if "conversation_outcomes" in findings:
            outcomes = findings["conversation_outcomes"]
            section.append("### 📈 結果分布")
            section.append("")
            
            for outcome, data in outcomes.items():
                outcome_labels = {
                    "success": "成功 ✅",
                    "failure": "失敗 ❌", 
                    "partial": "部分成功 ⚠️"
                }
                label = outcome_labels.get(outcome, outcome)
                section.append(f"**{label}**")
                section.append(f"- 件数: {data['count']}")
                section.append(f"- 平均時間: {data['avg_duration']:.1f}分")
                section.append(f"- 平均メッセージ数: {data['avg_messages']:.1f}")
                section.append("")
        
        return section