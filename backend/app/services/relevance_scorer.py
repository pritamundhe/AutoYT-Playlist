"""
Relevance scoring using semantic similarity
"""
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class RelevanceScorer:
    """Compute semantic relevance between topics and videos"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize sentence transformer model"""
        self.model = SentenceTransformer(model_name)
    
    def compute_relevance(self, topic: Dict, video: Dict) -> float:
        """
        Compute relevance score between topic and video
        
        Args:
            topic: Topic dictionary with title and keywords
            video: Video dictionary with title, description, tags
        
        Returns:
            Relevance score [0, 1]
        """
        # Build topic text
        topic_text = self._build_topic_text(topic)
        
        # Build video text (weighted combination)
        video_text = self._build_video_text(video)
        
        # Generate embeddings
        topic_embedding = self.model.encode([topic_text])[0]
        video_embedding = self.model.encode([video_text])[0]
        
        # Compute cosine similarity
        similarity = cosine_similarity(
            topic_embedding.reshape(1, -1),
            video_embedding.reshape(1, -1)
        )[0][0]
        
        # Normalize to [0, 1]
        relevance = (similarity + 1) / 2
        
        return float(relevance)
    
    def compute_batch_relevance(self, topic: Dict, videos: List[Dict]) -> List[float]:
        """
        Compute relevance scores for multiple videos
        
        Args:
            topic: Topic dictionary
            videos: List of video dictionaries
        
        Returns:
            List of relevance scores
        """
        if not videos:
            return []
        
        # Build topic text
        topic_text = self._build_topic_text(topic)
        topic_embedding = self.model.encode([topic_text])[0]
        
        # Build video texts and embeddings
        video_texts = [self._build_video_text(video) for video in videos]
        video_embeddings = self.model.encode(video_texts)
        
        # Compute similarities
        similarities = cosine_similarity(
            topic_embedding.reshape(1, -1),
            video_embeddings
        )[0]
        
        # Normalize to [0, 1]
        relevances = [(sim + 1) / 2 for sim in similarities]
        
        return relevances
    
    def _build_topic_text(self, topic: Dict) -> str:
        """
        Build text representation of topic
        
        Args:
            topic: Topic dictionary
        
        Returns:
            Combined text
        """
        parts = [topic.get('title', '')]
        
        # Add keywords
        keywords = topic.get('keywords', [])
        if keywords:
            parts.append(' '.join(keywords[:5]))
        
        # Add description if available
        if topic.get('description'):
            parts.append(topic['description'])
        
        return ' '.join(parts)
    
    def _build_video_text(self, video: Dict) -> str:
        """
        Build weighted text representation of video
        
        Args:
            video: Video dictionary
        
        Returns:
            Combined text with weighting
        """
        parts = []
        
        # Title (weight: 0.5) - repeat for emphasis
        title = video.get('title', '')
        parts.extend([title] * 3)
        
        # Description (weight: 0.3)
        description = video.get('description', '')[:500]  # Limit length
        parts.extend([description] * 2)
        
        # Tags (weight: 0.2)
        tags = video.get('tags', [])
        if tags:
            parts.append(' '.join(tags[:10]))
        
        return ' '.join(parts)
