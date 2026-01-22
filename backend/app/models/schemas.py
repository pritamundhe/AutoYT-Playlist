"""
Pydantic schemas for request/response validation
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID


# Document Schemas
class DocumentUpload(BaseModel):
    """Schema for document upload"""
    pass  # File will be handled separately


class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: UUID
    filename: str
    file_type: str
    file_size: int
    upload_date: datetime
    status: str
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


# Topic Schemas
class TopicBase(BaseModel):
    """Base topic schema"""
    title: str
    level: int = 1
    keywords: List[str] = []
    description: Optional[str] = None


class TopicCreate(TopicBase):
    """Schema for creating topic"""
    document_id: UUID
    parent_id: Optional[UUID] = None
    order_index: int = 0


class TopicResponse(TopicBase):
    """Schema for topic response"""
    id: UUID
    document_id: UUID
    parent_id: Optional[UUID] = None
    order_index: int
    subtopics: List['TopicResponse'] = []
    
    class Config:
        from_attributes = True


# Video Schemas
class VideoResponse(BaseModel):
    """Schema for video response"""
    id: UUID
    youtube_id: str
    title: str
    description: Optional[str] = None
    channel_title: str
    views: int
    likes: int
    duration: int
    upload_date: datetime
    thumbnail_url: Optional[str] = None
    has_captions: bool
    is_hd: bool
    
    class Config:
        from_attributes = True


# Playlist Schemas
class RankingWeights(BaseModel):
    """Schema for ranking weights"""
    views: float = Field(0.15, ge=0, le=1)
    likes: float = Field(0.20, ge=0, le=1)
    subscribers: float = Field(0.10, ge=0, le=1)
    relevance: float = Field(0.40, ge=0, le=1)
    recency: float = Field(0.10, ge=0, le=1)
    duration_penalty: float = Field(0.05, ge=0, le=1)
    
    @validator('*')
    def check_sum(cls, v, values):
        """Validate that weights sum to ~1.0"""
        if len(values) == 5:  # All fields set
            total = sum(values.values()) + v
            if not (0.95 <= total <= 1.05):
                raise ValueError(f"Weights must sum to 1.0, got {total}")
        return v


class PlaylistFilters(BaseModel):
    """Schema for playlist filters"""
    min_views: Optional[int] = None
    max_duration: Optional[int] = None  # in seconds
    min_duration: Optional[int] = None
    language: Optional[str] = "en"
    upload_date_after: Optional[datetime] = None
    has_captions: Optional[bool] = None
    is_hd: Optional[bool] = None


class PlaylistCreate(BaseModel):
    """Schema for creating playlist"""
    document_id: UUID
    name: str
    description: Optional[str] = None
    weights: RankingWeights = RankingWeights()
    filters: Optional[PlaylistFilters] = None
    videos_per_topic: int = Field(5, ge=1, le=20)
    use_ml_ranking: bool = True


class PlaylistItemResponse(BaseModel):
    """Schema for playlist item response"""
    id: UUID
    video: VideoResponse
    topic_title: str
    rank: int
    score: float
    relevance_score: Optional[float] = None
    
    class Config:
        from_attributes = True


class PlaylistResponse(BaseModel):
    """Schema for playlist response"""
    id: UUID
    document_id: UUID
    name: str
    description: Optional[str] = None
    total_videos: int
    total_duration: int
    created_date: datetime
    youtube_playlist_id: Optional[str] = None
    youtube_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class PlaylistDetailResponse(PlaylistResponse):
    """Schema for detailed playlist response with items"""
    items: List[PlaylistItemResponse] = []


# Export Schemas
class PlaylistExport(BaseModel):
    """Schema for playlist export"""
    playlist_id: UUID
    format: str = Field("youtube", pattern="^(youtube|json|csv)$")
    oauth_token: Optional[str] = None


class ExportResponse(BaseModel):
    """Schema for export response"""
    success: bool
    youtube_playlist_id: Optional[str] = None
    url: Optional[str] = None
    file_path: Optional[str] = None
    message: str


# Evaluation Schemas
class EvaluationRequest(BaseModel):
    """Schema for evaluation request"""
    playlist_id: UUID
    ground_truth: Optional[List[Dict[str, Any]]] = None


class EvaluationResponse(BaseModel):
    """Schema for evaluation response"""
    id: UUID
    playlist_id: UUID
    precision_at_1: Optional[float] = None
    precision_at_3: Optional[float] = None
    precision_at_5: Optional[float] = None
    precision_at_10: Optional[float] = None
    ndcg: Optional[float] = None
    topic_coverage: Optional[float] = None
    user_satisfaction: Optional[float] = None
    evaluated_at: datetime
    
    class Config:
        from_attributes = True


# Feedback Schemas
class FeedbackCreate(BaseModel):
    """Schema for creating feedback"""
    playlist_item_id: UUID
    rating: int = Field(..., ge=1, le=5)
    relevance_score: Optional[int] = Field(None, ge=1, le=5)
    quality_score: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Schema for feedback response"""
    id: UUID
    playlist_item_id: UUID
    rating: int
    relevance_score: Optional[int] = None
    quality_score: Optional[int] = None
    comment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Update forward references
TopicResponse.model_rebuild()
