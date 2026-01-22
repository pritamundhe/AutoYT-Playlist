"""
Evaluation metrics API endpoints
"""
from uuid import UUID
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import numpy as np

from app.core.database import get_db
from app.models.models import Playlist, PlaylistItem, EvaluationResult, UserFeedback
from app.models.schemas import EvaluationRequest, EvaluationResponse, FeedbackCreate, FeedbackResponse

router = APIRouter()


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_playlist(
    request: EvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate playlist using research metrics
    """
    # Get playlist
    playlist = db.query(Playlist).filter(Playlist.id == request.playlist_id).first()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Get playlist items
    items = db.query(PlaylistItem).filter(PlaylistItem.playlist_id == request.playlist_id).all()
    
    if not items:
        raise HTTPException(status_code=400, detail="Playlist has no items")
    
    # Compute metrics
    metrics = compute_evaluation_metrics(items, request.ground_truth)
    
    # Save or update evaluation result
    evaluation = db.query(EvaluationResult).filter(
        EvaluationResult.playlist_id == request.playlist_id
    ).first()
    
    if evaluation:
        # Update existing
        evaluation.precision_at_1 = metrics['precision_at_1']
        evaluation.precision_at_3 = metrics['precision_at_3']
        evaluation.precision_at_5 = metrics['precision_at_5']
        evaluation.precision_at_10 = metrics['precision_at_10']
        evaluation.ndcg = metrics['ndcg']
        evaluation.topic_coverage = metrics['topic_coverage']
        evaluation.metrics_json = metrics
    else:
        # Create new
        evaluation = EvaluationResult(
            playlist_id=request.playlist_id,
            precision_at_1=metrics['precision_at_1'],
            precision_at_3=metrics['precision_at_3'],
            precision_at_5=metrics['precision_at_5'],
            precision_at_10=metrics['precision_at_10'],
            ndcg=metrics['ndcg'],
            topic_coverage=metrics['topic_coverage'],
            metrics_json=metrics
        )
        db.add(evaluation)
    
    db.commit()
    db.refresh(evaluation)
    
    return evaluation


def compute_evaluation_metrics(items: List[PlaylistItem], ground_truth: List[Dict] = None) -> Dict:
    """
    Compute evaluation metrics
    
    Args:
        items: Playlist items
        ground_truth: Optional ground truth rankings
    
    Returns:
        Dictionary of metrics
    """
    # Group by topic
    topics = {}
    for item in items:
        if item.topic_id not in topics:
            topics[item.topic_id] = []
        topics[item.topic_id].append(item)
    
    # Compute Precision@K
    # For simplicity, assume relevance based on score threshold
    relevance_threshold = 0.6
    
    precision_at_k = {}
    for k in [1, 3, 5, 10]:
        precisions = []
        for topic_items in topics.values():
            top_k = sorted(topic_items, key=lambda x: x.rank)[:k]
            relevant = sum(1 for item in top_k if (item.relevance_score or 0) >= relevance_threshold)
            precisions.append(relevant / min(k, len(top_k)))
        precision_at_k[f'precision_at_{k}'] = np.mean(precisions) if precisions else 0.0
    
    # Compute nDCG
    ndcg_scores = []
    for topic_items in topics.values():
        sorted_items = sorted(topic_items, key=lambda x: x.rank)
        relevances = [item.relevance_score or 0 for item in sorted_items]
        ndcg = compute_ndcg(relevances)
        ndcg_scores.append(ndcg)
    
    avg_ndcg = np.mean(ndcg_scores) if ndcg_scores else 0.0
    
    # Topic coverage
    total_topics = len(topics)
    covered_topics = sum(1 for topic_items in topics.values() if any(
        (item.relevance_score or 0) >= relevance_threshold for item in topic_items
    ))
    topic_coverage = covered_topics / total_topics if total_topics > 0 else 0.0
    
    return {
        **precision_at_k,
        'ndcg': float(avg_ndcg),
        'topic_coverage': float(topic_coverage),
        'total_topics': total_topics,
        'covered_topics': covered_topics
    }


def compute_ndcg(relevances: List[float], k: int = None) -> float:
    """
    Compute Normalized Discounted Cumulative Gain
    
    Args:
        relevances: List of relevance scores
        k: Cutoff (None for all)
    
    Returns:
        nDCG score
    """
    if not relevances:
        return 0.0
    
    if k:
        relevances = relevances[:k]
    
    # DCG
    dcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(relevances))
    
    # IDCG (ideal DCG with perfect ranking)
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(ideal_relevances))
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    Submit user feedback for a playlist item
    """
    # Check if playlist item exists
    item = db.query(PlaylistItem).filter(PlaylistItem.id == feedback.playlist_item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Playlist item not found")
    
    # Create feedback
    user_feedback = UserFeedback(
        playlist_item_id=feedback.playlist_item_id,
        rating=feedback.rating,
        relevance_score=feedback.relevance_score,
        quality_score=feedback.quality_score,
        comment=feedback.comment
    )
    
    db.add(user_feedback)
    db.commit()
    db.refresh(user_feedback)
    
    return user_feedback


@router.get("/evaluation/{playlist_id}", response_model=EvaluationResponse)
async def get_evaluation(
    playlist_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get evaluation results for a playlist
    """
    evaluation = db.query(EvaluationResult).filter(
        EvaluationResult.playlist_id == playlist_id
    ).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    return evaluation
