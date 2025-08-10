#!/usr/bin/env python3
"""
Fixed Enterprise RAG Service Test Script
Tests the complete hybrid RAG pipeline: Database + Vector Search + AI Generation
Compatible with SQLAlchemy 2.x
"""

import asyncio
import sys
import os
from sqlalchemy import text

# Add parent directory to path to import app modules
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from app.services.rag_service import enterprise_rag_service
from app.services.vector_service import vector_service
from app.database import SessionLocal
from app.config import settings

async def check_database_connection():
    """Test database connection with SQLAlchemy 2.x compatibility"""
    print("🔍 Testing database connection...")
    
    try:
        db = SessionLocal()
        try:
            # Use text() for raw SQL in SQLAlchemy 2.x
            result = db.execute(text("SELECT 1 as test_connection")).fetchone()
            if result and result[0] == 1:
                print("✅ Database connection successful")
                return True
            else:
                print("❌ Database query returned unexpected result")
                return False
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("💡 Troubleshooting tips:")
        print("   1. Make sure PostgreSQL is running: docker-compose up postgres")
        print("   2. Check DATABASE_URL in your .env file")
        print("   3. Ensure database tables exist: run database seeding script")
        return False

async def check_database_data():
    """Check if database has been seeded with test data"""
    print("📊 Checking database data...")
    
    try:
        db = SessionLocal()
        try:
            # Import models
            from app.models.product import Product, ServiceOffering, StoreLocation
            
            # Check for products
            product_count = db.query(Product).count()
            service_count = db.query(ServiceOffering).count()
            store_count = db.query(StoreLocation).count()
            
            print(f"   📱 Products: {product_count}")
            print(f"   🔧 Services: {service_count}")
            print(f"   🏪 Store locations: {store_count}")
            
            if product_count > 0 and service_count > 0:
                print("✅ Database contains test data")
                return True
            else:
                print("⚠️ Database appears empty - consider running seed script")
                print("💡 Run: python scripts/database/seed_database.py")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Failed to check database data: {str(e)}")
        return False

