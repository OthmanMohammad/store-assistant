#!/usr/bin/env python3
"""
Arabic Language Debug Script
Helps identify why Arabic queries are getting English responses
"""

import asyncio
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from app.services.rag_service import enterprise_rag_service
from app.services.vector_service import vector_service
from app.database import SessionLocal

async def test_language_detection():
    """Test the language detection function directly"""
    print("🌍 Testing Language Detection Function...")
    
    test_cases = [
        "ما هي ساعات العمل؟",
        "كم سعر آيفون 15؟", 
        "هل تقدمون خدمة التوصيل؟",
        "What are your store hours?",
        "How much does iPhone cost?",
        "مرحبا، كيف الحال؟ What time do you open?",  # Mixed
    ]
    
    for text in test_cases:
        detected = enterprise_rag_service._detect_language(text)
        arabic_chars = enterprise_rag_service._count_arabic_chars(text)
        total_chars = len([c for c in text if c.isalpha()])
        ratio = arabic_chars / total_chars if total_chars > 0 else 0
        
        print(f"Text: '{text}'")
        print(f"  Arabic chars: {arabic_chars}/{total_chars} ({ratio:.2%})")
        print(f"  Detected: {detected}")
        print()

async def test_vector_search_language_filtering():
    """Test if Arabic documents are properly stored and searchable"""
    print("📚 Testing Vector Search Language Filtering...")
    
    arabic_queries = [
        "ساعات العمل",
        "أسعار المنتجات", 
        "خدمة التوصيل"
    ]
    
    for query in arabic_queries:
        print(f"Query: '{query}'")
        
        # Search without language filter
        results_all = await vector_service.search_similar(query, top_k=5)
        print(f"  All results: {len(results_all)}")
        
        # Search with Arabic language filter
        results_ar = await vector_service.search_similar(
            query, 
            top_k=5, 
            filter_dict={"language": "ar"}
        )
        print(f"  Arabic-filtered results: {len(results_ar)}")
        
        # Show top results
        for i, result in enumerate(results_all[:2], 1):
            metadata = result.get('metadata', {})
            lang = metadata.get('language', 'unknown')
            text = metadata.get('text', '')[:100]
            print(f"    {i}. Language: {lang}, Score: {result['score']:.3f}")
            print(f"       Text: {text}...")
        print()

async def check_document_languages():
    """Check what languages are stored in your documents"""
    print("📄 Checking Document Languages in Vector Store...")
    
    # Search for any content to see what languages we have
    test_results = await vector_service.search_similar("test", top_k=20)
    
    languages = {}
    for result in test_results:
        lang = result.get('metadata', {}).get('language', 'unknown')
        languages[lang] = languages.get(lang, 0) + 1
    
    print("Languages in vector store:")
    for lang, count in languages.items():
        print(f"  {lang}: {count} chunks")
    
    # Show some Arabic examples if they exist
    arabic_examples = [r for r in test_results if r.get('metadata', {}).get('language') == 'ar']
    if arabic_examples:
        print(f"\nFound {len(arabic_examples)} Arabic chunks. Examples:")
        for i, result in enumerate(arabic_examples[:3], 1):
            text = result['metadata'].get('text', '')[:100]
            print(f"  {i}. {text}...")
    else:
        print("\n⚠️ No Arabic content found in vector store!")

async def test_system_prompt_selection():
    """Test if the correct system prompt is being used"""
    print("💬 Testing System Prompt Selection...")
    
    # Test Arabic query
    arabic_query = "ما هي ساعات العمل؟"
    detected_lang = enterprise_rag_service._detect_language(arabic_query)
    
    print(f"Query: '{arabic_query}'")
    print(f"Detected language: {detected_lang}")
    
    # Get the system prompt that would be used
    system_prompt = enterprise_rag_service._build_enterprise_system_prompt(detected_lang)
    
    print("System prompt preview:")
    print(system_prompt[:200] + "...")
    
    # Check if it's actually in Arabic
    arabic_in_prompt = enterprise_rag_service._count_arabic_chars(system_prompt)
    print(f"Arabic characters in system prompt: {arabic_in_prompt}")
    
    if detected_lang == "ar" and arabic_in_prompt > 50:
        print("✅ Arabic system prompt correctly selected")
    else:
        print("❌ System prompt issue detected")

async def test_full_arabic_pipeline():
    """Test the complete pipeline with Arabic input"""
    print("🔄 Testing Full Arabic Pipeline...")
    
    db = SessionLocal()
    
    try:
        arabic_query = "ما هي ساعات عمل المتجر؟"
        print(f"Testing query: '{arabic_query}'")
        
        # Generate response
        response = await enterprise_rag_service.generate_response(
            user_message=arabic_query,
            language="auto",  # Let it auto-detect
            db=db
        )
        
        print("Response analysis:")
        print(f"  Detected language: {response.get('language')}")
        print(f"  Confidence: {response.get('confidence', 0):.3f}")
        print(f"  Sources: {response.get('sources', [])}")
        
        answer = response.get('answer', '')
        print(f"  Answer: {answer[:200]}...")
        
        # Check if response is in Arabic
        arabic_chars_response = enterprise_rag_service._count_arabic_chars(answer)
        total_chars_response = len([c for c in answer if c.isalpha()])
        
        if total_chars_response > 0:
            arabic_ratio = arabic_chars_response / total_chars_response
            print(f"  Arabic ratio in response: {arabic_ratio:.2%}")
            
            if arabic_ratio > 0.3:
                print("✅ Response is in Arabic")
            else:
                print("❌ Response is in English despite Arabic query")
        
    finally:
        db.close()

async def diagnose_arabic_issues():
    """Run complete Arabic diagnosis"""
    print("🏥 Arabic Language Diagnosis")
    print("=" * 50)
    
    await test_language_detection()
    await check_document_languages() 
    await test_vector_search_language_filtering()
    await test_system_prompt_selection()
    await test_full_arabic_pipeline()
    
    print("\n📋 Common Issues & Solutions:")
    print("1. Documents not tagged as Arabic:")
    print("   - Re-upload PDFs to ensure proper language detection")
    print("   - Check document processing logs")
    
    print("\n2. Language detection threshold too low:")
    print("   - Adjust arabic_ratio threshold in _detect_language()")
    
    print("\n3. OpenAI model defaulting to English:")
    print("   - Strengthen Arabic system prompts")
    print("   - Add explicit language instructions")
    
    print("\n4. Mixed content in context:")
    print("   - Improve language filtering in vector search")
    print("   - Separate Arabic/English document processing")

if __name__ == "__main__":
    asyncio.run(diagnose_arabic_issues())