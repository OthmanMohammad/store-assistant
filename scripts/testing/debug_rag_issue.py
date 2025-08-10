#!/usr/bin/env python3
"""
Debug script to identify where RAG service is failing
"""

import asyncio
import sys
import os
import traceback

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from app.services.rag_service import enterprise_rag_service
from app.database import SessionLocal

async def debug_rag_step_by_step():
    """Debug each step of RAG service"""
    
    print("🔍 Debugging RAG Service Step by Step")
    print("=" * 50)
    
    test_query = "What's the price of iPhone 15?"
    
    db = SessionLocal()
    
    try:
        # Step 1: Test query analysis
        print("1️⃣ Testing query analysis...")
        try:
            query_analysis = await enterprise_rag_service._analyze_query(test_query, "auto")
            print(f"✅ Query analysis successful")
            print(f"   Intent: {query_analysis.get('intent')}")
            print(f"   Language: {query_analysis.get('language')}")
            print(f"   Entities: {query_analysis.get('entities', {})}")
        except Exception as e:
            print(f"❌ Query analysis failed: {str(e)}")
            traceback.print_exc()
            return
        
        # Step 2: Test structured data retrieval
        print("\n2️⃣ Testing structured data retrieval...")
        try:
            structured_data = await enterprise_rag_service._retrieve_structured_data(query_analysis, db)
            print(f"✅ Structured data retrieval successful")
            print(f"   Products found: {len(structured_data.get('products', []))}")
            print(f"   Services found: {len(structured_data.get('services', []))}")
            print(f"   Store info: {bool(structured_data.get('store_info'))}")
            
            # Show sample product if found
            if structured_data.get('products'):
                sample_product = structured_data['products'][0]
                print(f"   Sample product: {sample_product.get('name')} - {sample_product.get('price_jod')} JOD")
        except Exception as e:
            print(f"❌ Structured data retrieval failed: {str(e)}")
            traceback.print_exc()
            return
        
        # Step 3: Test vector search
        print("\n3️⃣ Testing vector search...")
        try:
            unstructured_data = await enterprise_rag_service._retrieve_unstructured_data(test_query, query_analysis)
            print(f"✅ Vector search successful")
            print(f"   Chunks found: {len(unstructured_data.get('chunks', []))}")
            print(f"   Sources: {unstructured_data.get('sources', [])}")
            print(f"   Average score: {unstructured_data.get('average_score', 0):.3f}")
        except Exception as e:
            print(f"❌ Vector search failed: {str(e)}")
            traceback.print_exc()
            return
        
        # Step 4: Test prompt generation
        print("\n4️⃣ Testing prompt generation...")
        try:
            from app.services.prompt_service import prompt_service
            
            system_prompt = prompt_service.get_system_prompt(query_analysis.get('language', 'en'))
            print(f"✅ System prompt generated ({len(system_prompt)} chars)")
            
            data_context = enterprise_rag_service._build_data_context(structured_data, unstructured_data)
            print(f"✅ Data context built ({len(data_context)} chars)")
            
            user_prompt = prompt_service.get_user_prompt(
                user_message=test_query,
                language=query_analysis.get('language', 'en'),
                data_context=data_context,
                history_context="",
                query_analysis=query_analysis
            )
            print(f"✅ User prompt generated ({len(user_prompt)} chars)")
            
        except Exception as e:
            print(f"❌ Prompt generation failed: {str(e)}")
            traceback.print_exc()
            return
        
        # Step 5: Test OpenAI call (simplified)
        print("\n5️⃣ Testing OpenAI call...")
        try:
            response = enterprise_rag_service.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'OpenAI connection working'"}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            ai_response = response.choices[0].message.content.strip()
            print(f"✅ OpenAI call successful: {ai_response}")
            
        except Exception as e:
            print(f"❌ OpenAI call failed: {str(e)}")
            traceback.print_exc()
            return
        
        # Step 6: Test full response generation
        print("\n6️⃣ Testing full response generation...")
        try:
            response = await enterprise_rag_service._generate_hybrid_response(
                user_message=test_query,
                query_analysis=query_analysis,
                structured_data=structured_data,
                unstructured_data=unstructured_data,
                conversation_history=[],
                language="auto"
            )
            
            print(f"✅ Full response generation successful")
            print(f"   Answer: {response.get('answer', '')[:100]}...")
            print(f"   Confidence: {response.get('confidence', 0):.3f}")
            print(f"   Language: {response.get('language')}")
            
        except Exception as e:
            print(f"❌ Full response generation failed: {str(e)}")
            traceback.print_exc()
            return
        
        print("\n🎉 All steps completed successfully!")
        print("The issue might be in the main generate_response method or error handling.")
        
    finally:
        db.close()

async def test_simple_rag_call():
    """Test the main RAG service call"""
    print("\n🧪 Testing main RAG service call...")
    
    db = SessionLocal()
    
    try:
        response = await enterprise_rag_service.generate_response(
            user_message="What's the price of iPhone 15?",
            language="en",
            db=db
        )
        
        print(f"Response: {response.get('answer', '')[:200]}...")
        print(f"Confidence: {response.get('confidence', 0):.3f}")
        print(f"Language: {response.get('language')}")
        
        if response.get('confidence', 0) < 0.5:
            print("⚠️ Low confidence response - check data availability")
        
    except Exception as e:
        print(f"❌ Main RAG call failed: {str(e)}")
        traceback.print_exc()
    
    finally:
        db.close()

async def check_basic_setup():
    """Check basic setup requirements"""
    print("🔧 Checking basic setup...")
    
    # Check OpenAI API key
    from app.config import settings
    if settings.OPENAI_API_KEY:
        print("✅ OpenAI API key configured")
    else:
        print("❌ OpenAI API key missing")
    
    # Check vector service
    try:
        from app.services.vector_service import vector_service
        await vector_service.initialize()
        print("✅ Vector service initialized")
    except Exception as e:
        print(f"❌ Vector service failed: {str(e)}")
    
    # Check database
    try:
        db = SessionLocal()
        from app.models.product import Product
        product_count = db.query(Product).count()
        print(f"✅ Database connected - {product_count} products found")
        db.close()
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
    
    # Check prompt service
    try:
        from app.services.prompt_service import prompt_service
        system_prompt = prompt_service.get_system_prompt("en")
        print(f"✅ Prompt service working ({len(system_prompt)} chars)")
    except Exception as e:
        print(f"❌ Prompt service failed: {str(e)}")

async def main():
    """Run all debug checks"""
    await check_basic_setup()
    print()
    await debug_rag_step_by_step()
    print()
    await test_simple_rag_call()

if __name__ == "__main__":
    asyncio.run(main())