"""
Topic extraction API endpoints
"""
from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Document, Topic
from app.models.schemas import TopicResponse, TopicCreate
from app.services.document_processor import DocumentProcessor
from app.services.nlp_processor import TopicExtractor, HierarchyBuilder

router = APIRouter()
document_processor = DocumentProcessor()
topic_extractor = TopicExtractor()


@router.post("/extract-topics/{document_id}")
async def extract_topics(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    min_keywords: int = 3,
    max_depth: int = 3,
    db: Session = Depends(get_db)
):
    """
    Extract topics from document
    """
    # Get document
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.status == "processing":
        raise HTTPException(status_code=400, detail="Document is already being processed")
    
    # Update status
    document.status = "processing"
    db.commit()
    
    # Process in background
    background_tasks.add_task(
        process_document_topics,
        document_id,
        min_keywords,
        max_depth,
        db
    )
    
    return {"message": "Topic extraction started", "document_id": str(document_id)}


def process_document_topics(
    document_id: UUID,
    min_keywords: int,
    max_depth: int,
    db: Session
):
    """
    Background task to process document and extract topics
    """
    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            return
        
        # Process document
        text = document_processor.process(document.file_path, document.file_type)
        
        # Extract topics
        hierarchy = topic_extractor.extract_topics(text, max_depth, min_keywords)
        
        # Flatten hierarchy
        flat_topics = HierarchyBuilder.flatten_hierarchy(hierarchy)
        
        # Save topics to database
        topic_map = {}  # Map order_index to database ID
        
        for topic_data in flat_topics:
            parent_db_id = None
            if topic_data['parent_id'] is not None:
                parent_db_id = topic_map.get(topic_data['parent_id'])
            
            topic = Topic(
                document_id=document_id,
                title=topic_data['title'],
                level=topic_data['level'],
                parent_id=parent_db_id,
                keywords=topic_data['keywords'],
                order_index=topic_data['order_index']
            )
            
            db.add(topic)
            db.flush()  # Get ID without committing
            
            topic_map[topic_data['order_index']] = topic.id
        
        # Update document status
        document.status = "completed"
        db.commit()
    
    except Exception as e:
        # Update document with error
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = "failed"
            document.error_message = str(e)
            db.commit()


@router.get("/topics/{document_id}", response_model=List[TopicResponse])
async def get_topics(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all topics for a document
    """
    # Get document
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get root topics (level 1)
    topics = db.query(Topic).filter(
        Topic.document_id == document_id,
        Topic.parent_id == None
    ).order_by(Topic.order_index).all()
    
    # Build hierarchical response
    def build_topic_tree(topic):
        subtopics = db.query(Topic).filter(Topic.parent_id == topic.id).order_by(Topic.order_index).all()
        return TopicResponse(
            id=topic.id,
            document_id=topic.document_id,
            title=topic.title,
            level=topic.level,
            keywords=topic.keywords,
            description=topic.description,
            parent_id=topic.parent_id,
            order_index=topic.order_index,
            subtopics=[build_topic_tree(st) for st in subtopics]
        )
    
    return [build_topic_tree(topic) for topic in topics]


@router.get("/topics/{document_id}/flat", response_model=List[TopicResponse])
async def get_topics_flat(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all topics for a document (flat list)
    """
    topics = db.query(Topic).filter(
        Topic.document_id == document_id
    ).order_by(Topic.order_index).all()
    
    return topics
