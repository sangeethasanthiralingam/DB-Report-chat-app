#!/usr/bin/env python3
"""
Debug script to test the chat endpoint response
"""
import requests
import json

def test_chat_endpoint():
    """Test the chat endpoint with a simple query"""
    url = "http://localhost:5000/chat"
    
    # Test data
    test_data = {
        "question": "Show me all customers"
    }
    
    try:
        print("Sending request to:", url)
        print("Request data:", json.dumps(test_data, indent=2))
        
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\nResponse Data:")
                print(json.dumps(data, indent=2))
                
                # Check response structure
                if 'type' in data:
                    print(f"\nResponse Type: {data['type']}")
                if 'content' in data:
                    if isinstance(data['content'], list):
                        print(f"Content is list with {len(data['content'])} items")
                        if data['content']:
                            print(f"First item: {data['content'][0]}")
                    else:
                        print(f"Content: {data['content']}")
                if 'sql' in data:
                    print(f"SQL: {data['sql']}")
                    
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                print(f"Raw Response: {response.text}")
        else:
            print(f"Error Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Connection Error: Make sure Flask app is running on localhost:5000")
    except requests.exceptions.Timeout:
        print("Timeout Error: Request took too long")
    except Exception as e:
        print(f"Unexpected Error: {e}")

def test_simple_endpoint():
    """Test the simple test endpoint"""
    url = "http://localhost:5000/test_response"
    
    try:
        print(f"\nTesting simple endpoint: {url}")
        response = requests.get(url, timeout=10)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Test Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing simple endpoint: {e}")

if __name__ == "__main__":
    print("=== Debug Test Script ===")
    test_simple_endpoint()
    test_chat_endpoint() 