"""
Test script for the UDCPR RAG API
"""

import requests
import json

# API base URL (change this when deployed to Render)
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_chat():
    """Test the chat endpoint"""
    print("\nTesting chat endpoint...")
    try:
        payload = {
            "message": "What are the building height regulations in UDCPR?",
            "session_id": "test-session-123"
        }
        
        response = requests.post(
            f"{BASE_URL}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data['response'][:200]}...")
            print(f"Session ID: {data['session_id']}")
            print(f"Sources: {len(data.get('sources', []))} sources found")
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_sessions():
    """Test the sessions endpoint"""
    print("\nTesting sessions endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/sessions")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("UDCPR RAG API Test Suite")
    print("=" * 30)
    
    # Test health
    health_ok = test_health()
    
    if health_ok:
        # Test chat
        chat_ok = test_chat()
        
        # Test sessions
        sessions_ok = test_sessions()
        
        print("\n" + "=" * 30)
        print("Test Results:")
        print(f"Health: {'✅' if health_ok else '❌'}")
        print(f"Chat: {'✅' if chat_ok else '❌'}")
        print(f"Sessions: {'✅' if sessions_ok else '❌'}")
    else:
        print("❌ Health check failed. Make sure the server is running and API keys are configured.")