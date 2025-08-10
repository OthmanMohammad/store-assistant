"""
Document Management API
Handles document uploads, processing, and management
"""

import logging
import os
import tempfile
from typing import List, Dict, Any
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.services.document_service import document_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for responses
class DocumentStatus(BaseModel):
    id: int
    filename: str
    status: str
    total_chunks: int | None = None
    language: str | None = None
    is_active: bool
    created_at: str

class UploadResponse(BaseModel):
    message: str
    document_id: int | None = None
    filename: str
    status: str
    total_chunks: int | None = None
    language: str | None = None

class DocumentList(BaseModel):
    documents: List[DocumentStatus]
    total: int

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process a PDF document
    
    - **file**: PDF file to upload and process
    - Returns document processing status
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Validate file size (10MB limit)
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
        file_size = 0
        temp_content = await file.read()
        file_size = len(temp_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({file_size/1024/1024:.1f}MB) exceeds 10MB limit"
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(temp_content)
            temp_file_path = temp_file.name
        
        try:
            logger.info(f"📤 Processing uploaded file: {file.filename}")
            
            # Process document (this will take time for large files)
            result = await document_service.ingest_document(
                file_path=temp_file_path,
                filename=file.filename,
                db=db,
                additional_metadata={
                    "upload_source": "api",
                    "file_size": file_size
                }
            )
            
            return UploadResponse(
                message="Document processed successfully" if result["status"] == "completed" else f"Processing failed: {result.get('error', 'Unknown error')}",
                document_id=result.get("document_id"),
                filename=file.filename,
                status=result["status"],
                total_chunks=result.get("total_chunks"),
                language=result.get("language")
            )
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload processing failed: {str(e)}"
        )

@router.get("/", response_model=DocumentList)
async def list_documents(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    List all documents
    
    - **active_only**: Only return active (non-deleted) documents
    - Returns list of documents with their processing status
    """
    try:
        documents = await document_service.list_documents(db, active_only=active_only)
        
        return DocumentList(
            documents=[
                DocumentStatus(
                    id=doc["id"],
                    filename=doc["filename"],
                    status=doc["status"],
                    total_chunks=doc["total_chunks"],
                    language=doc["language"],
                    is_active=True,  # We only return active docs if active_only=True
                    created_at=doc["created_at"].isoformat()
                )
                for doc in documents
            ],
            total=len(documents)
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to list documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve documents: {str(e)}"
        )

@router.get("/{document_id}", response_model=DocumentStatus)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Get document status and information
    
    - **document_id**: ID of the document to retrieve
    - Returns detailed document information
    """
    try:
        doc_info = await document_service.get_document_status(document_id, db)
        
        if not doc_info:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )
        
        return DocumentStatus(
            id=doc_info["id"],
            filename=doc_info["filename"],
            status=doc_info["status"],
            total_chunks=doc_info["total_chunks"],
            language=doc_info["language"],
            is_active=doc_info["is_active"],
            created_at=doc_info["created_at"].isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve document: {str(e)}"
        )

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a document and all its vectors
    
    - **document_id**: ID of the document to delete
    - Removes document from vector database and marks as inactive
    """
    try:
        success = await document_service.delete_document(document_id, db)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Document not found or already deleted"
            )
        
        return {
            "message": f"Document {document_id} deleted successfully",
            "document_id": document_id,
            "status": "deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )

@router.get("/search/test")
async def test_search(
    query: str = "store hours",
    top_k: int = 3
):
    """
    Test vector search functionality
    
    - **query**: Search query text
    - **top_k**: Number of results to return
    - Returns similar document chunks
    """
    try:
        from app.services.vector_service import vector_service
        
        results = await vector_service.search_similar(query, top_k=top_k)
        
        return {
            "query": query,
            "results": results,
            "total_found": len(results)
        }
        
    except Exception as e:
        logger.error(f"❌ Search test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )