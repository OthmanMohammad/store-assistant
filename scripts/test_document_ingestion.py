"""
Test script for Document Ingestion Pipeline
Run this to verify your document processing is working
"""

import asyncio
import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.document_processor import document_processor
from app.services.document_service import document_service
from app.services.vector_service import vector_service
from app.database import SessionLocal
from app.config import settings

def create_sample_pdf():
    """Create a sample PDF for testing (text-based)"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create temporary PDF
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        
        # Create PDF content
        c = canvas.Canvas(temp_file.name, pagesize=letter)
        width, height = letter
        
        # Page 1
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 100, "Store Assistant - Sample Document")
        c.drawString(100, height - 130, "")
        c.drawString(100, height - 160, "Store Hours:")
        c.drawString(100, height - 180, "Monday - Friday: 9:00 AM - 8:00 PM")
        c.drawString(100, height - 200, "Saturday: 10:00 AM - 6:00 PM")
        c.drawString(100, height - 220, "Sunday: 11:00 AM - 5:00 PM")
        c.drawString(100, height - 260, "Return Policy:")
        c.drawString(100, height - 280, "Items can be returned within 30 days with receipt.")
        c.drawString(100, height - 300, "Refunds will be processed to original payment method.")
        c.drawString(100, height - 340, "Payment Methods:")
        c.drawString(100, height - 360, "We accept cash, credit cards, and mobile payments.")
        c.drawString(100, height - 380, "Contactless payments are preferred.")
        
        c.showPage()
        
        # Page 2
        c.drawString(100, height - 100, "Customer Service")
        c.drawString(100, height - 130, "")
        c.drawString(100, height - 160, "Contact Information:")
        c.drawString(100, height - 180, "Phone: +1 (555) 123-4567")
        c.drawString(100, height - 200, "Email: support@store.com")
        c.drawString(100, height - 240, "FAQ:")
        c.drawString(100, height - 260, "Q: Do you offer delivery?")
        c.drawString(100, height - 280, "A: Yes, we offer same-day delivery within 10 miles.")
        c.drawString(100, height - 320, "Q: Can I check product availability online?")
        c.drawString(100, height - 340, "A: Yes, visit our website or call the store.")
        
        c.save()
        return temp_file.name
        
    except ImportError:
        print("⚠️ reportlab not installed, creating text-based PDF manually...")
        
        # Create a simple text file instead
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w')
        temp_file.write("""Store Assistant - Sample Document

Store Hours:
Monday - Friday: 9:00 AM - 8:00 PM
Saturday: 10:00 AM - 6:00 PM
Sunday: 11:00 AM - 5:00 PM

Return Policy:
Items can be returned within 30 days with receipt.
Refunds will be processed to original payment method.

Payment Methods:
We accept cash, credit cards, and mobile payments.
Contactless payments are preferred.

Customer Service

Contact Information:
Phone: +1 (555) 123-4567
Email: support@store.com

FAQ:
Q: Do you offer delivery?
A: Yes, we offer same-day delivery within 10 miles.

