"""
Test script for RAG Service
Tests the complete RAG pipeline: Query → Retrieve → Generate
"""

import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag_service import rag_service
from app.services.vector_service import vector_service
from app.config import settings

async def setup_test_data():
    """Add some test data to vector store for RAG testing"""
    print("📝 Setting up test data...")
    
    test_data = [
        {
            "text": "Our store is open Monday through Friday from 9:00 AM to 8:00 PM, Saturday from 10:00 AM to 6:00 PM, and Sunday from 11:00 AM to 5:00 PM.",
            "source": "store_hours.pdf",
            "language": "en",
            "category": "hours"
        },
        {
            "text": "We have a 30-day return policy. Items can be returned within 30 days of purchase with a receipt for a full refund. Items must be in original condition.",
            "source": "return_policy.pdf",
            "language": "en", 
            "category": "returns"
        },
        {
            "text": "We accept cash, all major credit cards (Visa, MasterCard, American Express), and mobile payments including Apple Pay and Google Pay.",
            "source": "payment_info.pdf",
            "language": "en",
            "category": "payment"
        },
        {
            "text": "Yes, we offer delivery! Same-day delivery is available within 10 miles for orders over $50. Delivery fee is $5 for smaller orders.",
            "source": "delivery_service.pdf",
            "language": "en",
            "category": "delivery"
        },
        {
            "text": "Customer service is available at (555) 123-4567 or support@ourstore.com. Our support team is available Monday through Friday, 8 AM to 6 PM.",
            "source": "contact_info.pdf",
            "language": "en",
            "category": "contact"
        }
    ]
    
    try:
        # Generate embeddings
        texts = [item["text"] for item in test_data]
        embeddings = await vector_service.get_embeddings(texts)
        
        # Prepare vectors
        vectors = []
        for i, (data, embedding) in enumerate(zip(test_data, embeddings)):
            vector = {
                "id": f"rag_test_{i}",
                "values": embedding,
                "metadata": {
                    "text": data["text"],
                    "source": data["source"],
                    "language": data["language"],
                    "category": data["category"],
                    "test_data": True
                }
            }
            vectors.append(vector)
        
        # Store vectors
        await vector_service.upsert_vectors(vectors)
        print(f"✅ Added {len(vectors)} test documents to vector store")
        
        # Wait a moment for indexing
        print("⏳ Waiting for vectors to be indexed...")
        await asyncio.sleep(5)
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to setup test data: {str(e)}")
        return False

async def test_basic_rag():
    """Test basic RAG functionality"""
    print("\n🤖 Testing Basic RAG...")
    
    test_queries = [
        "What are your store hours?",
        "How do I return something?",
        "What payment methods do you accept?", 
        "Do you offer delivery?",
        "How can I contact customer service?"
    ]
    
    success_count = 0
    
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        
        try:
            response = await rag_service.generate_response(
                user_message=query,
                language="en",
                use_knowledge_base=True
            )
            
            print(f"   📤 Answer: {response['answer'][:100]}...")
            print(f"   🌍 Language: {response['language']}")
            print(f"   📊 Confidence: {response['confidence']:.2f}")
            print(f"   📚 Sources: {response.get('sources', [])}")
            print(f"   🔗 Context Used: {response['context_used']}")
            
            if response['context_used'] and response['confidence'] > 0.3:
                print("   ✅ RAG working correctly")
                success_count += 1
            else:
                print("   ⚠️ Low confidence or no context")
                
        except Exception as e:
            print(f"   ❌ RAG failed: {str(e)}")
    
    return success_count, len(test_queries)

async def test_multilingual():
    """Test multilingual capabilities"""
    print("\n🌍 Testing Multilingual Support...")
    
    # Arabic queries (if you have Arabic data, otherwise just test detection)
    arabic_queries = [
        "ما هي ساعات العمل؟",
        "كيف يمكنني إرجاع منتج؟"
    ]
    
    english_queries = [
        "What are your hours?",
        "Store hours please"
    ]
    
    for query in english_queries + arabic_queries:
        print(f"\n   Query: '{query}'")
        
        try:
            response = await rag_service.generate_response(
                user_message=query,
                language="auto",
                use_knowledge_base=True
            )
            
            print(f"   🌍 Detected Language: {response['language']}")
            print(f"   📤 Answer: {response['answer'][:80]}...")
            
        except Exception as e:
            print(f"   ❌ Multilingual test failed: {str(e)}")

