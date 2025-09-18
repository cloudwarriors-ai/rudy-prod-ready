#!/usr/bin/env python3

import requests
import json
import sys

# Test the user creation API
def test_user_creation():
    base_url = "http://localhost:8001"
    
    # First, try to connect
    print("1. Testing authentication...")
    auth_response = requests.post(f"{base_url}/auth/connect")
    print(f"Auth status: {auth_response.status_code}")
    print(f"Auth response: {auth_response.text}")
    
    if auth_response.status_code != 200:
        print("Authentication failed, trying direct user creation test...")
        # For testing, we'll create a PowerShell session manually
        import subprocess
        import uuid
        
        # Create a session ID and test the user creation logic directly
        session_id = str(uuid.uuid4())
        
        user_data = {
            "accountEnabled": True,
            "displayName": "API Test User 3",
            "userPrincipalName": "apitestuser3@cloudwarriors.onmicrosoft.com",
            "mailNickname": "apitestuser3", 
            "password": "APITest@P@ssw0rd123!",
            "forceChangePassword": True
        }
        
        print(f"2. Testing user creation with session: {session_id}")
        user_response = requests.post(f"{base_url}/users?session_id={session_id}", 
                                    json=user_data)
        print(f"User creation status: {user_response.status_code}")
        print(f"User creation response: {user_response.text}")
        
        return
    
    # If auth worked, get session ID and create user
    auth_data = auth_response.json()
    session_id = auth_data.get("session_id")
    
    if not session_id:
        print("No session ID returned from auth")
        return
    
    print(f"2. Testing user creation with session: {session_id}")
    
    user_data = {
        "accountEnabled": True,
        "displayName": "API Test User 3",
        "userPrincipalName": "apitestuser3@cloudwarriors.onmicrosoft.com",
        "mailNickname": "apitestuser3",
        "password": "APITest@P@ssw0rd123!",
        "forceChangePassword": True
    }
    
    user_response = requests.post(f"{base_url}/users?session_id={session_id}", 
                                json=user_data)
    print(f"User creation status: {user_response.status_code}")
    print(f"User creation response: {user_response.text}")

if __name__ == "__main__":
    test_user_creation()