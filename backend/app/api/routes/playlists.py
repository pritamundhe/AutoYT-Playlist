"""
Playlist generation and export API endpoints
"""
import os
from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Document, Topic, Playlist, PlaylistItem, Video
from app.models.schemas import (
    PlaylistCreate, PlaylistResponse, PlaylistDetailResponse,
    PlaylistExport, ExportResponse, PlaylistItemResponse, VideoResponse
)
from app.services.playlist_generator import PlaylistGenerator

router = APIRouter()
playlist_generator = PlaylistGenerator()


@router.post("/generate-playlist", response_model=PlaylistResponse)
async def generate_playlist(
    request: PlaylistCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate playlist from document topics
    """
    # Get document
    document = db.query(Document).filter(Document.id == request.document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.status != "completed":
        raise HTTPException(status_code=400, detail="Document processing not completed")
    
    # Get topics
    topics = db.query(Topic).filter(Topic.document_id == request.document_id).all()
    
    if not topics:
        raise HTTPException(status_code=400, detail="No topics found for document")
    
    # Create playlist record
    playlist = Playlist(
        document_id=request.document_id,
        name=request.name,
        description=request.description,
        weights=request.weights.dict(),
        filters=request.filters.dict() if request.filters else None,
        videos_per_topic=request.videos_per_topic,
        use_ml_ranking=request.use_ml_ranking
    )
    
    db.add(playlist)
    db.commit()
    db.refresh(playlist)
    
    # Convert topics to dictionaries eagerly to avoid DetachedInstanceError in background task
    topic_dicts = [
        {
            'id': str(topic.id),
            'title': topic.title,
            'keywords': topic.keywords,
            'level': topic.level
        }
        for topic in topics
    ]
    
    # Generate playlist in background
    background_tasks.add_task(
        process_playlist_generation,
        playlist.id,
        topic_dicts,
        request.weights.dict(),
        request.filters.dict() if request.filters else None,
        request.videos_per_topic,
        request.use_ml_ranking,
        db
    )
    
    return playlist


def process_playlist_generation(
    playlist_id: UUID,
    topic_dicts: List[dict],
    weights: dict,
    filters: dict,
    videos_per_topic: int,
    use_ml_ranking: bool,
    db: Session
):
    """
    Background task to generate playlist
    """
    try:
        # Generate playlist
        result = playlist_generator.generate_playlist(
            topic_dicts,
            weights=weights,
            filters=filters,
            videos_per_topic=videos_per_topic,
            use_ml_ranking=use_ml_ranking
        )
        
        # Save videos and playlist items
        playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
        
        for item_data in result['items']:
            video_data = item_data['video']
            
            # Check if video exists
            video = db.query(Video).filter(Video.youtube_id == video_data['youtube_id']).first()
            
            if not video:
                # Create new video record
                video = Video(
                    youtube_id=video_data['youtube_id'],
                    title=video_data['title'],
                    description=video_data.get('description'),
                    channel_id=video_data['channel_id'],
                    channel_title=video_data['channel_title'],
                    views=video_data['views'],
                    likes=video_data['likes'],
                    comments=video_data.get('comments', 0),
                    subscribers=video_data['subscribers'],
                    duration=video_data['duration'],
                    upload_date=video_data['upload_date'],
                    category_id=video_data.get('category_id'),
                    tags=video_data.get('tags', []),
                    has_captions=video_data.get('has_captions', False),
                    is_hd=video_data.get('is_hd', False),
                    thumbnail_url=video_data.get('thumbnail_url')
                )
                db.add(video)
                db.flush()
            
            # Create playlist item
            playlist_item = PlaylistItem(
                playlist_id=playlist_id,
                video_id=video.id,
                topic_id=item_data['topic_id'],
                rank=item_data['rank'],
                score=item_data['score'],
                relevance_score=item_data.get('relevance_score')
            )
            db.add(playlist_item)
        
        # Update playlist metadata
        playlist.total_videos = result['total_videos']
        playlist.total_duration = result['total_duration']
        
        db.commit()
    
    except Exception as e:
        print(f"Error generating playlist: {e}")


@router.get("/playlists/{playlist_id}", response_model=PlaylistDetailResponse)
async def get_playlist(
    playlist_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get playlist with all videos
    """
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Get playlist items with videos and topics
    items = db.query(PlaylistItem).filter(PlaylistItem.playlist_id == playlist_id).all()
    
    items_response = []
    for item in items:
        video = db.query(Video).filter(Video.id == item.video_id).first()
        topic = db.query(Topic).filter(Topic.id == item.topic_id).first()
        
        items_response.append(PlaylistItemResponse(
            id=item.id,
            video=VideoResponse.from_orm(video),
            topic_title=topic.title if topic else "Unknown",
            rank=item.rank,
            score=item.score,
            relevance_score=item.relevance_score
        ))
    
    return PlaylistDetailResponse(
        **playlist.__dict__,
        items=items_response
    )


@router.post("/export-playlist", response_model=ExportResponse)
async def export_playlist(
    request: PlaylistExport,
    db: Session = Depends(get_db)
):
    """
    Export playlist to various formats
    """
    # Get playlist
    playlist = db.query(Playlist).filter(Playlist.id == request.playlist_id).first()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Get playlist items
    items = db.query(PlaylistItem).filter(PlaylistItem.playlist_id == request.playlist_id).all()
    
    # Build playlist data
    playlist_data = {
        'items': [],
        'total_videos': playlist.total_videos,
        'total_duration': playlist.total_duration,
        'topics_covered': len(set(item.topic_id for item in items))
    }
    
    for item in items:
        video = db.query(Video).filter(Video.id == item.video_id).first()
        topic = db.query(Topic).filter(Topic.id == item.topic_id).first()
        
        playlist_data['items'].append({
            'topic_id': item.topic_id,
            'topic_title': topic.title if topic else "Unknown",
            'video': video.__dict__,
            'rank': item.rank,
            'score': item.score,
            'relevance_score': item.relevance_score
        })
    
    # Export based on format
    export_dir = "data/exports"
    os.makedirs(export_dir, exist_ok=True)
    
    if request.format == "json":
        file_path = os.path.join(export_dir, f"playlist_{playlist.id}.json")
        playlist_generator.export_to_json(playlist_data, file_path)
        
        return ExportResponse(
            success=True,
            file_path=file_path,
            message="Playlist exported to JSON"
        )
    
    elif request.format == "csv":
        file_path = os.path.join(export_dir, f"playlist_{playlist.id}.csv")
        playlist_generator.export_to_csv(playlist_data, file_path)
        
        return ExportResponse(
            success=True,
            file_path=file_path,
            message="Playlist exported to CSV"
        )
    
    elif request.format == "youtube":
        # TODO: Implement YouTube OAuth and playlist creation
        return ExportResponse(
            success=False,
            message="YouTube export requires OAuth implementation"
        )
    
    else:
        raise HTTPException(status_code=400, detail="Invalid export format")


@router.get("/playlists", response_model=List[PlaylistResponse])
async def list_playlists(
    document_id: UUID = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all playlists
    """
    query = db.query(Playlist)
    
    if document_id:
        query = query.filter(Playlist.document_id == document_id)
    
    playlists = query.offset(skip).limit(limit).all()
    return playlists
