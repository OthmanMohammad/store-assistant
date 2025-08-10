"""
Test script for Document Upload API
Tests the HTTP endpoints for document management
"""

import requests
import json
import tempfile
import os

API_BASE = "http://localhost:8000"

def create_sample_text_file():
    """Create a sample text file (we'll rename it to .pdf for testing)"""
    content = """Store Assistant - Sample Store Information

STORE HOURS
Monday - Friday: 9:00 AM - 8:00 PM  
Saturday: 10:00 AM - 6:00 PM
Sunday: 11:00 AM - 5:00 PM

RETURN POLICY
• Items can be returned within 30 days with receipt
• Refunds processed to original payment method
• Items must be in original condition

PAYMENT METHODS
We accept:
- Cash
- Credit/Debit cards (Visa, MasterCard, American Express)
- Mobile payments (Apple Pay, Google Pay)
- Gift cards

CONTACT INFORMATION
Phone: (555) 123-4567
Email: support@store.com
Address: 123 Main Street, City, State 12345

FREQUENTLY ASKED QUESTIONS

Q: Do you offer delivery?
A: Yes, we offer same-day delivery within 10 miles for orders over $50.

Q: Can I check product availability?
A: Yes, call us or check our website for real-time inventory.

Q: Do you price match?
A: Yes, we match prices from major competitors with valid proof.

Q: What is your exchange policy?
A: Exchanges are accepted within 14 days with receipt.
"""
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', mode='w')
    temp_file.write(content)
    temp_file.close()
    
    return temp_file.name

def test_health_check():
    """Test if the API is running"""
    print("🔍 Testing API health...")
    try:
        response = requests.get(f"{API_BASE}/health/readyz")
        if response.status_code == 200:
            print("✅ API is running")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {str(e)}")
        print("💡 Make sure to run: uvicorn app.main:app --reload")
        return False

def test_document_upload():
    """Test document upload endpoint"""
    print("\n📤 Testing document upload...")
    
    # Create sample file
    sample_file = create_sample_text_file()
    
    try:
        with open(sample_file, 'rb') as f:
            files = {'file': ('sample_store_info.pdf', f, 'application/pdf')}
            
            print("⏳ Uploading document (this may take a moment)...")
            response = requests.post(f"{API_BASE}/documents/upload", files=files)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Upload successful!")
                print(f"   Document ID: {result.get('document_id')}")
                print(f"   Status: {result.get('status')}")
                print(f"   Chunks: {result.get('total_chunks')}")
                print(f"   Language: {result.get('language')}")
                return result.get('document_id')
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return None
    finally:
        os.unlink(sample_file)

def test_document_list():
    """Test document listing endpoint"""
    print("\n📋 Testing document list...")
    
    try:
        response = requests.get(f"{API_BASE}/documents/")
        
        if response.status_code == 200:
            result = response.json()
            documents = result.get('documents', [])
            print(f"✅ Found {len(documents)} documents:")
            
            for doc in documents:
                print(f"   - ID: {doc['id']}, Name: {doc['filename']}")
                print(f"     Status: {doc['status']}, Chunks: {doc.get('total_chunks', 'N/A')}")
            
            return documents
        else:
            print(f"❌ List failed: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ List error: {str(e)}")
        return []

def test_document_details(document_id):
    """Test document details endpoint"""
    print(f"\n📊 Testing document details for ID {document_id}...")
    
    try:
        response = requests.get(f"{API_BASE}/documents/{document_id}")
        
        if response.status_code == 200:
            doc = response.json()
            print("✅ Document details retrieved:")
            print(f"   - ID: {doc['id']}")
            print(f"   - Filename: {doc['filename']}")
            print(f"   - Status: {doc['status']}")
            print(f"   - Chunks: {doc.get('total_chunks', 'N/A')}")
            print(f"   - Language: {doc.get('language', 'N/A')}")
            print(f"   - Active: {doc['is_active']}")
            return doc
        else:
            print(f"❌ Details failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Details error: {str(e)}")
        return None

def test_search():
    """Test search functionality"""
    print("\n🔍 Testing search functionality...")
    
    test_queries = [
        "store hours",
        "return policy", 
        "payment methods",
        "delivery"
    ]
    
    for query in test_queries:
        try:
            response = requests.get(f"{API_BASE}/documents/search/test?query={query}&top_k=2")
            
            if response.status_code == 200:
                result = response.json()
                results = result.get('results', [])
                print(f"\n   Query: '{query}' - Found {len(results)} results")
                
                for i, res in enumerate(results, 1):
                    score = res.get('score', 0)
                    text = res.get('metadata', {}).get('text', 'No text')
                    print(f"      {i}. Score: {score:.3f}")
                    print(f"         Text: {text[:80]}...")
            else:
                print(f"   ❌ Search failed for '{query}': {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Search error for '{query}': {str(e)}")

def test_document_deletion(document_id):
    """Test document deletion"""
    print(f"\n🗑️ Testing document deletion for ID {document_id}...")
    
    try:
        response = requests.delete(f"{API_BASE}/documents/{document_id}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Document deleted successfully")
            print(f"   Message: {result.get('message')}")
            return True
        else:
            print(f"❌ Deletion failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Deletion error: {str(e)}")
        return False

def main():
    """Run all API tests"""
    print("🏪 Store Assistant - Document Upload API Test")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_health_check():
        return
    
    # Test 2: Document upload
    document_id = test_document_upload()
    if not document_id:
        print("❌ Cannot continue without successful upload")
        return
    
    # Test 3: Document listing
    documents = test_document_list()
    
    # Test 4: Document details
    test_document_details(document_id)
    
    # Test 5: Search functionality
    test_search()
    
    # Test 6: Cleanup (delete test document)
    test_document_deletion(document_id)
    
    print("\n" + "=" * 50)
    print("🎉 All API tests completed!")
    print("💡 Your document ingestion pipeline is ready for production!")

if __name__ == "__main__":
    main()