async def setup_test_data():
    """Add comprehensive test data to vector store for RAG testing"""
    print("📝 Setting up comprehensive test data...")
    
    test_data = [
        # Store Information
        {
            "text": "TechMart Palestine is open Monday through Friday from 9:00 AM to 8:00 PM, Saturday from 10:00 AM to 6:00 PM, and Sunday from 11:00 AM to 5:00 PM. During Ramadan, we have split hours: 10:00 AM - 4:00 PM and 8:00 PM - 1:00 AM.",
            "source": "store_hours.pdf",
            "language": "en",
            "category": "hours",
            "document_type": "policy"
        },
        {
            "text": "We have a comprehensive 30-day return policy. Items can be returned within 30 days of purchase with original receipt for a full refund. Items must be in original condition with all accessories and packaging. Opened electronics have a 14-day return window.",
            "source": "return_policy.pdf",
            "language": "en", 
            "category": "returns",
            "document_type": "policy"
        },
        {
            "text": "We accept multiple payment methods: cash (JOD), all major credit cards (Visa, MasterCard, American Express), debit cards, mobile payments (Apple Pay, Google Pay), and installment plans for purchases over 500 JOD.",
            "source": "payment_info.pdf",
            "language": "en",
            "category": "payment",
            "document_type": "policy"
        },
        {
            "text": "Yes, we offer comprehensive delivery services! Same-day delivery is available within Nablus city for orders over 200 JOD (free) or 15 JOD fee for smaller orders. Express delivery (1 hour) available for 50 JOD. We also serve greater Nablus area with next-day delivery for 25 JOD.",
            "source": "delivery_service.pdf",
            "language": "en",
            "category": "delivery",
            "document_type": "service"
        },
        {
            "text": "Customer service is available at +970-9-234-5678 or info@techmart-palestine.ps. Our technical support team is available Monday through Friday, 8 AM to 6 PM. For emergencies outside hours, call +970-59-123-4567 (WhatsApp available).",
            "source": "contact_info.pdf",
            "language": "en",
            "category": "contact",
            "document_type": "policy"
        },
        # Arabic Content
        {
            "text": "متجر تك مارت فلسطين مفتوح من الأحد إلى الخميس من 9 صباحاً حتى 8 مساءً، والجمعة من 9 صباحاً حتى 2 ظهراً، والسبت من 10 صباحاً حتى 8 مساءً. نحن في شارع الرفيدية، نابلس.",
            "source": "معلومات_المتجر.pdf",
            "language": "ar",
            "category": "hours",
            "document_type": "policy"
        },
        {
            "text": "نقدم خدمات تركيب متخصصة: تركيب أجهزة التكييف (120 دينار)، تركيب التلفزيونات على الحائط (45 دينار)، إعداد أجهزة الكمبيوتر (50 دينار)، ونقل البيانات للهواتف الذكية (25 دينار).",
            "source": "خدمات_التركيب.pdf",
            "language": "ar",
            "category": "installation",
            "document_type": "service"
        },
        # Product Information
        {
            "text": "iPhone 15 Pro Max features: 6.7-inch display, A17 Pro chip, 48MP camera system, titanium design, USB-C, available in 256GB, 512GB, 1TB. Prices start at 1,899 JOD with 12-month Apple warranty. Trade-in programs available.",
            "source": "iphone_specs.pdf",
            "language": "en",
            "category": "smartphones",
            "document_type": "product"
        },
        {
            "text": "Samsung Galaxy S24 Ultra specifications: 6.8-inch Dynamic AMOLED, Snapdragon 8 Gen 3, 200MP camera, S Pen included, 12GB RAM, 512GB storage. Price: 1,599 JOD (original 1,699 JOD) with 24-month Samsung warranty.",
            "source": "samsung_specs.pdf",
            "language": "en",
            "category": "smartphones",
            "document_type": "product"
        }
    ]
    
    try:
        # Generate embeddings
        texts = [item["text"] for item in test_data]
        embeddings = await vector_service.get_embeddings(texts)
        
        # Prepare vectors with rich metadata
        vectors = []
        for i, (data, embedding) in enumerate(zip(test_data, embeddings)):
            vector = {
                "id": f"enterprise_test_{i}",
                "values": embedding,
                "metadata": {
                    "text": data["text"],
                    "source": data["source"],
                    "language": data["language"],
                    "category": data["category"],
                    "document_type": data["document_type"],
                    "test_data": True,
                    "chunk_index": i,
                    "text_length": len(data["text"]),
                    "word_count": len(data["text"].split())
                }
            }
            vectors.append(vector)
        
        # Store vectors
        await vector_service.upsert_vectors(vectors)
        print(f"✅ Added {len(vectors)} comprehensive test documents to vector store")
        
        # Wait for indexing
        print("⏳ Waiting for vectors to be indexed...")
        await asyncio.sleep(3)
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to setup test data: {str(e)}")
        return False

async def test_basic_enterprise_rag():
    """Test basic Enterprise RAG functionality with database integration"""
    print("\n🤖 Testing Enterprise RAG with Database Integration...")
    
    test_queries = [
        ("What are your store hours?", "en"),
        ("How much does iPhone 15 cost?", "en"),
        ("Do you offer installation services?", "en"),
        ("What payment methods do you accept?", "en"),
        ("ما هي ساعات العمل؟", "ar"),
        ("كم سعر آيفون 15؟", "ar")
    ]
    
    success_count = 0
    db = SessionLocal()
    
    try:
        for query, expected_lang in test_queries:
            print(f"\n   Query: '{query}' (Expected: {expected_lang})")
            
            try:
                # Use Enterprise RAG service with database
                response = await enterprise_rag_service.generate_response(
                    user_message=query,
                    language="auto",
                    conversation_history=None,
                    db=db
                )
                
                print(f"   📤 Answer: {response['answer'][:150]}...")
                print(f"   🌍 Language: {response['language']}")
                print(f"   📊 Confidence: {response['confidence']:.3f}")
                print(f"   📚 Sources: {response.get('sources', [])}")
                
                # Get metadata safely
                metadata = response.get('metadata', {})
                print(f"   🛒 Products Found: {metadata.get('products_found', 0)}")
                print(f"   🔧 Services Found: {metadata.get('services_found', 0)}")
                print(f"   📄 Document Chunks: {metadata.get('context_chunks', 0)}")
                print(f"   🎯 Intent: {metadata.get('intent', 'unknown')}")
                
                # Check if we got a meaningful response
                if (response['confidence'] > 0.3 and 
                    len(response['answer']) > 50 and 
                    response['language'] == expected_lang):
                    print("   ✅ Enterprise RAG working correctly")
                    success_count += 1
                else:
                    print("   ⚠️ Response quality below threshold")
                    
            except Exception as e:
                print(f"   ❌ RAG failed: {str(e)}")
        
        return success_count, len(test_queries)
        
    finally:
        db.close()

