"""Vector search functionality"""

from typing import List, Tuple, Optional
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
from ..models import Message


class VectorSearchEngine:
    """Vector search engine for semantic similarity"""
    
    def __init__(self, repository=None):
        """Initialize vector search engine
        
        Args:
            repository: Database repository for message queries
        """
        self.repository = repository
    
    def find_similar_messages(self, 
                            query_embedding: List[float], 
                            messages: List[Message],
                            threshold: float = 0.7, 
                            limit: int = 10) -> List[Tuple[Message, float]]:
        """Find similar messages using cosine similarity
        
        Args:
            query_embedding: Query embedding vector
            messages: List of messages to search
            threshold: Minimum similarity threshold
            limit: Maximum number of results
            
        Returns:
            List of (message, similarity_score) tuples
        """
        if not messages or not query_embedding:
            return []
        
        # Extract embeddings from messages
        message_embeddings = []
        valid_messages = []
        
        for message in messages:
            if message.embedding:
                message_embeddings.append(message.embedding)
                valid_messages.append(message)
        
        if not message_embeddings:
            return []
        
        # Calculate cosine similarity
        query_array = np.array(query_embedding).reshape(1, -1)
        message_array = np.array(message_embeddings)
        
        similarities = cosine_similarity(query_array, message_array)[0]
        
        # Filter by threshold and sort
        results = []
        for i, similarity in enumerate(similarities):
            if similarity >= threshold:
                results.append((valid_messages[i], float(similarity)))
        
        # Sort by similarity (descending) and limit
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def cluster_by_similarity(self, 
                            messages: List[Message], 
                            threshold: float = 0.8) -> List[List[Message]]:
        """Cluster messages by similarity
        
        Args:
            messages: List of messages to cluster
            threshold: Similarity threshold for clustering
            
        Returns:
            List of message clusters
        """
        if not messages:
            return []
        
        # Extract embeddings
        message_embeddings = []
        valid_messages = []
        
        for message in messages:
            if message.embedding:
                message_embeddings.append(message.embedding)
                valid_messages.append(message)
        
        if len(valid_messages) < 2:
            return [valid_messages] if valid_messages else []
        
        # Perform clustering
        embedding_array = np.array(message_embeddings)
        
        # Use agglomerative clustering with cosine distance
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=1.0 - threshold,  # Convert similarity to distance
            linkage='average',
            metric='cosine'
        )
        
        cluster_labels = clustering.fit_predict(embedding_array)
        
        # Group messages by cluster
        clusters = {}
        for i, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(valid_messages[i])
        
        return list(clusters.values())
    
    def calculate_cosine_similarity(self, 
                                  embedding1: List[float], 
                                  embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        array1 = np.array(embedding1).reshape(1, -1)
        array2 = np.array(embedding2).reshape(1, -1)
        
        similarity = cosine_similarity(array1, array2)[0][0]
        return float(similarity)
    
    def find_sentiment_similar_messages(self, 
                                      reference_embeddings: List[List[float]],
                                      messages: List[Message],
                                      threshold: float = 0.6) -> List[Tuple[Message, float]]:
        """Find messages similar to reference sentiment embeddings
        
        Args:
            reference_embeddings: List of reference embedding vectors
            messages: List of messages to search
            threshold: Minimum similarity threshold
            
        Returns:
            List of (message, max_similarity_score) tuples
        """
        if not reference_embeddings or not messages:
            return []
        
        results = []
        for message in messages:
            if not message.embedding:
                continue
            
            # Calculate similarity with all reference embeddings
            max_similarity = 0.0
            for ref_embedding in reference_embeddings:
                similarity = self.calculate_cosine_similarity(
                    message.embedding, ref_embedding
                )
                max_similarity = max(max_similarity, similarity)
            
            if max_similarity >= threshold:
                results.append((message, max_similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        return results