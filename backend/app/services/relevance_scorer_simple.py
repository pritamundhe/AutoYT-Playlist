"""
Simplified relevance scorer using pre-trained embeddings
"""
import pickle
import numpy as np
from typing import List, Dict
from pathlib import Path



# Need to define the class structure for unpickling
class EmbeddingGenerator:
    """Wrapper for sentence embeddings with caching."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        # This will fail if libraries are missing, but that's expected
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except ImportError:
            self.model = None
        self.cache = {}
    
    def encode(self, texts, use_cache: bool = True):
        """Generate embeddings for text(s)."""
        if self.model is None:
            raise ImportError("sentence-transformers not installed")
            
        import numpy as np
        if isinstance(texts, str):
            texts = [texts]
            single = True
        else:
            single = False
        
        embeddings = []
        for text in texts:
            if use_cache and text in self.cache:
                embeddings.append(self.cache[text])
            else:
                emb = self.model.encode(text, convert_to_numpy=True)
                if use_cache:
                    self.cache[text] = emb
                embeddings.append(emb)
        
        embeddings = np.array(embeddings)
        return embeddings[0] if single else embeddings

import sys
sys.modules['__main__'].EmbeddingGenerator = EmbeddingGenerator

class RelevanceScorer:
    """Compute relevance using pre-trained embeddings from Kaggle"""
    
    def __init__(self, model_path: str = "ml_models/nlp/embeddings.pkl"):
        """Initialize with pre-trained embeddings"""
        self.model_path = Path(model_path)
        self.embeddings = None
        
        # Try to load pre-trained embeddings
        if self.model_path.exists():
            with open(self.model_path, 'rb') as f:
                self.embeddings = pickle.load(f)
            print(f"Loaded pre-trained embeddings from {model_path}")
        else:
            print(f"Warning: No embeddings found at {model_path}")
            print("Using simple text matching fallback")
    
    def compute_relevance(self, topic: Dict, video: Dict) -> float:
        """
        Compute relevance score between topic and video
        
        If embeddings available, use them. Otherwise, use keyword matching.
        """
        if self.embeddings:
            return self._compute_with_embeddings(topic, video)
        else:
            return self._compute_keyword_match(topic, video)
    
    def compute_batch_relevance(self, topic: Dict, videos: List[Dict]) -> List[float]:
        """Compute relevance scores for multiple videos"""
        return [self.compute_relevance(topic, video) for video in videos]
    
    def _compute_with_embeddings(self, topic: Dict, video: Dict) -> float:
        """Use pre-trained embeddings for similarity"""
        # Your Kaggle model should provide embedding vectors
        topic_text = self._build_topic_text(topic)
        video_text = self._build_video_text(video)
        
        # Get embeddings and compute cosine similarity
        topic_emb = self.embeddings.encode(topic_text)
        video_emb = self.embeddings.encode(video_text)
        
        # Cosine similarity
        similarity = np.dot(topic_emb, video_emb) / (
            np.linalg.norm(topic_emb) * np.linalg.norm(video_emb)
        )
        
        # Normalize to [0, 1]
        return float((similarity + 1) / 2)
    
    def _compute_keyword_match(self, topic: Dict, video: Dict) -> float:
        """
        Simple keyword matching fallback
        """
        # Get keywords from topic
        topic_keywords = set(topic.get('keywords', []))
        topic_title_words = set(topic.get('title', '').lower().split())
        topic_words = topic_keywords | topic_title_words
        
        # Get words from video
        video_title = video.get('title', '').lower()
        video_desc = video.get('description', '').lower()
        video_tags = [tag.lower() for tag in video.get('tags', [])]
        
        video_words = set(video_title.split()) | set(video_desc.split()) | set(video_tags)
        
        # Calculate overlap
        if not topic_words or not video_words:
            return 0.0
        
        overlap = len(topic_words & video_words)
        max_possible = len(topic_words)
        
        # Normalize to [0, 1]
        score = overlap / max_possible if max_possible > 0 else 0.0
        
        # Boost if title matches
        if any(keyword in video_title for keyword in topic_keywords):
            score = min(1.0, score * 1.5)
        
        return float(score)
    
    def _build_topic_text(self, topic: Dict) -> str:
        """Build text representation of topic"""
        parts = [topic.get('title', '')]
        keywords = topic.get('keywords', [])
        if keywords:
            parts.append(' '.join(keywords[:5]))
        return ' '.join(parts)
    
    def _build_video_text(self, video: Dict) -> str:
        """Build text representation of video"""
        parts = []
        
        # Title (most important)
        title = video.get('title', '')
        parts.extend([title] * 3)
        
        # Description
        description = video.get('description', '')[:500]
        parts.extend([description] * 2)
        
        # Tags
        tags = video.get('tags', [])
        if tags:
            parts.append(' '.join(tags[:10]))
        
        return ' '.join(parts)
