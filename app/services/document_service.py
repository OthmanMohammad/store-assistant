"""
Document Ingestion Service
Handles complete document ingestion pipeline: PDF → Chunks → Embeddings → Vector Storage
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.services.vector_service import vector_service
from app.utils.document_processor import document_processor
from app.utils.embeddings import generate_chunk_id, prepare_vector_for_upsert

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self):
        self.processor = document_processor
        self.vector_service = vector_service
    
    async def ingest_document(
        self, 
        file_path: str, 
        filename: str,
        db: Session,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete document ingestion pipeline
        
        Args:
            file_path: Path to the document file
            filename: Original filename
            db: Database session
            additional_metadata: Extra metadata to include
            
        Returns:
            Ingestion results
        """
        doc_record = None
        try:
            logger.info(f"🚀 Starting document ingestion: {filename}")
            
            # Create database record
            doc_record = Document(
                filename=filename,
                source_path=file_path,
                status="processing"
            )
            db.add(doc_record)
            db.commit()
            db.refresh(doc_record)
            
            # Process document (extract text and chunk)
            processing_result = self.processor.process_document(file_path, filename)
            
            if processing_result["status"] == "failed":
                # Update database record
                doc_record.status = "failed"
                db.commit()
                return processing_result
            
            # Update document record with processing results
            doc_record.total_chunks = processing_result["total_chunks"]
            doc_record.language = processing_result["language"]
            
            # Generate embeddings and store vectors
            if processing_result["chunks"]:
                await self._process_chunks(
                    processing_result["chunks"], 
                    doc_record.id,
                    additional_metadata
                )
            
            # Mark as completed
            doc_record.status = "completed"
            db.commit()
            
            result = {
                "document_id": doc_record.id,
                "filename": filename,
                "status": "completed",
                "total_chunks": processing_result["total_chunks"],
                "language": processing_result["language"],
                "total_words": processing_result["total_words"]
            }
            
            logger.info(f"✅ Document ingestion completed: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Document ingestion failed: {str(e)}")
            
            # Update database record if it exists
            if doc_record:
                doc_record.status = "failed"
                db.commit()
            
            return {
                "filename": filename,
                "status": "failed",
                "error": str(e)
            }
    
    async def _process_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        document_id: int,
        additional_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Process chunks: generate embeddings and store in vector database
        
        Args:
            chunks: List of text chunks with metadata
            document_id: Database document ID
            additional_metadata: Extra metadata to include
        """
        try:
            logger.info(f"🧠 Processing {len(chunks)} chunks for embeddings")
            
            # Extract texts for embedding
            chunk_texts = [chunk["text"] for chunk in chunks]
            
            # Generate embeddings in batches
            batch_size = 50  # Process 50 chunks at a time
            all_vectors = []
            
            for i in range(0, len(chunk_texts), batch_size):
                batch_texts = chunk_texts[i:i + batch_size]
                batch_chunks = chunks[i:i + batch_size]
                
                logger.info(f"⚡ Generating embeddings for batch {i//batch_size + 1}")
                
                # Generate embeddings for this batch
                embeddings = await self.vector_service.get_embeddings(batch_texts)
                
                # Prepare vectors for upsert
                for j, (chunk, embedding) in enumerate(zip(batch_chunks, embeddings)):
                    chunk_index = i + j
                    source = chunk["metadata"]["source"]
                    
                    # Generate unique chunk ID
                    chunk_id = generate_chunk_id(
                        chunk["text"], 
                        source, 
                        chunk_index
                    )
                    
                    # Prepare metadata
                    metadata = {
                        **chunk["metadata"],
                        "document_id": document_id,
                        **(additional_metadata or {})
                    }
                    
                    # Create vector for upsert
                    vector = prepare_vector_for_upsert(
                        chunk_id=chunk_id,
                        embedding=embedding,
                        text=chunk["text"],
                        source=source,
                        chunk_index=chunk_index,
                        language=chunk["metadata"]["language"],
                        additional_metadata=metadata
                    )
                    
                    all_vectors.append(vector)
            
            # Upsert all vectors to Pinecone
            logger.info(f"🚀 Storing {len(all_vectors)} vectors in Pinecone")
            await self.vector_service.upsert_vectors(all_vectors)
            
            logger.info(f"✅ Successfully processed {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"❌ Failed to process chunks: {str(e)}")
            raise
    
    async def delete_document(self, document_id: int, db: Session) -> bool:
        """
        Delete a document and all its vectors
        
        Args:
            document_id: Database document ID
            db: Database session
            
        Returns:
            True if successful
        """
        try:
            # Get document record
            doc_record = db.query(Document).filter(Document.id == document_id).first()
            if not doc_record:
                logger.warning(f"⚠️ Document {document_id} not found")
                return False
            
            logger.info(f"🗑️ Deleting document: {doc_record.filename}")
            
            # Delete vectors from Pinecone
            # We need to search for vectors with this document_id
            search_results = await self.vector_service.search_similar(
                query_text="dummy",  # We just need to filter by metadata
                top_k=10000,  # Large number to get all chunks
                filter_dict={"document_id": document_id}
            )
            
            if search_results:
                vector_ids = [result["id"] for result in search_results]
                await self.vector_service.delete_vectors(vector_ids)
                logger.info(f"🗑️ Deleted {len(vector_ids)} vectors from Pinecone")
            
            # Mark document as inactive (soft delete)
            doc_record.is_active = False
            doc_record.status = "deleted"
            db.commit()
            
            logger.info(f"✅ Document {document_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete document: {str(e)}")
            return False
    
    async def get_document_status(self, document_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """
        Get document processing status and metadata
        
        Args:
            document_id: Database document ID
            db: Database session
            
        Returns:
            Document status information
        """
        try:
            doc_record = db.query(Document).filter(Document.id == document_id).first()
            if not doc_record:
                return None
            
            return {
                "id": doc_record.id,
                "filename": doc_record.filename,
                "status": doc_record.status,
                "total_chunks": doc_record.total_chunks,
                "language": doc_record.language,
                "is_active": doc_record.is_active,
                "created_at": doc_record.created_at,
                "updated_at": doc_record.updated_at
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get document status: {str(e)}")
            return None
    
    async def list_documents(self, db: Session, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        List all documents
        
        Args:
            db: Database session
            active_only: Only return active documents
            
        Returns:
            List of document information
        """
        try:
            query = db.query(Document)
            if active_only:
                query = query.filter(Document.is_active == True)
            
            documents = query.order_by(Document.created_at.desc()).all()
            
            return [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "status": doc.status,
                    "total_chunks": doc.total_chunks,
                    "language": doc.language,
                    "created_at": doc.created_at
                }
                for doc in documents
            ]
            
        except Exception as e:
            logger.error(f"❌ Failed to list documents: {str(e)}")
            return []

# Global instance
document_service = DocumentService()