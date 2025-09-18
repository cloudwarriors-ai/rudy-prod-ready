#!/usr/bin/env python3

import requests
import json
import uuid
import time

def test_session_user_creation():
    base_url = "http://localhost:8001"
    
    # Manually create a session by directly calling the API
    # For testing, we'll simulate what a successful auth would return
    fake_session_id = str(uuid.uuid4())
    
    print(f"Testing session-based user creation with fake session: {fake_session_id}")
    
    user_data = {
        "accountEnabled": True,
        "displayName": "Session Test User 1", 
        "userPrincipalName": "sessiontestuser1@cloudwarriors.onmicrosoft.com",
        "mailNickname": "sessiontestuser1",
        "password": "SessionTest@P@ssw0rd123!",
        "forceChangePassword": True
    }
    
    print("Testing /users/session endpoint...")
    start_time = time.time()
    
    response = requests.post(f"{base_url}/users/session?session_id={fake_session_id}", 
                           json=user_data,
                           timeout=30)
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print(f"Time taken: {elapsed:.2f} seconds")
    
    # Also test the direct endpoint for comparison
    print("\nTesting /users/direct endpoint for comparison...")
    user_data["displayName"] = "Direct Test User 6"
    user_data["userPrincipalName"] = "directtestuser6@cloudwarriors.onmicrosoft.com"
    user_data["mailNickname"] = "directtestuser6"
    
    start_time = time.time()
    
    response = requests.post(f"{base_url}/users/direct", 
                           json=user_data,
                           timeout=120)
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print(f"Time taken: {elapsed:.2f} seconds")

if __name__ == "__main__":
    test_session_user_creation()