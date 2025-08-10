"""
Pinecone Vector Service
Handles vector operations for the Store Assistant RAG system
"""

import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
import openai
from app.config import settings

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self):
        self.pc = None
        self.index = None
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
    async def initialize(self):
        """Initialize Pinecone connection and ensure index exists"""
        try:
            # Initialize Pinecone
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Check if index exists, create if not
            existing_indexes = self.pc.list_indexes()
            index_names = [idx.name for idx in existing_indexes]
            
            if settings.PINECONE_INDEX not in index_names:
                logger.info(f"Creating Pinecone index: {settings.PINECONE_INDEX}")
                self.pc.create_index(
                    name=settings.PINECONE_INDEX,
                    dimension=settings.EMBED_DIM,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud=settings.PINECONE_CLOUD,
                        region=settings.PINECONE_REGION
                    )
                )
                logger.info("✅ Pinecone index created successfully")
            else:
                logger.info(f"✅ Pinecone index '{settings.PINECONE_INDEX}' already exists")
            
            # Connect to index
            self.index = self.pc.Index(settings.PINECONE_INDEX)
            logger.info(f"🔗 Connected to Pinecone index: {settings.PINECONE_INDEX}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Pinecone: {str(e)}")
            raise
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=texts,
                dimensions=settings.EMBED_DIM
            )
            
            embeddings = [data.embedding for data in response.data]
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embeddings: {str(e)}")
            raise
    
    async def upsert_vectors(self, vectors: List[Dict[str, Any]]) -> bool:
        """
        Upsert vectors to Pinecone
        
        Args:
            vectors: List of dicts with 'id', 'values', and 'metadata'
        """
        try:
            if not self.index:
                await self.initialize()
            
            # Upsert in batches of 100 (Pinecone limit)
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
                logger.info(f"✅ Upserted batch {i//batch_size + 1}: {len(batch)} vectors")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to upsert vectors: {str(e)}")
            raise
    
    async def search_similar(self, query_text: str, top_k: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        Search for similar vectors using text query
        
        Args:
            query_text: Text to search for
            top_k: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            List of matches with id, score, and metadata
        """
        try:
            if not self.index:
                await self.initialize()
            
            # Generate embedding for query
            query_embedding = await self.get_embeddings([query_text])
            
            # Search in Pinecone
            results = self.index.query(
                vector=query_embedding[0],
                top_k=top_k,
                filter=filter_dict,
                include_metadata=True
            )
            
            # Format results
            matches = []
            for match in results.matches:
                matches.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
            
            logger.info(f"✅ Found {len(matches)} similar vectors for query")
            return matches
            
        except Exception as e:
            logger.error(f"❌ Failed to search vectors: {str(e)}")
            raise
    
    async def delete_vectors(self, ids: List[str]) -> bool:
        """Delete vectors by IDs"""
        try:
            if not self.index:
                await self.initialize()
            
            self.index.delete(ids=ids)
            logger.info(f"✅ Deleted {len(ids)} vectors")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete vectors: {str(e)}")
            raise
    
    async def get_index_stats(self) -> Dict:
        """Get index statistics"""
        try:
            if not self.index:
                await self.initialize()
            
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": dict(stats.namespaces) if stats.namespaces else {}
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get index stats: {str(e)}")
            raise

# Global instance
vector_service = VectorService()