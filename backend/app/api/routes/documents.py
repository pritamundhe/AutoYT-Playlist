"""
Document upload and processing API endpoints
"""
import os
import shutil
from uuid import UUID
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.models import Document
from app.models.schemas import DocumentResponse
from app.services.document_processor import DocumentProcessor

router = APIRouter()
document_processor = DocumentProcessor()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a syllabus document (PDF, DOCX, or TXT)
    """
    # Validate file type
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Create upload directory
    upload_dir = "data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Validate file
    try:
        document_processor.validate_file(file_path, max_size_mb=settings.MAX_UPLOAD_SIZE // (1024 * 1024))
    except ValueError as e:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create document record
    document = Document(
        filename=file.filename,
        file_type=file_ext,
        file_path=file_path,
        file_size=file_size,
        status="uploaded"
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return document


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get document by ID
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all documents
    """
    documents = db.query(Document).offset(skip).limit(limit).all()
    return documents


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete document and associated data
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Delete database record (cascade will delete topics and playlists)
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}