async def test_product_queries():
    """Test product-specific queries that should trigger database lookups"""
    print("\n🛒 Testing Product Database Integration...")
    
    product_queries = [
        "Show me Samsung phones",
        "What's the price of Galaxy S24?",
        "Do you have iPhone 15 in stock?",
        "Compare Samsung and Apple phones",
        "What's the cheapest laptop you have?"
    ]
    
    db = SessionLocal()
    success_count = 0
    
    try:
        for query in product_queries:
            print(f"\n   Query: '{query}'")
            
            try:
                response = await enterprise_rag_service.generate_response(
                    user_message=query,
                    language="en",
                    db=db
                )
                
                metadata = response.get('metadata', {})
                products_found = metadata.get('products_found', 0)
                has_pricing = 'JOD' in response['answer']
                confidence = response['confidence']
                
                print(f"   📱 Products Found: {products_found}")
                print(f"   💰 Has Pricing: {has_pricing}")
                print(f"   📊 Confidence: {confidence:.3f}")
                print(f"   📤 Response: {response['answer'][:100]}...")
                
                if products_found > 0 and confidence > 0.4:
                    success_count += 1
                    print("   ✅ Product query successful")
                else:
                    print("   ⚠️ Limited product data retrieved")
                    
            except Exception as e:
                print(f"   ❌ Product query failed: {str(e)}")
        
        return success_count, len(product_queries)
        
    finally:
        db.close()

async def test_service_queries():
    """Test service-related queries"""
    print("\n🔧 Testing Service Database Integration...")
    
    service_queries = [
        "Do you install air conditioners?",
        "How much does TV mounting cost?",
        "What installation services do you offer?",
        "Do you provide laptop setup?"
    ]
    
    db = SessionLocal()
    success_count = 0
    
    try:
        for query in service_queries:
            print(f"\n   Query: '{query}'")
            
            try:
                response = await enterprise_rag_service.generate_response(
                    user_message=query,
                    language="en",
                    db=db
                )
                
                metadata = response.get('metadata', {})
                services_found = metadata.get('services_found', 0)
                has_pricing = 'JOD' in response['answer'] or 'price' in response['answer'].lower()
                confidence = response['confidence']
                
                print(f"   🔧 Services Found: {services_found}")
                print(f"   💰 Has Service Info: {has_pricing}")
                print(f"   📊 Confidence: {confidence:.3f}")
                print(f"   📤 Response: {response['answer'][:100]}...")
                
                if confidence > 0.4:
                    success_count += 1
                    print("   ✅ Service query successful")
                else:
                    print("   ⚠️ Low confidence response")
                    
            except Exception as e:
                print(f"   ❌ Service query failed: {str(e)}")
        
        return success_count, len(service_queries)
        
    finally:
        db.close()