Q: Can I check product availability online?
A: Yes, visit our website or call the store.
""")
        temp_file.close()
        return temp_file.name

async def test_document_processor():
    """Test document text extraction and chunking"""
    print("\n1️⃣ Testing Document Processor...")
    
    try:
        # Create sample document
        sample_file = create_sample_pdf()
        filename = "sample_store_info.pdf"
        
        print(f"📄 Created sample document: {filename}")
        
        # Test document processing
        result = document_processor.process_document(sample_file, filename)
        
        print(f"✅ Document processing completed:")
        print(f"   - Status: {result['status']}")
        print(f"   - Language: {result.get('language', 'unknown')}")
        print(f"   - Total chunks: {result.get('total_chunks', 0)}")
        print(f"   - Total words: {result.get('total_words', 0)}")
        
        if result["chunks"]:
            print(f"\n📝 Sample chunk:")
            first_chunk = result["chunks"][0]
            print(f"   Text preview: {first_chunk['text'][:200]}...")
            print(f"   Metadata: {first_chunk['metadata']}")
        
        # Clean up
        os.unlink(sample_file)
        
        return result
        
    except Exception as e:
        print(f"❌ Document processor test failed: {str(e)}")
        return None

async def test_full_ingestion():
    """Test complete document ingestion pipeline"""
    print("\n2️⃣ Testing Full Document Ingestion...")
    
    try:
        # Create sample document
        sample_file = create_sample_pdf()
        filename = "test_store_policy.pdf"
        
        # Get database session
        db = SessionLocal()
        
        try:
            print(f"🚀 Starting full ingestion: {filename}")
            
            # Test complete ingestion
            result = await document_service.ingest_document(
                file_path=sample_file,
                filename=filename,
                db=db,
                additional_metadata={"test": True, "category": "policy"}
            )
            
            print(f"✅ Ingestion completed:")
            print(f"   - Document ID: {result.get('document_id')}")
            print(f"   - Status: {result['status']}")
            print(f"   - Total chunks: {result.get('total_chunks')}")
            print(f"   - Language: {result.get('language')}")
            
            return result
            
        finally:
            db.close()
            os.unlink(sample_file)
        
    except Exception as e:
        print(f"❌ Full ingestion test failed: {str(e)}")
        return None

async def test_search_functionality():
    """Test search functionality with ingested documents"""
    print("\n3️⃣ Testing Search Functionality...")
    
    try:
        # Test various search queries
        test_queries = [
            "What are the store hours?",
            "How do I return an item?",
            "What payment methods do you accept?",
            "Do you offer delivery?",
            "Contact information"
        ]
        
        print("🔍 Testing search queries:")
        
        for query in test_queries:
            print(f"\n   Query: '{query}'")
            
            results = await vector_service.search_similar(query, top_k=2)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"      {i}. Score: {result['score']:.3f}")
                    print(f"         Text: {result['metadata']['text'][:100]}...")
                    print(f"         Source: {result['metadata']['source']}")
            else:
                print("      No results found")
        
        return True
        
    except Exception as e:
        print(f"❌ Search test failed: {str(e)}")
        return False

async def test_document_management():
    """Test document listing and deletion"""
    print("\n4️⃣ Testing Document Management...")
    
    try:
        db = SessionLocal()
        
        try:
            # List documents
            documents = await document_service.list_documents(db)
            print(f"📋 Found {len(documents)} documents:")
            
            for doc in documents:
                print(f"   - ID: {doc['id']}, Name: {doc['filename']}, Status: {doc['status']}")
            
            # Test document status check
            if documents:
                doc_id = documents[0]['id']
                status = await document_service.get_document_status(doc_id, db)
                print(f"\n📊 Document {doc_id} status: {status}")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Document management test failed: {str(e)}")
        return False

async def cleanup_test_data():
    """Clean up test documents"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        db = SessionLocal()
        
        try:
            # Get all test documents
            documents = await document_service.list_documents(db)
            test_docs = [doc for doc in documents if 'test' in doc['filename'].lower() or 'sample' in doc['filename'].lower()]
            
            if test_docs:
                print(f"🗑️ Found {len(test_docs)} test documents to clean up")
                
                for doc in test_docs:
                    success = await document_service.delete_document(doc['id'], db)
                    if success:
                        print(f"   ✅ Deleted: {doc['filename']}")
                    else:
                        print(f"   ❌ Failed to delete: {doc['filename']}")
            else:
                print("   No test documents found")
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Cleanup failed: {str(e)}")

async def main():
    """Run all tests"""
    print("🏪 Store Assistant - Document Ingestion Pipeline Test")
    print("=" * 60)
    
    # Check if vector service is initialized
    print("🔧 Checking prerequisites...")
    try:
        await vector_service.initialize()
        print("✅ Vector service ready")
    except Exception as e:
        print(f"❌ Vector service not ready: {str(e)}")
        return
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Document Processing
    result1 = await test_document_processor()
    if result1 and result1.get("status") == "completed":
        tests_passed += 1
    
    # Test 2: Full Ingestion
    result2 = await test_full_ingestion()
    if result2 and result2.get("status") == "completed":
        tests_passed += 1
    
    # Test 3: Search
    result3 = await test_search_functionality()
    if result3:
        tests_passed += 1
    
    # Test 4: Management
    result4 = await test_document_management()
    if result4:
        tests_passed += 1
    
    # Cleanup
    await cleanup_test_data()
    
    # Summary
    print("\n" + "=" * 60)
    print(f"🎯 Test Summary: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Document ingestion pipeline is working correctly!")
        print("✅ Ready to implement RAG-powered chat responses!")
    else:
        print("❌ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())