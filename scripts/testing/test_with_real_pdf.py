"""
Test script using manual PDF upload
Since creating PDFs programmatically requires dependencies, this script guides you through manual testing
"""

import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector_service import vector_service
from app.services.document_service import document_service
from app.database import SessionLocal

def create_simple_test_data():
    """Create simple test data directly in vector store"""
    return [
        {
            "text": "Our store hours are Monday to Friday 9 AM to 8 PM, Saturday 10 AM to 6 PM, and Sunday 11 AM to 5 PM.",
            "source": "store_policy.pdf",
            "language": "en",
            "category": "hours"
        },
        {
            "text": "We accept returns within 30 days with receipt. Items must be in original condition for a full refund.",
            "source": "store_policy.pdf", 
            "language": "en",
            "category": "returns"
        },
        {
            "text": "Payment methods accepted include cash, credit cards (Visa, MasterCard, American Express), and mobile payments like Apple Pay and Google Pay.",
            "source": "store_policy.pdf",
            "language": "en", 
            "category": "payment"
        },
        {
            "text": "We offer same-day delivery within 10 miles for orders over $50. Delivery fee is $5 for orders under $50.",
            "source": "store_policy.pdf",
            "language": "en",
            "category": "delivery"
        },
        {
            "text": "Customer service is available at (555) 123-4567 or support@store.com. Our support hours are Monday to Friday 8 AM to 6 PM.",
            "source": "store_policy.pdf",
            "language": "en",
            "category": "contact"
        }
    ]

async def test_direct_vector_ingestion():
    """Test vector ingestion without PDF processing"""
    print("🧠 Testing Direct Vector Ingestion...")
    
    try:
        # Get test data
        test_chunks = create_simple_test_data()
        
        # Extract texts for embedding
        texts = [chunk["text"] for chunk in test_chunks]
        
        print(f"📝 Processing {len(texts)} text chunks...")
        
        # Generate embeddings
        embeddings = await vector_service.get_embeddings(texts)
        print(f"✅ Generated {len(embeddings)} embeddings")
        
        # Prepare vectors for upsert
        vectors = []
        for i, (chunk, embedding) in enumerate(zip(test_chunks, embeddings)):
            vector = {
                "id": f"test_chunk_{i}",
                "values": embedding,
                "metadata": {
                    "text": chunk["text"],
                    "source": chunk["source"],
                    "language": chunk["language"],
                    "category": chunk["category"],
                    "chunk_index": i,
                    "test_data": True
                }
            }
            vectors.append(vector)
        
        # Upsert vectors
        await vector_service.upsert_vectors(vectors)
        print(f"✅ Stored {len(vectors)} vectors in Pinecone")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct ingestion failed: {str(e)}")
        return False

async def test_search_with_real_data():
    """Test search functionality with our test data"""
    print("\n🔍 Testing Search with Real Data...")
    
    test_queries = [
        "What are your store hours?",
        "How do I return something?", 
        "What payment methods do you accept?",
        "Do you offer delivery?",
        "How can I contact customer service?"
    ]
    
    try:
        for query in test_queries:
            print(f"\n   Query: '{query}'")
            
            results = await vector_service.search_similar(query, top_k=2)
            
            if results:
                for i, result in enumerate(results, 1):
                    score = result['score']
                    text = result['metadata']['text']
                    category = result['metadata'].get('category', 'unknown')
                    
                    print(f"      {i}. Score: {score:.3f} | Category: {category}")
                    print(f"         Answer: {text}")
            else:
                print("      No results found")
        
        return True
        
    except Exception as e:
        print(f"❌ Search test failed: {str(e)}")
        return False

async def test_database_operations():
    """Test database operations"""
    print("\n📊 Testing Database Operations...")
    
    try:
        db = SessionLocal()
        
        try:
            # List documents
            documents = await document_service.list_documents(db)
            print(f"📋 Found {len(documents)} documents in database")
            
            for doc in documents:
                print(f"   - ID: {doc['id']}, Name: {doc['filename']}, Status: {doc['status']}")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False

async def cleanup_test_vectors():
    """Clean up test vectors"""
    print("\n🧹 Cleaning up test vectors...")
    
    try:
        # Delete test vectors
        test_ids = [f"test_chunk_{i}" for i in range(5)]
        await vector_service.delete_vectors(test_ids)
        print("✅ Test vectors cleaned up")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {str(e)}")

async def main():
    """Run simplified tests"""
    print("🏪 Store Assistant - Simplified Pipeline Test")
    print("=" * 55)
    
    # Check prerequisites
    print("🔧 Checking vector service...")
    try:
        await vector_service.initialize()
        print("✅ Vector service ready")
    except Exception as e:
        print(f"❌ Vector service failed: {str(e)}")
        return
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Direct vector ingestion
    if await test_direct_vector_ingestion():
        tests_passed += 1
    
    # Test 2: Search functionality
    if await test_search_with_real_data():
        tests_passed += 1
    
    # Test 3: Database operations
    if await test_database_operations():
        tests_passed += 1
    
    # Cleanup
    await cleanup_test_vectors()
    
    # Summary
    print("\n" + "=" * 55)
    print(f"🎯 Test Summary: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 Core pipeline working! Vector ingestion and search operational!")
        print("\n📋 Next Steps:")
        print("   1. Test with real PDF: Create any PDF and use the API")
        print("   2. Or install reportlab: pip install reportlab")
    else:
        print("❌ Some core functions failed.")

if __name__ == "__main__":
    asyncio.run(main())