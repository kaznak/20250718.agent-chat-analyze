"""Feedback analyzer using vector embeddings"""

from typing import List, Dict, Any
from datetime import datetime
from ..models import Conversation, Message, AnalysisResult
from ..embeddings import BaseEmbedding, VectorSearchEngine
from .base import BaseAnalyzer


class FeedbackAnalyzer(BaseAnalyzer):
    """Analyzer for user feedback patterns using vector embeddings"""
    
    def __init__(self, embedding_model: BaseEmbedding):
        """Initialize feedback analyzer
        
        Args:
            embedding_model: Embedding model for text vectorization
        """
        self.embedding_model = embedding_model
        self.vector_search = VectorSearchEngine()
        
        # Reference sentiment embeddings
        self.positive_references = [
            "素晴らしい実装です。完璧です。",
            "ありがとうございます。とても助かります。",
            "Great implementation! Perfect solution.",
            "Thank you so much. Very helpful."
        ]
        
        self.negative_references = [
            "これは不十分です。改善が必要です。",
            "問題があります。役に立ちません。",
            "This is insufficient. Needs improvement.",
            "There are problems. Not helpful."
        ]
        
        self.request_references = [
            "修正してください。追加してください。",
            "もっと詳しく説明してください。",
            "Please fix this. Add more features.",
            "Could you explain in more detail?"
        ]
    
    def analyze(self, conversations: List[Conversation]) -> AnalysisResult:
        """Analyze feedback patterns using vector embeddings
        
        Args:
            conversations: List of conversations to analyze
            
        Returns:
            Analysis result with feedback patterns
        """
        # Extract all user messages
        user_messages = []
        for conversation in conversations:
            for message in conversation.messages:
                if message.role == "user":
                    user_messages.append(message)
        
        if not user_messages:
            return AnalysisResult(
                conversation_id="all",
                analysis_type="feedback",
                findings={
                    "total_messages": 0,
                    "sentiment_distribution": {},
                    "feedback_clusters": [],
                    "temporal_patterns": {}
                },
                recommendations=[],
                confidence=0.0
            )
        
        # Generate embeddings for messages if not already present
        self._ensure_embeddings(user_messages)
        
        # Generate reference embeddings
        positive_embeddings = self.embedding_model.encode(self.positive_references)
        negative_embeddings = self.embedding_model.encode(self.negative_references)
        request_embeddings = self.embedding_model.encode(self.request_references)
        
        # Analyze sentiment using vector similarity
        sentiment_analysis = self._analyze_sentiment_with_vectors(
            user_messages, positive_embeddings, negative_embeddings, request_embeddings
        )
        
        # Cluster similar feedback
        feedback_clusters = self._cluster_feedback(user_messages)
        
        # Analyze temporal patterns
        temporal_patterns = self._analyze_temporal_patterns(user_messages, sentiment_analysis)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            sentiment_analysis, feedback_clusters, temporal_patterns
        )
        
        findings = {
            "total_messages": len(user_messages),
            "sentiment_distribution": sentiment_analysis["distribution"],
            "feedback_clusters": feedback_clusters,
            "temporal_patterns": temporal_patterns,
            "detailed_sentiment": sentiment_analysis["detailed"]
        }
        
        confidence = self._calculate_confidence(user_messages, sentiment_analysis)
        
        return AnalysisResult(
            conversation_id="all",
            analysis_type="feedback",
            findings=findings,
            recommendations=recommendations,
            confidence=confidence
        )
    
    def _ensure_embeddings(self, messages: List[Message]) -> None:
        """Ensure all messages have embeddings"""
        for message in messages:
            if message.embedding is None:
                message.embedding = self.embedding_model.encode_single(message.content)
    
    def _analyze_sentiment_with_vectors(self, 
                                      messages: List[Message],
                                      positive_embeddings: List[List[float]],
                                      negative_embeddings: List[List[float]],
                                      request_embeddings: List[List[float]]) -> Dict[str, Any]:
        """Analyze sentiment using vector similarity"""
        sentiment_scores = []
        sentiment_counts = {"positive": 0, "negative": 0, "request": 0, "neutral": 0}
        
        for message in messages:
            if not message.embedding:
                continue
            
            # Calculate max similarity with each sentiment category
            pos_similarity = max(
                self.vector_search.calculate_cosine_similarity(message.embedding, ref_emb)
                for ref_emb in positive_embeddings
            )
            
            neg_similarity = max(
                self.vector_search.calculate_cosine_similarity(message.embedding, ref_emb)
                for ref_emb in negative_embeddings
            )
            
            req_similarity = max(
                self.vector_search.calculate_cosine_similarity(message.embedding, ref_emb)
                for ref_emb in request_embeddings
            )
            
            # Determine sentiment based on highest similarity
            max_similarity = max(pos_similarity, neg_similarity, req_similarity)
            
            if max_similarity < 0.3:  # Low threshold for all sentiments
                sentiment = "neutral"
            elif pos_similarity == max_similarity:
                sentiment = "positive"
            elif neg_similarity == max_similarity:
                sentiment = "negative"
            else:
                sentiment = "request"
            
            sentiment_scores.append({
                "message_content": message.content[:100] + "..." if len(message.content) > 100 else message.content,
                "sentiment": sentiment,
                "positive_score": pos_similarity,
                "negative_score": neg_similarity,
                "request_score": req_similarity,
                "timestamp": message.timestamp.isoformat()
            })
            
            sentiment_counts[sentiment] += 1
        
        # Calculate distribution percentages
        total = len(sentiment_scores)
        distribution = {}
        if total > 0:
            for sentiment, count in sentiment_counts.items():
                distribution[sentiment] = round((count / total) * 100, 2)
        
        return {
            "detailed": sentiment_scores,
            "distribution": distribution,
            "counts": sentiment_counts
        }
    
    def _cluster_feedback(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Cluster similar feedback messages"""
        if not messages:
            return []
        
        # Use vector search to cluster messages
        clusters = self.vector_search.cluster_by_similarity(messages, threshold=0.75)
        
        cluster_info = []
        for i, cluster in enumerate(clusters):
            if len(cluster) < 2:  # Skip single-message clusters
                continue
            
            cluster_info.append({
                "cluster_id": i,
                "message_count": len(cluster),
                "sample_messages": [
                    {
                        "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                        "timestamp": msg.timestamp.isoformat()
                    }
                    for msg in cluster[:3]  # Show first 3 messages
                ],
                "common_themes": self._extract_common_themes(cluster)
            })
        
        return cluster_info
    
    def _extract_common_themes(self, messages: List[Message]) -> List[str]:
        """Extract common themes from a cluster of messages"""
        # Simple keyword extraction based on frequency
        all_words = []
        for message in messages:
            words = message.content.lower().split()
            all_words.extend(words)
        
        # Count word frequency
        word_counts = {}
        for word in all_words:
            if len(word) > 2:  # Skip short words
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Return top 5 most frequent words
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:5] if count > 1]
    
    def _analyze_temporal_patterns(self, 
                                 messages: List[Message], 
                                 sentiment_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze temporal patterns in feedback"""
        if not messages:
            return {}
        
        # Sort messages by timestamp
        sorted_messages = sorted(messages, key=lambda x: x.timestamp)
        
        # Group by hour of day
        hourly_sentiment = {}
        for i, message in enumerate(sorted_messages):
            hour = message.timestamp.hour
            if hour not in hourly_sentiment:
                hourly_sentiment[hour] = {"positive": 0, "negative": 0, "neutral": 0, "request": 0}
            
            # Get sentiment for this message
            if i < len(sentiment_analysis["detailed"]):
                sentiment = sentiment_analysis["detailed"][i]["sentiment"]
                hourly_sentiment[hour][sentiment] += 1
        
        # Calculate sentiment trend over time
        sentiment_trend = []
        window_size = max(1, len(sorted_messages) // 10)  # 10 time windows
        
        for i in range(0, len(sorted_messages), window_size):
            window_messages = sorted_messages[i:i+window_size]
            window_sentiment = {"positive": 0, "negative": 0, "neutral": 0, "request": 0}
            
            for j, message in enumerate(window_messages):
                detail_index = i + j
                if detail_index < len(sentiment_analysis["detailed"]):
                    sentiment = sentiment_analysis["detailed"][detail_index]["sentiment"]
                    window_sentiment[sentiment] += 1
            
            sentiment_trend.append({
                "start_time": window_messages[0].timestamp.isoformat(),
                "end_time": window_messages[-1].timestamp.isoformat(),
                "sentiment_counts": window_sentiment
            })
        
        return {
            "hourly_patterns": hourly_sentiment,
            "sentiment_trend": sentiment_trend,
            "first_message_time": sorted_messages[0].timestamp.isoformat(),
            "last_message_time": sorted_messages[-1].timestamp.isoformat()
        }
    
    def _generate_recommendations(self, 
                                sentiment_analysis: Dict[str, Any],
                                feedback_clusters: List[Dict[str, Any]],
                                temporal_patterns: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Sentiment-based recommendations
        distribution = sentiment_analysis["distribution"]
        
        if distribution.get("negative", 0) > 30:
            recommendations.append(
                "ネガティブフィードバックが多い（{}%）ため、ユーザーの期待に応えられていない可能性があります。"
                "より具体的な要求確認や段階的な実装を検討してください。".format(distribution["negative"])
            )
        
        if distribution.get("positive", 0) > 60:
            recommendations.append(
                "ポジティブフィードバックが多い（{}%）ため、現在のアプローチは効果的です。"
                "この成功パターンを他の類似タスクにも適用してください。".format(distribution["positive"])
            )
        
        if distribution.get("request", 0) > 40:
            recommendations.append(
                "リクエストが多い（{}%）ため、初期提案の完成度を高めることを検討してください。"
                "ユーザーの要求を事前に予測し、より包括的なソリューションを提供してください。".format(distribution["request"])
            )
        
        # Cluster-based recommendations
        large_clusters = [c for c in feedback_clusters if c["message_count"] > 3]
        if large_clusters:
            recommendations.append(
                "{}個の大きなフィードバッククラスターが見つかりました。"
                "これらの共通テーマに対する標準的な対応パターンを作成することを検討してください。".format(len(large_clusters))
            )
        
        # Temporal pattern recommendations
        if temporal_patterns and "sentiment_trend" in temporal_patterns:
            trend = temporal_patterns["sentiment_trend"]
            if len(trend) > 3:
                early_negative = sum(t["sentiment_counts"]["negative"] for t in trend[:len(trend)//2])
                late_negative = sum(t["sentiment_counts"]["negative"] for t in trend[len(trend)//2:])
                
                if late_negative > early_negative * 1.5:
                    recommendations.append(
                        "時間の経過とともにネガティブフィードバックが増加する傾向があります。"
                        "長期的な対話では、より頻繁な確認と調整が必要かもしれません。"
                    )
        
        if not recommendations:
            recommendations.append(
                "フィードバックパターンは概ね良好です。現在のアプローチを継続してください。"
            )
        
        return recommendations
    
    def _calculate_confidence(self, 
                            messages: List[Message], 
                            sentiment_analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for the analysis"""
        if not messages:
            return 0.0
        
        # Base confidence on number of messages
        message_count_score = min(len(messages) / 50, 1.0)  # Max at 50 messages
        
        # Factor in embedding quality (how many messages have embeddings)
        embedding_count = sum(1 for msg in messages if msg.embedding)
        embedding_score = embedding_count / len(messages) if messages else 0
        
        # Factor in sentiment clarity (how clear the sentiment signals are)
        sentiment_clarity = 0.0
        if sentiment_analysis["detailed"]:
            total_max_scores = 0
            for detail in sentiment_analysis["detailed"]:
                max_score = max(
                    detail["positive_score"],
                    detail["negative_score"],
                    detail["request_score"]
                )
                total_max_scores += max_score
            
            sentiment_clarity = total_max_scores / len(sentiment_analysis["detailed"])
        
        # Combine scores
        confidence = (message_count_score * 0.3 + 
                     embedding_score * 0.4 + 
                     sentiment_clarity * 0.3)
        
        return round(confidence, 3)