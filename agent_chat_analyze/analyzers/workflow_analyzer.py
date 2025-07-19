"""Workflow analyzer for identifying success and blocking factors"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from ..models import Conversation, Message, AnalysisResult
from .base import BaseAnalyzer


class WorkflowAnalyzer(BaseAnalyzer):
    """Analyzer for workflow patterns and success/blocking factors"""
    
    def __init__(self):
        """Initialize workflow analyzer"""
        self.success_indicators = [
            "完了", "成功", "解決", "実装", "動作", "正常", "完璧", "素晴らしい",
            "completed", "success", "solved", "implemented", "working", "perfect", "great"
        ]
        
        self.blocking_indicators = [
            "エラー", "問題", "失敗", "できない", "分からない", "不明", "困った", "停止",
            "error", "problem", "failed", "cannot", "unknown", "stuck", "stopped", "blocked"
        ]
        
        self.progress_indicators = [
            "進捗", "進行", "開始", "作成", "追加", "修正", "改善", "更新",
            "progress", "started", "created", "added", "fixed", "improved", "updated"
        ]
    
    def analyze(self, conversations: List[Conversation]) -> AnalysisResult:
        """Analyze workflow patterns
        
        Args:
            conversations: List of conversations to analyze
            
        Returns:
            Analysis result with workflow patterns
        """
        if not conversations:
            return AnalysisResult(
                conversation_id="all",
                analysis_type="workflow",
                findings={
                    "total_conversations": 0,
                    "success_factors": [],
                    "blocking_factors": [],
                    "efficiency_metrics": {}
                },
                recommendations=[],
                confidence=0.0
            )
        
        # Analyze each conversation
        conversation_analyses = []
        for conv in conversations:
            analysis = self._analyze_conversation(conv)
            conversation_analyses.append(analysis)
        
        # Aggregate findings
        success_factors = self._aggregate_success_factors(conversation_analyses)
        blocking_factors = self._aggregate_blocking_factors(conversation_analyses)
        efficiency_metrics = self._calculate_efficiency_metrics(conversations, conversation_analyses)
        
        # Generate recommendations
        recommendations = self._generate_workflow_recommendations(
            success_factors, blocking_factors, efficiency_metrics
        )
        
        findings = {
            "total_conversations": len(conversations),
            "success_factors": success_factors,
            "blocking_factors": blocking_factors,
            "efficiency_metrics": efficiency_metrics,
            "conversation_outcomes": self._summarize_outcomes(conversation_analyses)
        }
        
        confidence = self._calculate_confidence(conversations, conversation_analyses)
        
        return AnalysisResult(
            conversation_id="all",
            analysis_type="workflow",
            findings=findings,
            recommendations=recommendations,
            confidence=confidence
        )
    
    def _analyze_conversation(self, conversation: Conversation) -> Dict[str, Any]:
        """Analyze a single conversation for workflow patterns"""
        analysis = {
            "conversation_id": conversation.id,
            "outcome": conversation.outcome,
            "duration": self._calculate_duration(conversation),
            "message_count": len(conversation.messages),
            "user_message_count": len([m for m in conversation.messages if m.role == "user"]),
            "assistant_message_count": len([m for m in conversation.messages if m.role == "assistant"]),
            "success_signals": [],
            "blocking_signals": [],
            "progress_signals": [],
            "workflow_stages": self._identify_workflow_stages(conversation)
        }
        
        # Analyze message content for indicators
        for message in conversation.messages:
            content = message.content.lower()
            
            # Check for success indicators
            for indicator in self.success_indicators:
                if indicator in content:
                    analysis["success_signals"].append({
                        "indicator": indicator,
                        "message_role": message.role,
                        "timestamp": message.timestamp.isoformat(),
                        "context": content[:100] + "..." if len(content) > 100 else content
                    })
            
            # Check for blocking indicators
            for indicator in self.blocking_indicators:
                if indicator in content:
                    analysis["blocking_signals"].append({
                        "indicator": indicator,
                        "message_role": message.role,
                        "timestamp": message.timestamp.isoformat(),
                        "context": content[:100] + "..." if len(content) > 100 else content
                    })
            
            # Check for progress indicators
            for indicator in self.progress_indicators:
                if indicator in content:
                    analysis["progress_signals"].append({
                        "indicator": indicator,
                        "message_role": message.role,
                        "timestamp": message.timestamp.isoformat(),
                        "context": content[:100] + "..." if len(content) > 100 else content
                    })
        
        return analysis
    
    def _calculate_duration(self, conversation: Conversation) -> Dict[str, Any]:
        """Calculate conversation duration"""
        if not conversation.messages:
            return {"total_minutes": 0, "active_periods": 0}
        
        start_time = conversation.started_at
        end_time = conversation.ended_at
        total_duration = end_time - start_time
        
        # Calculate active periods (gaps less than 10 minutes count as active)
        active_periods = 0
        last_message_time = None
        
        for message in sorted(conversation.messages, key=lambda x: x.timestamp):
            if last_message_time is None:
                active_periods = 1
            else:
                gap = message.timestamp - last_message_time
                if gap > timedelta(minutes=10):
                    active_periods += 1
            last_message_time = message.timestamp
        
        return {
            "total_minutes": total_duration.total_seconds() / 60,
            "active_periods": active_periods,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    
    def _identify_workflow_stages(self, conversation: Conversation) -> List[Dict[str, Any]]:
        """Identify workflow stages in a conversation"""
        stages = []
        
        # Simple stage identification based on message patterns
        current_stage = None
        stage_start = None
        
        for message in conversation.messages:
            content = message.content.lower()
            
            # Determine stage based on content
            if any(word in content for word in ["要件", "仕様", "設計", "requirement", "specification", "design"]):
                new_stage = "requirements"
            elif any(word in content for word in ["実装", "コード", "プログラム", "implement", "code", "program"]):
                new_stage = "implementation"
            elif any(word in content for word in ["テスト", "確認", "検証", "test", "verify", "check"]):
                new_stage = "testing"
            elif any(word in content for word in ["デプロイ", "リリース", "公開", "deploy", "release", "publish"]):
                new_stage = "deployment"
            else:
                new_stage = "discussion"
            
            # If stage changed, record the previous stage
            if current_stage != new_stage:
                if current_stage is not None and stage_start is not None:
                    stages.append({
                        "stage": current_stage,
                        "start_time": stage_start.isoformat(),
                        "end_time": message.timestamp.isoformat(),
                        "duration_minutes": (message.timestamp - stage_start).total_seconds() / 60
                    })
                
                current_stage = new_stage
                stage_start = message.timestamp
        
        # Add the last stage
        if current_stage is not None and stage_start is not None:
            stages.append({
                "stage": current_stage,
                "start_time": stage_start.isoformat(),
                "end_time": conversation.ended_at.isoformat(),
                "duration_minutes": (conversation.ended_at - stage_start).total_seconds() / 60
            })
        
        return stages
    
    def _aggregate_success_factors(self, conversation_analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate success factors across conversations"""
        success_factors = {}
        
        for analysis in conversation_analyses:
            for signal in analysis["success_signals"]:
                indicator = signal["indicator"]
                role = signal["message_role"]
                
                key = f"{indicator}_{role}"
                if key not in success_factors:
                    success_factors[key] = {
                        "indicator": indicator,
                        "role": role,
                        "frequency": 0,
                        "associated_outcomes": []
                    }
                
                success_factors[key]["frequency"] += 1
                success_factors[key]["associated_outcomes"].append(analysis["outcome"])
        
        # Convert to list and sort by frequency
        result = list(success_factors.values())
        result.sort(key=lambda x: x["frequency"], reverse=True)
        
        # Calculate success rate for each factor
        for factor in result:
            outcomes = factor["associated_outcomes"]
            success_rate = len([o for o in outcomes if o == "success"]) / len(outcomes) if outcomes else 0
            factor["success_rate"] = round(success_rate, 3)
        
        return result
    
    def _aggregate_blocking_factors(self, conversation_analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate blocking factors across conversations"""
        blocking_factors = {}
        
        for analysis in conversation_analyses:
            for signal in analysis["blocking_signals"]:
                indicator = signal["indicator"]
                role = signal["message_role"]
                
                key = f"{indicator}_{role}"
                if key not in blocking_factors:
                    blocking_factors[key] = {
                        "indicator": indicator,
                        "role": role,
                        "frequency": 0,
                        "associated_outcomes": []
                    }
                
                blocking_factors[key]["frequency"] += 1
                blocking_factors[key]["associated_outcomes"].append(analysis["outcome"])
        
        # Convert to list and sort by frequency
        result = list(blocking_factors.values())
        result.sort(key=lambda x: x["frequency"], reverse=True)
        
        # Calculate failure rate for each factor
        for factor in result:
            outcomes = factor["associated_outcomes"]
            failure_rate = len([o for o in outcomes if o == "failure"]) / len(outcomes) if outcomes else 0
            factor["failure_rate"] = round(failure_rate, 3)
        
        return result
    
    def _calculate_efficiency_metrics(self, 
                                    conversations: List[Conversation], 
                                    conversation_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate efficiency metrics"""
        if not conversations:
            return {}
        
        # Basic metrics
        total_conversations = len(conversations)
        successful_conversations = len([c for c in conversations if c.outcome == "success"])
        failed_conversations = len([c for c in conversations if c.outcome == "failure"])
        partial_conversations = len([c for c in conversations if c.outcome == "partial"])
        
        # Duration metrics
        durations = [a["duration"]["total_minutes"] for a in conversation_analyses]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Message count metrics
        message_counts = [a["message_count"] for a in conversation_analyses]
        avg_message_count = sum(message_counts) / len(message_counts) if message_counts else 0
        
        # Success rate by duration
        short_conversations = [a for a in conversation_analyses if a["duration"]["total_minutes"] < 30]
        long_conversations = [a for a in conversation_analyses if a["duration"]["total_minutes"] >= 30]
        
        short_success_rate = len([a for a in short_conversations if a["outcome"] == "success"]) / len(short_conversations) if short_conversations else 0
        long_success_rate = len([a for a in long_conversations if a["outcome"] == "success"]) / len(long_conversations) if long_conversations else 0
        
        return {
            "total_conversations": total_conversations,
            "success_rate": round(successful_conversations / total_conversations, 3),
            "failure_rate": round(failed_conversations / total_conversations, 3),
            "partial_rate": round(partial_conversations / total_conversations, 3),
            "average_duration_minutes": round(avg_duration, 2),
            "average_message_count": round(avg_message_count, 2),
            "short_conversation_success_rate": round(short_success_rate, 3),
            "long_conversation_success_rate": round(long_success_rate, 3),
            "outcome_distribution": {
                "success": successful_conversations,
                "failure": failed_conversations,
                "partial": partial_conversations
            }
        }
    
    def _summarize_outcomes(self, conversation_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize conversation outcomes"""
        outcomes = {}
        
        for analysis in conversation_analyses:
            outcome = analysis["outcome"]
            if outcome not in outcomes:
                outcomes[outcome] = {
                    "count": 0,
                    "avg_duration": 0,
                    "avg_messages": 0,
                    "common_stages": []
                }
            
            outcomes[outcome]["count"] += 1
            outcomes[outcome]["avg_duration"] += analysis["duration"]["total_minutes"]
            outcomes[outcome]["avg_messages"] += analysis["message_count"]
        
        # Calculate averages
        for outcome_data in outcomes.values():
            if outcome_data["count"] > 0:
                outcome_data["avg_duration"] = round(outcome_data["avg_duration"] / outcome_data["count"], 2)
                outcome_data["avg_messages"] = round(outcome_data["avg_messages"] / outcome_data["count"], 2)
        
        return outcomes
    
    def _generate_workflow_recommendations(self, 
                                         success_factors: List[Dict[str, Any]],
                                         blocking_factors: List[Dict[str, Any]],
                                         efficiency_metrics: Dict[str, Any]) -> List[str]:
        """Generate workflow recommendations"""
        recommendations = []
        
        # Success rate recommendations
        if efficiency_metrics.get("success_rate", 0) < 0.7:
            recommendations.append(
                f"成功率が{efficiency_metrics['success_rate']*100:.1f}%と低いため、ワークフローの改善が必要です。"
                "より段階的なアプローチや事前の要件確認を強化してください。"
            )
        
        # Duration recommendations
        avg_duration = efficiency_metrics.get("average_duration_minutes", 0)
        if avg_duration > 60:
            recommendations.append(
                f"平均対話時間が{avg_duration:.1f}分と長いため、より効率的なアプローチを検討してください。"
                "事前準備や標準的なテンプレートの使用を検討してください。"
            )
        
        # Success factor recommendations
        if success_factors:
            top_success_factor = success_factors[0]
            recommendations.append(
                f"最も効果的な成功要因は'{top_success_factor['indicator']}'です（成功率: {top_success_factor['success_rate']*100:.1f}%）。"
                "このパターンを他の対話にも積極的に適用してください。"
            )
        
        # Blocking factor recommendations
        if blocking_factors:
            top_blocking_factor = blocking_factors[0]
            recommendations.append(
                f"最も頻繁な阻害要因は'{top_blocking_factor['indicator']}'です（失敗率: {top_blocking_factor['failure_rate']*100:.1f}%）。"
                "この要因を早期に検出し、対策を講じるプロセスを確立してください。"
            )
        
        # Efficiency comparison
        short_success = efficiency_metrics.get("short_conversation_success_rate", 0)
        long_success = efficiency_metrics.get("long_conversation_success_rate", 0)
        
        if short_success > long_success + 0.2:
            recommendations.append(
                f"短い対話の成功率（{short_success*100:.1f}%）が長い対話（{long_success*100:.1f}%）より高いため、"
                "より簡潔で焦点を絞ったアプローチを採用してください。"
            )
        elif long_success > short_success + 0.2:
            recommendations.append(
                f"長い対話の成功率（{long_success*100:.1f}%）が短い対話（{short_success*100:.1f}%）より高いため、"
                "より詳細な議論と段階的なアプローチが効果的です。"
            )
        
        if not recommendations:
            recommendations.append("ワークフローパターンは概ね良好です。現在のアプローチを継続してください。")
        
        return recommendations
    
    def _calculate_confidence(self, 
                            conversations: List[Conversation], 
                            conversation_analyses: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for workflow analysis"""
        if not conversations:
            return 0.0
        
        # Base confidence on number of conversations
        conversation_count_score = min(len(conversations) / 20, 1.0)  # Max at 20 conversations
        
        # Factor in outcome clarity
        outcome_clarity = 0.0
        defined_outcomes = len([c for c in conversations if c.outcome in ["success", "failure", "partial"]])
        if conversations:
            outcome_clarity = defined_outcomes / len(conversations)
        
        # Factor in signal strength
        signal_strength = 0.0
        total_signals = 0
        for analysis in conversation_analyses:
            total_signals += len(analysis["success_signals"]) + len(analysis["blocking_signals"])
        
        if conversation_analyses:
            signal_strength = min(total_signals / (len(conversation_analyses) * 5), 1.0)  # Max at 5 signals per conversation
        
        # Combine scores
        confidence = (conversation_count_score * 0.4 + 
                     outcome_clarity * 0.3 + 
                     signal_strength * 0.3)
        
        return round(confidence, 3)