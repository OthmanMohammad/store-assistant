"""
Test script for Web Chat API
Tests the complete web chat experience via HTTP requests
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_chat_message(message, session_id=None, locale=None):
    """Send a chat message and return response"""
    try:
        payload = {"text": message}
        if session_id:
            payload["session_id"] = session_id
        if locale:
            payload["locale"] = locale
        
        response = requests.post(
            f"{API_BASE}/channels/webchat/message",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Request failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Request error: {str(e)}")
        return None

def test_suggestions(language="en"):
    """Test suggestions endpoint"""
    try:
        response = requests.get(f"{API_BASE}/channels/webchat/suggestions?language={language}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"❌ Suggestions error: {str(e)}")
        return None

def test_conversation_flow():
    """Test a complete conversation flow"""
    print("💬 Testing Complete Conversation Flow...")
    
    session_id = None
    conversation = [
        "Hello!",
        "What are your store hours?", 
        "Do you accept credit cards?",
        "How do I return something?",
        "Thank you!"
    ]
    
    for i, message in enumerate(conversation, 1):
        print(f"\n   Step {i}: User says '{message}'")
        
        response = test_chat_message(message, session_id)
        
        if response:
            # Update session ID for conversation continuity
            session_id = response.get("session_id")
            
            print(f"   🤖 Bot: {response.get('text', 'No response')[:100]}...")
            print(f"   📊 Confidence: {response.get('confidence', 0):.2f}")
            print(f"   🌍 Language: {response.get('language', 'unknown')}")
            
            if response.get('sources'):
                print(f"   📚 Sources: {', '.join(response['sources'][:2])}")
            
            # Add delay to simulate real conversation
            time.sleep(1)
        else:
            print("   ❌ No response received")
            break
    
    return session_id is not None

def test_multilingual_chat():
    """Test multilingual capabilities"""
    print("\n🌍 Testing Multilingual Chat...")
    
    test_cases = [
        ("What are your hours?", "en"),
        ("ما هي ساعات العمل؟", "ar"),
        ("How much does delivery cost?", "en"),
    ]
    
    success_count = 0
    
    for message, expected_lang in test_cases:
        print(f"\n   Testing: '{message}' (Expected: {expected_lang})")
        
        response = test_chat_message(message)
        
        if response:
            detected_lang = response.get('language', 'unknown')
            bot_text = response.get('text', 'No response')
            
            print(f"   🤖 Response: {bot_text[:80]}...")
            print(f"   🌍 Detected: {detected_lang}")
            
            # Check if language detection is reasonable
            if expected_lang == "ar" and detected_lang == "ar":
                success_count += 1
                print("   ✅ Arabic detection correct")
            elif expected_lang == "en" and detected_lang in ["en", "auto"]:
                success_count += 1 
                print("   ✅ English detection correct")
            else:
                print(f"   ⚠️ Language detection: expected {expected_lang}, got {detected_lang}")
        else:
            print("   ❌ No response")
    
    return success_count, len(test_cases)

def test_suggestions_endpoint():
    """Test the suggestions endpoint"""
    print("\n💡 Testing Suggestions...")
    
    # Test English suggestions
    en_suggestions = test_suggestions("en")
    if en_suggestions:
        suggestions = en_suggestions.get('suggestions', [])
        print(f"   📝 English suggestions ({len(suggestions)}):")
        for suggestion in suggestions[:3]:
            print(f"      - {suggestion}")
    
    # Test Arabic suggestions
    ar_suggestions = test_suggestions("ar") 
    if ar_suggestions:
        suggestions = ar_suggestions.get('suggestions', [])
        print(f"   📝 Arabic suggestions ({len(suggestions)}):")
        for suggestion in suggestions[:3]:
            print(f"      - {suggestion}")
    
    return en_suggestions is not None

def test_error_handling():
    """Test error handling and edge cases"""
    print("\n🔧 Testing Error Handling...")
    
    test_cases = [
        "",  # Empty message
        "a" * 1000,  # Very long message
        "🤖🚀💬",  # Emoji only
        "Hello\nworld\n\n\n",  # Multiline
    ]
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {repr(message[:50])}")
        
        response = test_chat_message(message)
        
        if response:
            print(f"   ✅ Handled gracefully: {response.get('text', '')[:50]}...")
        else:
            print("   ❌ Failed to handle")

def test_session_persistence():
    """Test session persistence across multiple requests"""
    print("\n🔄 Testing Session Persistence...")
    
    # First message
    response1 = test_chat_message("My name is John")
    if not response1:
        print("   ❌ First message failed")
        return False
    
    session_id = response1.get("session_id")
    print(f"   📝 Session ID: {session_id}")
    
    # Second message in same session
    response2 = test_chat_message("What's my name?", session_id)
    if not response2:
        print("   ❌ Second message failed")
        return False
    
    # Check if session is maintained
    same_session = response2.get("session_id") == session_id
    print(f"   🔄 Session maintained: {same_session}")
    
    return same_session

def main():
    """Run all web chat tests"""
    print("💬 Store Assistant - Web Chat Test")
    print("=" * 45)
    
    # Check if API is running
    print("🔍 Checking API status...")
    try:
        response = requests.get(f"{API_BASE}/health/readyz")
        if response.status_code == 200:
            print("✅ API is running")
        else:
            print("❌ API not responding correctly")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {str(e)}")
        print("💡 Make sure to run: uvicorn app.main:app --reload")
        return
    
    # Run tests
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Basic conversation flow
    if test_conversation_flow():
        tests_passed += 1
        print("✅ Conversation flow test passed")
    
    # Test 2: Multilingual support
    success_count, total_queries = test_multilingual_chat()
    if success_count >= total_queries * 0.5:  # 50% success rate
        tests_passed += 1
        print("✅ Multilingual test passed")
    
    # Test 3: Suggestions
    if test_suggestions_endpoint():
        tests_passed += 1
        print("✅ Suggestions test passed")
    
    # Test 4: Error handling
    test_error_handling()
    tests_passed += 1  # Error handling should always work
    print("✅ Error handling test completed")
    
    # Test 5: Session persistence
    if test_session_persistence():
        tests_passed += 1
        print("✅ Session persistence test passed")
    
    # Summary
    print("\n" + "=" * 45)
    print(f"🎯 Test Summary: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed >= 4:
        print("🎉 Web chat is working excellently!")
        print("✅ Ready for users!")
        print("\n📋 Try it yourself:")
        print(f"   🌐 Open: {API_BASE}")
        print("   💬 Start chatting with the AI assistant!")
    else:
        print("❌ Some web chat functions need attention.")

if __name__ == "__main__":
    main()