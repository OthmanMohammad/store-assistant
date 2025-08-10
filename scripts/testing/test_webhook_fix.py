#!/usr/bin/env python3
"""
Test script to verify webhook is working with new RAG service
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_webhook_endpoints():
    """Test all webhook endpoints"""
    
    print("🧪 Testing Webhook Endpoints")
    print("=" * 40)
    
    # Test 1: Debug endpoint
    print("1️⃣ Testing debug endpoint...")
    try:
        response = requests.post(
            f"{API_BASE}/channels/webchat/debug",
            json={"text": "What's the price of iPhone 15?", "locale": "en"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Debug endpoint working")
            print(f"   Confidence: {data.get('confidence', 0):.3f}")
            print(f"   Message: {data.get('message', 'No message')}")
            
            if data.get('confidence', 0) > 0.5:
                print("   🎉 RAG service working correctly!")
            else:
                print("   ⚠️ Low confidence response")
        else:
            print(f"❌ Debug endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Debug endpoint error: {str(e)}")
    
    # Test 2: Main message endpoint
    print("\n2️⃣ Testing main message endpoint...")
    try:
        response = requests.post(
            f"{API_BASE}/channels/webchat/message",
            json={"text": "What's the price of iPhone 15?", "locale": "en"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Message endpoint working")
            print(f"   Response: {data.get('text', '')[:100]}...")
            print(f"   Confidence: {data.get('confidence', 0):.3f}")
            print(f"   Language: {data.get('language', 'unknown')}")
            print(f"   Sources: {data.get('sources', [])}")
            
            if data.get('confidence', 0) > 0.5:
                print("   🎉 High confidence response!")
            else:
                print("   ⚠️ Low confidence - might be fallback")
        else:
            print(f"❌ Message endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Message endpoint error: {str(e)}")
    
    # Test 3: Arabic query
    print("\n3️⃣ Testing Arabic query...")
    try:
        response = requests.post(
            f"{API_BASE}/channels/webchat/message",
            json={"text": "ما هي ساعات العمل؟", "locale": "ar"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Arabic query working")
            print(f"   Response: {data.get('text', '')[:100]}...")
            print(f"   Language: {data.get('language', 'unknown')}")
            print(f"   Confidence: {data.get('confidence', 0):.3f}")
            
            # Check if response contains Arabic
            response_text = data.get('text', '')
            arabic_chars = len([c for c in response_text if '\u0600' <= c <= '\u06FF'])
            total_chars = len([c for c in response_text if c.isalpha()])
            
            if total_chars > 0:
                arabic_ratio = arabic_chars / total_chars
                print(f"   Arabic ratio: {arabic_ratio:.2%}")
                
                if arabic_ratio > 0.5:
                    print("   🎉 Arabic response confirmed!")
                else:
                    print("   ⚠️ Response is in English")
        else:
            print(f"❌ Arabic query failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Arabic query error: {str(e)}")
    
    # Test 4: Suggestions endpoint
    print("\n4️⃣ Testing suggestions endpoint...")
    try:
        response = requests.get(f"{API_BASE}/channels/webchat/suggestions?language=en")
        
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get('suggestions', [])
            print(f"✅ Suggestions working")
            print(f"   Found {len(suggestions)} suggestions")
            if suggestions:
                print(f"   Sample: {suggestions[0]}")
        else:
            print(f"❌ Suggestions failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Suggestions error: {str(e)}")

def test_web_ui_simulation():
    """Simulate what the web UI does"""
    print("\n🌐 Simulating Web UI Interaction")
    print("=" * 40)
    
    # Simulate a complete conversation
    session_id = None
    queries = [
        ("Hello!", "en"),
        ("What's the price of iPhone 15?", "en"),
        ("ما هي ساعات العمل؟", "ar"),
        ("Thank you!", "en")
    ]
    
    for i, (query, locale) in enumerate(queries, 1):
        print(f"\n{i}. Query: '{query}' ({locale})")
        
        try:
            payload = {"text": query, "locale": locale}
            if session_id:
                payload["session_id"] = session_id
            
            response = requests.post(
                f"{API_BASE}/channels/webchat/message",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                session_id = data.get('session_id')  # Maintain session
                
                print(f"   Response: {data.get('text', '')[:80]}...")
                print(f"   Confidence: {data.get('confidence', 0):.3f}")
                print(f"   Language: {data.get('language', 'unknown')}")
                
                if data.get('confidence', 0) > 0.5:
                    print("   ✅ Good response")
                else:
                    print("   ⚠️ Low confidence")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🏪 TechMart Palestine - Webhook Fix Test")
    print("Make sure your server is running on http://localhost:8000")
    print()
    
    test_webhook_endpoints()
    test_web_ui_simulation()
    
    print("\n" + "=" * 50)
    print("🎯 Summary:")
    print("If all tests show ✅ and high confidence (>0.5), the fix worked!")
    print("If you see ⚠️ or ❌, there are still issues to resolve.")
    print()
    print("🌐 Test the actual web UI at: http://localhost:8000")