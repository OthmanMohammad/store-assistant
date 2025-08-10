"""
Test script for Pinecone Vector Service
Run this to verify your Pinecone integration is working
"""

import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector_service import vector_service
from app.config import settings

async def test_pinecone_integration():
    """Test all vector service functionality"""
    
    print("🧪 Testing Pinecone Vector Service Integration")
    print("=" * 50)
    
    try:
        # Test 1: Initialize connection
        print("\n1️⃣ Testing Pinecone initialization...")
        await vector_service.initialize()
        print("✅ Pinecone initialized successfully!")
        
        # Test 2: Check index stats
        print("\n2️⃣ Getting index statistics...")
        stats = await vector_service.get_index_stats()
        print(f"📊 Index Stats:")
        print(f"   - Total vectors: {stats['total_vectors']}")
        print(f"   - Dimensions: {stats['dimension']}")
        print(f"   - Index fullness: {stats['index_fullness']:.2%}")
        
        # Test 3: Generate embeddings
        print("\n3️⃣ Testing embedding generation...")
        test_texts = [
            "What are your store hours?",
            "Do you accept returns?", 
            "What payment methods do you accept?"
        ]
        
        embeddings = await vector_service.get_embeddings(test_texts)
        print(f"✅ Generated {len(embeddings)} embeddings")
        print(f"   - Embedding dimension: {len(embeddings[0])}")
        
        # Test 4: Upsert test vectors
        print("\n4️⃣ Testing vector upsert...")
        test_vectors = []
        for i, (text, embedding) in enumerate(zip(test_texts, embeddings)):
            test_vectors.append({
                "id": f"test_doc_{i}",
                "values": embedding,
                "metadata": {
                    "text": text,
                    "source": "test_script",
                    "category": "faq"
                }
            })
        
        await vector_service.upsert_vectors(test_vectors)
        print("✅ Test vectors upserted successfully!")
        
        # Test 5: Search for similar vectors
        print("\n5️⃣ Testing similarity search...")
        query = "What time do you open?"
        results = await vector_service.search_similar(query, top_k=3)
        
        print(f"🔍 Search results for: '{query}'")
        for i, result in enumerate(results, 1):
            print(f"   {i}. Score: {result['score']:.4f}")
            print(f"      Text: {result['metadata']['text']}")
            print(f"      ID: {result['id']}")
        
        # Test 6: Clean up test data
        print("\n6️⃣ Cleaning up test data...")
        test_ids = [f"test_doc_{i}" for i in range(len(test_texts))]
        await vector_service.delete_vectors(test_ids)
        print("✅ Test data cleaned up!")
        
        print("\n🎉 All tests passed! Pinecone integration is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        print("📋 Troubleshooting tips:")
        print("   1. Check your .env file has valid PINECONE_API_KEY and OPENAI_API_KEY")
        print("   2. Verify your Pinecone cloud/region settings match your account")
        print("   3. Ensure you have sufficient credits in both OpenAI and Pinecone")
        return False
    
    return True

async def test_configuration():
    """Test configuration settings"""
    print("\n🔧 Configuration Check:")
    print(f"   - Pinecone Index: {settings.PINECONE_INDEX}")
    print(f"   - Embedding Dimensions: {settings.EMBED_DIM}")
    print(f"   - Pinecone Cloud: {settings.PINECONE_CLOUD}")
    print(f"   - Pinecone Region: {settings.PINECONE_REGION}")
    print(f"   - OpenAI API Key: {'✅ Set' if settings.OPENAI_API_KEY else '❌ Missing'}")
    print(f"   - Pinecone API Key: {'✅ Set' if settings.PINECONE_API_KEY else '❌ Missing'}")

if __name__ == "__main__":
    print("🏪 Store Assistant - Pinecone Integration Test")
    
    # Check configuration first
    asyncio.run(test_configuration())
    
    # Run integration tests
    success = asyncio.run(test_pinecone_integration())
    
    if success:
        print("\n✅ Ready to implement document ingestion pipeline!")
    else:
        print("\n❌ Fix the issues above before proceeding.")