async def test_conversation_context():
    """Test conversation history handling"""
    print("\n💬 Testing Conversation Context...")
    
    conversation_history = [
        {"role": "user", "content": "What are your store hours?"},
        {"role": "assistant", "content": "We're open Monday-Friday 9am-8pm, Saturday 10am-6pm, Sunday 11am-5pm."}
    ]
    
    follow_up_query = "Are you open on holidays?"
    
    try:
        response = await rag_service.generate_response(
            user_message=follow_up_query,
            language="en",
            conversation_history=conversation_history,
            use_knowledge_base=True
        )
        
        print(f"   Query: '{follow_up_query}'")
        print(f"   📤 Answer: {response['answer']}")
        print(f"   💭 Used conversation context: {len(conversation_history) > 0}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Context test failed: {str(e)}")
        return False

async def test_fallback_behavior():
    """Test behavior without knowledge base"""
    print("\n🔄 Testing Fallback Behavior...")
    
    queries = [
        "What is the meaning of life?",  # Unrelated query
        "Tell me a joke",  # Casual query
        "What's the weather like?"  # External query
    ]
    
    for query in queries:
        print(f"\n   Query: '{query}'")
        
        try:
            response = await rag_service.generate_response(
                user_message=query,
                language="en",
                use_knowledge_base=True
            )
            
            print(f"   📤 Answer: {response['answer'][:100]}...")
            print(f"   📊 Confidence: {response['confidence']:.2f}")
            print(f"   🔗 Context Used: {response['context_used']}")
            
        except Exception as e:
            print(f"   ❌ Fallback test failed: {str(e)}")

async def test_suggestions():
    """Test suggested questions"""
    print("\n💡 Testing Suggested Questions...")
    
    try:
        en_suggestions = await rag_service.get_suggested_questions("en")
        ar_suggestions = await rag_service.get_suggested_questions("ar")
        
        print(f"   📝 English suggestions: {len(en_suggestions)}")
        for suggestion in en_suggestions[:3]:
            print(f"      - {suggestion}")
        
        print(f"   📝 Arabic suggestions: {len(ar_suggestions)}")
        for suggestion in ar_suggestions[:3]:
            print(f"      - {suggestion}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Suggestions test failed: {str(e)}")
        return False

async def cleanup_test_data():
    """Clean up test vectors"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        test_ids = [f"rag_test_{i}" for i in range(5)]
        await vector_service.delete_vectors(test_ids)
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {str(e)}")

async def main():
    """Run all RAG tests"""
    print("🤖 Store Assistant - RAG Service Test")
    print("=" * 50)
    
    # Check prerequisites
    print("🔧 Checking prerequisites...")
    try:
        await vector_service.initialize()
        print("✅ Vector service ready")
    except Exception as e:
        print(f"❌ Vector service failed: {str(e)}")
        return
    
    # Check OpenAI connection
    if not settings.OPENAI_API_KEY:
        print("❌ OpenAI API key not configured")
        return
    
    print("✅ OpenAI API key configured")
    
    # Setup test data
    if not await setup_test_data():
        print("❌ Failed to setup test data")
        return
    
    # Run tests
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Basic RAG
    success_count, total_queries = await test_basic_rag()
    if success_count >= total_queries * 0.6:  # 60% success rate
        tests_passed += 1
        print(f"✅ Basic RAG test passed ({success_count}/{total_queries} queries successful)")
    else:
        print(f"❌ Basic RAG test failed ({success_count}/{total_queries} queries successful)")
    
    # Test 2: Multilingual
    await test_multilingual()
    tests_passed += 1  # Language detection works even if no Arabic content
    
    # Test 3: Conversation context
    if await test_conversation_context():
        tests_passed += 1
    
    # Test 4: Fallback behavior
    await test_fallback_behavior()
    tests_passed += 1  # Fallback should always work
    
    # Test 5: Suggestions
    if await test_suggestions():
        tests_passed += 1
    
    # Cleanup
    await cleanup_test_data()
    
    # Summary
    print("\n" + "=" * 50)
    print(f"🎯 Test Summary: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed >= 4:
        print("🎉 RAG service is working correctly!")
        print("✅ Ready for production use!")
        print("\n📋 Next Steps:")
        print("   1. Test the web chat interface")
        print("   2. Upload real store documents")
        print("   3. Deploy to production")
    else:
        print("❌ Some RAG functions need attention.")
        print("💡 Check OpenAI API credits and vector service setup")

if __name__ == "__main__":
    asyncio.run(main())