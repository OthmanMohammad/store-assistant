"""
Embedding utilities for text processing
"""

import hashlib
import re
from typing import List, Dict, Any

def generate_chunk_id(text: str, source: str, chunk_index: int) -> str:
    """Generate a unique ID for a text chunk"""
    # Create a hash of the content for uniqueness
    content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
    
    # Clean source name (remove path and extension)
    clean_source = re.sub(r'[^\w\-_.]', '_', source)
    if '.' in clean_source:
        clean_source = clean_source.rsplit('.', 1)[0]
    
    return f"{clean_source}_{chunk_index}_{content_hash}"

def prepare_vector_for_upsert(
    chunk_id: str,
    embedding: List[float],
    text: str,
    source: str,
    chunk_index: int,
    language: str = "en",
    additional_metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Prepare a vector for Pinecone upsert
    
    Args:
        chunk_id: Unique identifier for the chunk
        embedding: Vector embedding
        text: Original text content
        source: Source document name
        chunk_index: Index of chunk in document
        language: Language of the text
        additional_metadata: Extra metadata to include
    
    Returns:
        Formatted vector dict for Pinecone
    """
    metadata = {
        "text": text,
        "source": source,
        "chunk_index": chunk_index,
        "language": language,
        "text_length": len(text),
        "word_count": len(text.split())
    }
    
    # Add any additional metadata
    if additional_metadata:
        metadata.update(additional_metadata)
    
    return {
        "id": chunk_id,
        "values": embedding,
        "metadata": metadata
    }

def clean_text_for_embedding(text: str) -> str:
    """Clean text before embedding generation"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters that might confuse embeddings
    text = re.sub(r'[^\w\s\-.,!?():]', '', text)
    
    # Strip and ensure minimum length
    text = text.strip()
    
    return text if len(text) > 10 else None

def calculate_similarity_threshold(query_type: str = "general") -> float:
    """
    Get appropriate similarity threshold based on query type
    
    Args:
        query_type: Type of query (general, exact, faq, etc.)
    
    Returns:
        Similarity threshold (0.0 to 1.0)
    """
    thresholds = {
        "exact": 0.9,      # Very high similarity required
        "faq": 0.85,       # High similarity for FAQ matching  
        "general": 0.75,   # Standard similarity
        "broad": 0.65,     # Lower threshold for broader matching
        "fallback": 0.5    # Last resort threshold
    }
    
    return thresholds.get(query_type, 0.75)