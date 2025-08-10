"""
Fixed Embedding utilities for text processing
Ensures ASCII-only vector IDs for Pinecone compatibility
"""

import hashlib
import re
import unicodedata
from typing import List, Dict, Any

def generate_chunk_id(text: str, source: str, chunk_index: int) -> str:
    """Generate a unique ASCII-only ID for a text chunk compatible with Pinecone"""
    # Create a hash of the content for uniqueness
    content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
    
    # Clean source name to ASCII-only characters
    clean_source = _ascii_safe_filename(source)
    
    # Remove file extension if present
    if '.' in clean_source:
        clean_source = clean_source.rsplit('.', 1)[0]
    
    # Ensure the final ID is ASCII-only and within reasonable length
    chunk_id = f"{clean_source}_{chunk_index}_{content_hash}"
    
    # Double-check: only allow ASCII alphanumeric, hyphens, and underscores
    chunk_id = re.sub(r'[^a-zA-Z0-9\-_]', '_', chunk_id)
    
    # Ensure ID doesn't start with underscore (Pinecone requirement)
    if chunk_id.startswith('_'):
        chunk_id = 'doc' + chunk_id
    
    return chunk_id

def _ascii_safe_filename(filename: str) -> str:
    """Convert filename to ASCII-safe string"""
    # Remove path if present
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Try to transliterate Unicode characters to ASCII
    try:
        # Normalize and convert to ASCII where possible
        ascii_name = unicodedata.normalize('NFKD', filename)
        ascii_name = ascii_name.encode('ascii', 'ignore').decode('ascii')
        
        # If we lost too much content, use hash instead
        if len(ascii_name) < 3:
            # Create a meaningful hash-based name
            file_hash = hashlib.md5(filename.encode()).hexdigest()[:12]
            ascii_name = f"doc_{file_hash}"
        
    except Exception:
        # Fallback: use hash of original filename
        file_hash = hashlib.md5(filename.encode()).hexdigest()[:12]
        ascii_name = f"doc_{file_hash}"
    
    # Clean up any remaining non-ASCII or problematic characters
    ascii_name = re.sub(r'[^a-zA-Z0-9\-_.]', '_', ascii_name)
    
    # Remove consecutive underscores
    ascii_name = re.sub(r'_+', '_', ascii_name)
    
    # Ensure it doesn't start/end with underscore
    ascii_name = ascii_name.strip('_')
    
    # Ensure minimum length
    if len(ascii_name) < 3:
        file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
        ascii_name = f"doc_{file_hash}"
    
    return ascii_name

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
    Prepare a vector for Pinecone upsert with ASCII-safe ID
    
    Args:
        chunk_id: Unique identifier for the chunk (must be ASCII)
        embedding: Vector embedding
        text: Original text content
        source: Source document name
        chunk_index: Index of chunk in document
        language: Language of the text
        additional_metadata: Extra metadata to include
    
    Returns:
        Formatted vector dict for Pinecone
    """
    # Ensure chunk_id is ASCII-safe
    safe_chunk_id = re.sub(r'[^a-zA-Z0-9\-_]', '_', chunk_id)
    if safe_chunk_id != chunk_id:
        print(f"Warning: Chunk ID sanitized from '{chunk_id}' to '{safe_chunk_id}'")
    
    metadata = {
        "text": text,
        "source": source,  # Keep original source name in metadata
        "chunk_index": chunk_index,
        "language": language,
        "text_length": len(text),
        "word_count": len(text.split())
    }
    
    # Add any additional metadata
    if additional_metadata:
        metadata.update(additional_metadata)
    
    return {
        "id": safe_chunk_id,
        "values": embedding,
        "metadata": metadata
    }

def clean_text_for_embedding(text: str) -> str:
    """Clean text before embedding generation"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters that might confuse embeddings
    text = re.sub(r'[^\w\s\-.,!?():؟،؛]', '', text)  # Added Arabic punctuation
    
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

def test_chunk_id_generation():
    """Test function to verify ASCII-safe ID generation"""
    test_cases = [
        ("الأسئلة الشائعة.pdf", "Arabic FAQ file"),
        ("عربي_document.pdf", "Arabic document"),
        ("english_file.pdf", "English file"),
        ("مزيج_mixed_عربي.pdf", "Mixed language"),
        ("file with spaces.pdf", "Spaces"),
        ("special@#$chars.pdf", "Special characters")
    ]
    
    print("🧪 Testing ASCII-safe chunk ID generation:")
    for filename, description in test_cases:
        chunk_id = generate_chunk_id("Sample text content", filename, 0)
        is_ascii = all(ord(c) < 128 for c in chunk_id)
        print(f"   {description}: '{filename}' -> '{chunk_id}' (ASCII: {is_ascii})")
    
    return True

if __name__ == "__main__":
    test_chunk_id_generation()