async def test_conversation_context():
    """Test conversation history handling"""
    print("\n💬 Testing Conversation Context...")
    
    db = SessionLocal()
    
    try:
        # First query
        print("   First query: 'What phones do you have?'")
        response1 = await enterprise_rag_service.generate_response(
            user_message="What phones do you have?",
            language="en",
            db=db
        )
        print(f"   📤 Response 1: {response1['answer'][:100]}...")
        
        # Follow-up query with context
        conversation_history = [
            {"role": "user", "content": "What phones do you have?"},
            {"role": "assistant", "content": response1['answer']}
        ]
        
        print("   Follow-up query: 'What about their prices?'")
        response2 = await enterprise_rag_service.generate_response(
            user_message="What about their prices?",
            language="en",
            conversation_history=conversation_history,
            db=db
        )
        
        print(f"   📤 Response 2: {response2['answer'][:100]}...")
        print(f"   📊 Confidence: {response2['confidence']:.3f}")
        
        # Check if context was used effectively
        context_effectiveness = (
            response2['confidence'] > 0.4 and
            ('price' in response2['answer'].lower() or 'JOD' in response2['answer'])
        )
        
        if context_effectiveness:
            print("   ✅ Conversation context working correctly")
            return True
        else:
            print("   ⚠️ Context may not be fully utilized")
            return False
        
    except Exception as e:
        print(f"   ❌ Context test failed: {str(e)}")
        return False
    
    finally:
        db.close()

async def test_multilingual_capabilities():
    """Test advanced multilingual support"""
    print("\n🌍 Testing Advanced Multilingual Support...")
    
    multilingual_tests = [
        ("What are your hours?", "en"),
        ("ما هي ساعات العمل؟", "ar"),
        ("Do you have Samsung phones?", "en"),
        ("هل يوجد هواتف سامسونغ؟", "ar")
    ]
    
    db = SessionLocal()
    success_count = 0
    
    try:
        for query, expected_lang in multilingual_tests:
            print(f"\n   Query: '{query}' (Expected: {expected_lang})")
            
            try:
                response = await enterprise_rag_service.generate_response(
                    user_message=query,
                    language="auto",
                    db=db
                )
                
                detected_lang = response['language']
                confidence = response['confidence']
                
                print(f"   🌍 Detected: {detected_lang}")
                print(f"   📊 Confidence: {confidence:.3f}")
                print(f"   📤 Response: {response['answer'][:80]}...")
                
                if detected_lang == expected_lang and confidence > 0.3:
                    success_count += 1
                    print("   ✅ Language detection correct")
                else:
                    print(f"   ⚠️ Expected {expected_lang}, got {detected_lang}")
                    
            except Exception as e:
                print(f"   ❌ Multilingual test failed: {str(e)}")
        
        return success_count, len(multilingual_tests)
        
    finally:
        db.close()

async def test_suggestions():
    """Test suggested questions functionality"""
    print("\n💡 Testing Suggested Questions...")
    
    try:
        # Test English suggestions
        en_suggestions = await enterprise_rag_service.get_suggested_questions("en")
        print(f"   📝 English suggestions ({len(en_suggestions)}):")
        for i, suggestion in enumerate(en_suggestions[:5], 1):
            print(f"      {i}. {suggestion}")
        
        # Test Arabic suggestions
        ar_suggestions = await enterprise_rag_service.get_suggested_questions("ar")
        print(f"   📝 Arabic suggestions ({len(ar_suggestions)}):")
        for i, suggestion in enumerate(ar_suggestions[:5], 1):
            print(f"      {i}. {suggestion}")
        
        # Check quality
        if len(en_suggestions) >= 5 and len(ar_suggestions) >= 5:
            print("   ✅ Suggestions working correctly")
            return True
        else:
            print("   ⚠️ Insufficient suggestions generated")
            return False
        
    except Exception as e:
        print(f"   ❌ Suggestions test failed: {str(e)}")
        return False

