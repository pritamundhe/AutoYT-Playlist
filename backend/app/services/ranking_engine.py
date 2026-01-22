"""
Multi-criteria ranking engine with weighted scoring and ML-based ranking
"""
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import numpy as np

from app.core.config import settings


class WeightedRanker:
    """Rule-based weighted ranking"""
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize ranker with weights
        
        Args:
            weights: Dictionary of ranking weights
        """
        self.weights = weights or {
            'views': settings.WEIGHT_VIEWS,
            'likes': settings.WEIGHT_LIKES,
            'subscribers': settings.WEIGHT_SUBSCRIBERS,
            'relevance': settings.WEIGHT_RELEVANCE,
            'recency': settings.WEIGHT_RECENCY,
            'duration_penalty': settings.WEIGHT_DURATION_PENALTY,
        }
    
    def rank_videos(self, videos: List[Dict], relevance_scores: List[float]) -> List[Dict]:
        """
        Rank videos using weighted scoring
        
        Args:
            videos: List of video dictionaries
            relevance_scores: List of relevance scores
        
        Returns:
            Ranked list of videos with scores
        """
        if not videos:
            return []
        
        # Compute normalized metrics
        views_norm = self._normalize_log([v['views'] for v in videos])
        likes_norm = self._normalize_log([v['likes'] for v in videos])
        subs_norm = self._normalize_log([v['subscribers'] for v in videos])
        recency_scores = [self._compute_recency(v['upload_date']) for v in videos]
        duration_penalties = [self._compute_duration_penalty(v['duration']) for v in videos]
        
        # Compute final scores
        ranked_videos = []
        for i, video in enumerate(videos):
            score = (
                self.weights['views'] * views_norm[i] +
                self.weights['likes'] * likes_norm[i] +
                self.weights['subscribers'] * subs_norm[i] +
                self.weights['relevance'] * relevance_scores[i] +
                self.weights['recency'] * recency_scores[i] -
                self.weights['duration_penalty'] * duration_penalties[i]
            )
            
            ranked_videos.append({
                **video,
                'score': float(score),
                'relevance_score': float(relevance_scores[i])
            })
        
        # Sort by score descending
        ranked_videos.sort(key=lambda x: x['score'], reverse=True)
        
        return ranked_videos
    
    def _normalize_log(self, values: List[float]) -> List[float]:
        """
        Normalize values using log transformation
        
        Args:
            values: List of values
        
        Returns:
            Normalized values [0, 1]
        """
        if not values or max(values) == 0:
            return [0.0] * len(values)
        
        # Log transform
        log_values = [math.log(max(v, 1)) for v in values]
        
        # Min-max normalization
        min_val = min(log_values)
        max_val = max(log_values)
        
        if max_val == min_val:
            return [0.5] * len(values)
        
        normalized = [(v - min_val) / (max_val - min_val) for v in log_values]
        
        return normalized
    
    def _compute_recency(self, upload_date: datetime) -> float:
        """
        Compute recency score (newer = higher)
        
        Args:
            upload_date: Video upload date
        
        Returns:
            Recency score [0, 1]
        """
        # Days since upload
        days_old = (datetime.utcnow() - upload_date.replace(tzinfo=None)).days
        
        # Exponential decay: score = e^(-days/365)
        # Videos from last year get high scores
        score = math.exp(-days_old / 365)
        
        return float(score)
    
    def _compute_duration_penalty(self, duration: int) -> float:
        """
        Compute duration penalty (prefer 5-20 min videos)
        
        Args:
            duration: Video duration in seconds
        
        Returns:
            Penalty score [0, 1]
        """
        # Ideal range: 5-20 minutes (300-1200 seconds)
        ideal_min = 300
        ideal_max = 1200
        
        if ideal_min <= duration <= ideal_max:
            return 0.0  # No penalty
        elif duration < ideal_min:
            # Too short
            penalty = (ideal_min - duration) / ideal_min
        else:
            # Too long
            penalty = (duration - ideal_max) / (3600 - ideal_max)  # Max 1 hour
        
        return float(min(penalty, 1.0))


class XGBoostRanker:
    """
    Wrapper for XGBoost ranking model.
    Must match the class definition used in the training notebook.
    """
    
    def __init__(self, model, feature_names: List[str]):
        self.model = model
        self.feature_names = feature_names
    
    def rank(self, videos: List[Dict]) -> List[Dict]:
        """Rank videos using the trained model."""
        if not videos:
            return []
            
        import xgboost as xgb
        
        # Extract features
        features = []
        for video in videos:
            feature_vector = [video.get(feat, 0) for feat in self.feature_names]
            features.append(feature_vector)
        
        # Predict scores
        X = np.array(features)
        dmatrix = xgb.DMatrix(X)
        scores = self.model.predict(dmatrix)
        
        # Add scores to videos and sort
        for video, score in zip(videos, scores):
            video['ml_score'] = float(score)
        
        ranked_videos = sorted(videos, key=lambda x: x['ml_score'], reverse=True)
        return ranked_videos

import sys
# Hack to allow unpickling of XGBoostRanker if it was saved in __main__
sys.modules['__main__'].XGBoostRanker = XGBoostRanker


class MLRanker:
    """ML-based ranking using XGBoost"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize ML ranker
        
        Args:
            model_path: Path to trained model
        """
        import pickle
        from pathlib import Path
        
        self.model_path = Path(model_path or "ml_models/ranking/xgboost_ranker.pkl")
        self.model = None
        
        # Try to load pre-trained model
        if self.model_path.exists():
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print(f"Loaded ML ranking model from {self.model_path}")
            except Exception as e:
                print(f"Error loading ML model: {e}")
                print("Using weighted ranking fallback")
        else:
            print(f"Warning: No ML model found at {self.model_path}")
            print("Using weighted ranking fallback")
            
        self.fallback_ranker = WeightedRanker()
    
    def rank_videos(self, videos: List[Dict], relevance_scores: List[float]) -> List[Dict]:
        """
        Rank videos using ML model if available, else fallback
        """
        if self.model:
            try:
                # Pre-process videos to add relevance score and other derived features expected by model
                processed_videos = []
                for i, video in enumerate(videos):
                    v_copy = video.copy()
                    v_copy['relevance'] = relevance_scores[i]
                    
                    # Add derived features if missing (must match data generation in notebook)
                    # 'like_ratio', 'recency_score', 'duration_penalty', 'days_old'
                    if 'like_ratio' not in v_copy:
                        views = max(v_copy.get('views', 0), 1)
                        v_copy['like_ratio'] = v_copy.get('likes', 0) / views
                        
                    if 'days_old' not in v_copy:
                        upload_date = v_copy.get('upload_date')
                        if isinstance(upload_date, str):
                            # Parse if string (simplified)
                            pass 
                        elif isinstance(upload_date, datetime):
                            v_copy['days_old'] = (datetime.utcnow() - upload_date.replace(tzinfo=None)).days
                        else:
                            v_copy['days_old'] = 30 # Default
                            
                    if 'recency_score' not in v_copy:
                        v_copy['recency_score'] = 1 / (1 + v_copy.get('days_old', 30) / 365)
                        
                    if 'duration_penalty' not in v_copy:
                        dur = v_copy.get('duration', 0)
                        v_copy['duration_penalty'] = 1 if 600 <= dur <= 1800 else 0.5
                        
                    processed_videos.append(v_copy)
                
                return self.model.rank(processed_videos)
            except Exception as e:
                print(f"Error during ML ranking: {e}")
                return self.fallback_ranker.rank_videos(videos, relevance_scores)
        
        return self.fallback_ranker.rank_videos(videos, relevance_scores)


class RankingEnsemble:
    """Ensemble of weighted and ML ranking"""
    
    def __init__(self, weights: Optional[Dict[str, float]] = None, use_ml: bool = True):
        """
        Initialize ensemble ranker
        
        Args:
            weights: Ranking weights
            use_ml: Whether to use ML ranking
        """
        self.weighted_ranker = WeightedRanker(weights)
        self.ml_ranker = MLRanker() if use_ml else None
        self.use_ml = use_ml and settings.USE_ML_RANKING
    
    def rank_videos(self, videos: List[Dict], relevance_scores: List[float]) -> List[Dict]:
        """
        Rank videos using ensemble approach
        
        Args:
            videos: List of video dictionaries
            relevance_scores: List of relevance scores
        
        Returns:
            Ranked list of videos
        """
        if self.use_ml and self.ml_ranker:
            # Use ML ranking
            return self.ml_ranker.rank_videos(videos, relevance_scores)
        else:
            # Use weighted ranking
            return self.weighted_ranker.rank_videos(videos, relevance_scores)
