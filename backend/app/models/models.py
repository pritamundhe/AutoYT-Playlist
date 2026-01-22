"""
Database models for the application
"""
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean, JSON, TypeDecorator
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(36), storing as stringified hex values.
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import UUID
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


class Document(Base):
    """Uploaded syllabus document"""
    __tablename__ = "documents"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx, txt
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="uploaded")  # uploaded, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Relationships
    topics = relationship("Topic", back_populates="document", cascade="all, delete-orphan")
    playlists = relationship("Playlist", back_populates="document", cascade="all, delete-orphan")


class Topic(Base):
    """Extracted topic from syllabus"""
    __tablename__ = "topics"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id = Column(GUID(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(512), nullable=False)
    level = Column(Integer, default=1)  # 1=unit, 2=topic, 3=subtopic
    parent_id = Column(GUID(), ForeignKey("topics.id", ondelete="CASCADE"), nullable=True)
    keywords = Column(JSON, default=list)  # List of keywords
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)
    
    # Relationships
    document = relationship("Document", back_populates="topics")
    parent = relationship("Topic", remote_side=[id], backref="subtopics")
    playlist_items = relationship("PlaylistItem", back_populates="topic")


class Video(Base):
    """Cached YouTube video metadata"""
    __tablename__ = "videos"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    youtube_id = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    channel_id = Column(String(50), nullable=False)
    channel_title = Column(String(255), nullable=False)
    
    # Metrics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    subscribers = Column(Integer, default=0)
    
    # Video details
    duration = Column(Integer, nullable=False)  # in seconds
    upload_date = Column(DateTime, nullable=False)
    category_id = Column(String(10), nullable=True)
    tags = Column(JSON, default=list)
    
    # Quality indicators
    has_captions = Column(Boolean, default=False)
    is_hd = Column(Boolean, default=False)
    
    # Metadata
    thumbnail_url = Column(String(512), nullable=True)
    cached_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    playlist_items = relationship("PlaylistItem", back_populates="video")


class Playlist(Base):
    """Generated playlist"""
    __tablename__ = "playlists"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id = Column(GUID(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Configuration
    weights = Column(JSON, nullable=False)  # Ranking weights used
    filters = Column(JSON, nullable=True)  # Filters applied
    videos_per_topic = Column(Integer, default=5)
    use_ml_ranking = Column(Boolean, default=True)
    
    # Metadata
    total_videos = Column(Integer, default=0)
    total_duration = Column(Integer, default=0)  # in seconds
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # YouTube export
    youtube_playlist_id = Column(String(50), nullable=True)
    youtube_url = Column(String(512), nullable=True)
    exported_at = Column(DateTime, nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="playlists")
    items = relationship("PlaylistItem", back_populates="playlist", cascade="all, delete-orphan")
    evaluation = relationship("EvaluationResult", back_populates="playlist", uselist=False, cascade="all, delete-orphan")


class PlaylistItem(Base):
    """Video in a playlist"""
    __tablename__ = "playlist_items"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    playlist_id = Column(GUID(), ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(GUID(), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(GUID(), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    
    # Ranking
    rank = Column(Integer, nullable=False)  # Position in topic
    score = Column(Float, nullable=False)  # Final ranking score
    relevance_score = Column(Float, nullable=True)
    
    # Relationships
    playlist = relationship("Playlist", back_populates="items")
    video = relationship("Video", back_populates="playlist_items")
    topic = relationship("Topic", back_populates="playlist_items")
    feedback = relationship("UserFeedback", back_populates="playlist_item", cascade="all, delete-orphan")


class UserFeedback(Base):
    """User feedback for ML training"""
    __tablename__ = "user_feedback"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    playlist_item_id = Column(GUID(), ForeignKey("playlist_items.id", ondelete="CASCADE"), nullable=False)
    
    # Ratings
    rating = Column(Integer, nullable=False)  # 1-5 scale
    relevance_score = Column(Integer, nullable=True)  # 1-5 scale
    quality_score = Column(Integer, nullable=True)  # 1-5 scale
    
    # Comments
    comment = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    playlist_item = relationship("PlaylistItem", back_populates="feedback")


class EvaluationResult(Base):
    """Evaluation metrics for a playlist"""
    __tablename__ = "evaluation_results"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    playlist_id = Column(GUID(), ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Metrics
    precision_at_1 = Column(Float, nullable=True)
    precision_at_3 = Column(Float, nullable=True)
    precision_at_5 = Column(Float, nullable=True)
    precision_at_10 = Column(Float, nullable=True)
    ndcg = Column(Float, nullable=True)
    topic_coverage = Column(Float, nullable=True)
    
    # User study
    user_satisfaction = Column(Float, nullable=True)
    time_saved = Column(Float, nullable=True)  # compared to manual search
    
    # Additional metrics
    metrics_json = Column(JSON, nullable=True)
    
    # Metadata
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    playlist = relationship("Playlist", back_populates="evaluation")