async def cleanup_test_data():
    """Clean up test vectors"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        test_ids = [f"enterprise_test_{i}" for i in range(9)]
        await vector_service.delete_vectors(test_ids)
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {str(e)}")

async def main():
    """Run comprehensive Enterprise RAG tests"""
    print("🚀 TechMart Palestine - Enterprise RAG Service Test")
    print("=" * 60)
    
    # Check prerequisites
    print("🔧 Checking prerequisites...")
    
    # 1. Vector service
    try:
        await vector_service.initialize()
        print("✅ Vector service ready")
    except Exception as e:
        print(f"❌ Vector service failed: {str(e)}")
        print("💡 Check your Pinecone API key and configuration")
        return
    
    # 2. OpenAI API
    if not settings.OPENAI_API_KEY:
        print("❌ OpenAI API key not configured")
        print("💡 Set OPENAI_API_KEY in your .env file")
        return
    print("✅ OpenAI API key configured")
    
    # 3. Database connection (FIXED)
    if not await check_database_connection():
        return
    
    # 4. Database data
    has_data = await check_database_data()
    if not has_data:
        print("⚠️ Database appears empty - results may be limited")
        print("💡 Consider running: python scripts/database/seed_database.py")
    
    # Setup test data
    if not await setup_test_data():
        print("❌ Failed to setup test data")
        return
    
    # Run comprehensive tests
    tests_passed = 0
    total_tests = 6
    
    print(f"\n🧪 Running {total_tests} comprehensive test suites...")
    
    # Test 1: Basic Enterprise RAG
    success_count, total_queries = await test_basic_enterprise_rag()
    if success_count >= total_queries * 0.7:  # 70% success rate
        tests_passed += 1
        print(f"✅ Basic Enterprise RAG test PASSED ({success_count}/{total_queries} queries successful)")
    else:
        print(f"❌ Basic Enterprise RAG test FAILED ({success_count}/{total_queries} queries successful)")
    
    # Test 2: Product queries
    success_count, total_queries = await test_product_queries()
    if success_count >= total_queries * 0.6:  # 60% success rate
        tests_passed += 1
        print(f"✅ Product queries test PASSED ({success_count}/{total_queries} queries successful)")
    else:
        print(f"❌ Product queries test FAILED ({success_count}/{total_queries} queries successful)")
    
    # Test 3: Service queries
    success_count, total_queries = await test_service_queries()
    if success_count >= total_queries * 0.6:
        tests_passed += 1
        print(f"✅ Service queries test PASSED ({success_count}/{total_queries} queries successful)")
    else:
        print(f"❌ Service queries test FAILED ({success_count}/{total_queries} queries successful)")
    
    # Test 4: Conversation context
    if await test_conversation_context():
        tests_passed += 1
        print("✅ Conversation context test PASSED")
    else:
        print("❌ Conversation context test FAILED")
    
    # Test 5: Multilingual support
    success_count, total_queries = await test_multilingual_capabilities()
    if success_count >= total_queries * 0.7:
        tests_passed += 1
        print(f"✅ Multilingual test PASSED ({success_count}/{total_queries} languages correct)")
    else:
        print(f"❌ Multilingual test FAILED ({success_count}/{total_queries} languages correct)")
    
    # Test 6: Suggestions
    if await test_suggestions():
        tests_passed += 1
        print("✅ Suggestions test PASSED")
    else:
        print("❌ Suggestions test FAILED")
    
    # Cleanup
    await cleanup_test_data()
    
    # Final summary
    print("\n" + "=" * 60)
    print(f"🎯 FINAL RESULTS: {tests_passed}/{total_tests} test suites passed")
    
    if tests_passed >= 5:
        print("🎉 ENTERPRISE RAG SERVICE IS WORKING EXCELLENTLY!")
        print("✅ Your TechMart Palestine AI assistant is ready for production!")
        print("\n📋 What's working:")
        print("   ✅ Hybrid database + vector search")
        print("   ✅ Bilingual Arabic/English support")
        print("   ✅ Product and service integration")
        print("   ✅ Conversation context management")
        print("   ✅ Intelligent confidence scoring")
        print("   ✅ Professional customer service responses")
        
        print("\n🚀 Next Steps:")
        print("   1. Test the web chat interface at http://localhost:8000")
        print("   2. Upload your real store documents via Postman")
        print("   3. Run the database seed script if not done")
        print("   4. Deploy to production when ready")
        
    elif tests_passed >= 3:
        print("⚠️ Enterprise RAG is mostly working with some issues")
        print("🔧 Review the failed tests and check:")
        print("   - Database has been seeded with products/services")
        print("   - API keys are valid and have sufficient credits")
        print("   - Vector search is returning quality results")
        
    else:
        print("❌ Enterprise RAG needs significant attention")
        print("🚨 Critical issues found. Please check:")
        print("   - OpenAI API key and credits")
        print("   - Pinecone configuration and credits")
        print("   - Database connection and seeded data")
        print("   - Server logs for detailed error information")

if __name__ == "__main__":
    asyncio.run(main())