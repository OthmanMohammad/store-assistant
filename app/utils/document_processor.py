"""
Document Processing Utilities
Handles PDF text extraction and intelligent chunking for RAG pipeline
"""

import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import pypdf
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import settings

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        # Initialize text splitter with optimal settings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=[
                "\n\n",  # Paragraphs
                "\n",    # Lines
                ". ",    # Sentences
                "! ",    # Exclamations
                "? ",    # Questions
                "; ",    # Semicolons
                ", ",    # Commas
                " ",     # Words
                ""       # Characters
            ]
        )
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            text_content = ""
            
            # First, check if this is actually a PDF by reading the header
            with open(pdf_path, 'rb') as file:
                header = file.read(5)
                if not header.startswith(b'%PDF'):
                    # If not a PDF, try reading as text file for testing
                    logger.warning(f"⚠️ File doesn't appear to be a PDF, attempting text extraction")
                    file.seek(0)
                    try:
                        content = file.read().decode('utf-8', errors='ignore')
                        if content.strip():
                            logger.info(f"✅ Extracted {len(content)} characters as text")
                            return content
                        else:
                            raise ValueError("File appears to be empty")
                    except Exception as e:
                        raise ValueError(f"Cannot read file as PDF or text: {str(e)}")
            
            # If it is a PDF, process normally
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                logger.info(f"📄 Processing PDF with {len(pdf_reader.pages)} pages")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_content += f"\n\n--- Page {page_num + 1} ---\n\n"
                            text_content += page_text
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to extract text from page {page_num + 1}: {str(e)}")
                        continue
                
            if not text_content.strip():
                raise ValueError("No readable text found in PDF")
                
            logger.info(f"✅ Extracted {len(text_content)} characters from PDF")
            return text_content
            
        except Exception as e:
            logger.error(f"❌ Failed to extract text from PDF: {str(e)}")
            raise
    
    def clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers (common patterns)
        text = re.sub(r'Page \d+.*?\n', '', text)
        text = re.sub(r'\n\d+\n', '\n', text)
        
        # Remove headers/footers (repeated short lines)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 15 or line == "":  # Keep substantial content and empty lines
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Fix common OCR errors
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Split joined words
        text = re.sub(r'(\w)(\d)', r'\1 \2', text)        # Space before numbers
        text = re.sub(r'(\d)(\w)', r'\1 \2', text)        # Space after numbers
        
        # Normalize punctuation
        text = re.sub(r'\.{2,}', '.', text)  # Multiple dots
        text = re.sub(r',,+', ',', text)     # Multiple commas
        
        # Remove extra spaces
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Split text into optimal chunks for embedding
        
        Args:
            text: Text to chunk
            metadata: Additional metadata to include with each chunk
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        try:
            # Split text using LangChain's intelligent splitter
            chunks = self.text_splitter.split_text(text)
            
            processed_chunks = []
            
            for i, chunk_text in enumerate(chunks):
                # Clean the chunk
                clean_chunk = chunk_text.strip()
                
                # Skip very short chunks
                if len(clean_chunk) < 50:
                    logger.debug(f"⏭️ Skipping short chunk {i}: {len(clean_chunk)} chars")
                    continue
                
                # Create chunk metadata
                chunk_metadata = {
                    "chunk_index": i,
                    "text_length": len(clean_chunk),
                    "word_count": len(clean_chunk.split()),
                    **(metadata or {})
                }
                
                processed_chunks.append({
                    "text": clean_chunk,
                    "metadata": chunk_metadata
                })
            
            logger.info(f"✅ Created {len(processed_chunks)} chunks from {len(text)} characters")
            return processed_chunks
            
        except Exception as e:
            logger.error(f"❌ Failed to chunk text: {str(e)}")
            raise
    
    def detect_language(self, text: str) -> str:
        """
        Simple language detection (Arabic vs English)
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code ('ar' or 'en')
        """
        # Count Arabic characters
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        total_chars = len(re.findall(r'[\w]', text))
        
        if total_chars == 0:
            return "en"  # Default to English
        
        arabic_ratio = arabic_chars / total_chars
        
        # If more than 30% Arabic characters, classify as Arabic
        return "ar" if arabic_ratio > 0.3 else "en"
    
    def process_document(self, file_path: str, source_name: str) -> Dict[str, Any]:
        """
        Complete document processing pipeline
        
        Args:
            file_path: Path to document file
            source_name: Name to use for source identification
            
        Returns:
            Processing results with chunks and metadata
        """
        try:
            logger.info(f"🔄 Starting document processing: {source_name}")
            
            # Extract text from PDF
            raw_text = self.extract_text_from_pdf(file_path)
            
            # Clean the text
            clean_text = self.clean_extracted_text(raw_text)
            
            # Detect language
            language = self.detect_language(clean_text)
            logger.info(f"🌍 Detected language: {language}")
            
            # Create base metadata
            base_metadata = {
                "source": source_name,
                "language": language,
                "original_length": len(raw_text),
                "cleaned_length": len(clean_text)
            }
            
            # Chunk the text
            chunks = self.chunk_text(clean_text, base_metadata)
            
            # Calculate statistics
            total_words = sum(chunk["metadata"]["word_count"] for chunk in chunks)
            avg_chunk_size = len(clean_text) // len(chunks) if chunks else 0
            
            result = {
                "source": source_name,
                "language": language,
                "total_chunks": len(chunks),
                "total_words": total_words,
                "avg_chunk_size": avg_chunk_size,
                "chunks": chunks,
                "status": "completed"
            }
            
            logger.info(f"✅ Document processing completed: {len(chunks)} chunks, {total_words} words")
            return result
            
        except Exception as e:
            logger.error(f"❌ Document processing failed: {str(e)}")
            return {
                "source": source_name,
                "status": "failed",
                "error": str(e),
                "chunks": []
            }

# Global instance
document_processor = DocumentProcessor()