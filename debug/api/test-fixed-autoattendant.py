#!/usr/bin/env python3
"""
Test the fixed Auto Attendant creation API
Tests the working queue "demoqueueiscake" with its resource account
"""

import requests
import json
import time

API_BASE = "http://127.0.0.1:8000"

def test_autoattendant_creation():
    """Test Auto Attendant creation with the working queue"""
    
    print("=== TESTING FIXED AUTO ATTENDANT API ===")
    
    # Step 1: Create a PowerShell session via auth/connect
    print("\n1. Creating PowerShell session...")
    session_response = requests.post(f"{API_BASE}/auth/connect")
    
    if session_response.status_code != 200:
        print(f"❌ Failed to create session: {session_response.status_code}")
        print(session_response.text)
        return
    
    session_data = session_response.json()
    session_id = session_data["session_id"]
    print(f"✅ Session created: {session_id}")
    
    # Step 2: Test Auto Attendant creation with the working queue
    print("\n2. Creating Auto Attendant with working queue...")
    
    # Use the working queue ID from our investigation
    autoattendant_data = {
        "name": f"Test AA Fixed - {int(time.time())}",
        "languageId": "en-US",
        "greetingPrompt": "Welcome to our test auto attendant. Press 1 for demo queue.",
        "menuOptions": [
            {
                "dtmfResponse": "1",
                "prompt": "Demo Queue",
                "callTargetType": "CallQueue", 
                "callTargetId": "4c642d0d-6340-4f22-8294-0e0bc5dc8d41"  # demoqueueiscake queue ID
            }
        ],
        "enableVoiceResponse": True
    }
    
    print(f"📤 Request data: {json.dumps(autoattendant_data, indent=2)}")
    
    aa_response = requests.post(
        f"{API_BASE}/autoattendants",
        params={"session_id": session_id},
        json=autoattendant_data
    )
    
    print(f"\n📥 Response status: {aa_response.status_code}")
    print(f"📥 Response content: {aa_response.text}")
    
    if aa_response.status_code == 200:
        aa_data = aa_response.json()
        print(f"✅ Auto Attendant created successfully!")
        print(f"   Name: {aa_data.get('name')}")
        print(f"   Identity: {aa_data.get('identity')}")
        print(f"   Status: {aa_data.get('status')}")
        
        # Save success details
        with open("/root/code/teams-sdk/debug/logs/api-autoattendant-success.log", "a") as f:
            f.write(f"\n{time.strftime('%Y-%m-%d %H:%M:%S')} - SUCCESS\n")
            f.write(f"Request: {json.dumps(autoattendant_data, indent=2)}\n")
            f.write(f"Response: {json.dumps(aa_data, indent=2)}\n")
            f.write("-" * 50 + "\n")
    else:
        print(f"❌ Auto Attendant creation failed!")
        try:
            error_data = aa_response.json()
            print(f"   Error: {error_data.get('detail', 'Unknown error')}")
        except:
            print(f"   Raw error: {aa_response.text}")
        
        # Save error details
        with open("/root/code/teams-sdk/debug/logs/api-autoattendant-errors.log", "a") as f:
            f.write(f"\n{time.strftime('%Y-%m-%d %H:%M:%S')} - ERROR\n")
            f.write(f"Status: {aa_response.status_code}\n")
            f.write(f"Request: {json.dumps(autoattendant_data, indent=2)}\n")
            f.write(f"Response: {aa_response.text}\n")
            f.write("-" * 50 + "\n")
    
    # Step 3: Clean up session
    print("\n3. Cleaning up session...")
    cleanup_response = requests.post(f"{API_BASE}/auth/disconnect", params={"session_id": session_id})
    if cleanup_response.status_code == 200:
        print("✅ Session cleaned up")
    else:
        print(f"⚠️  Session cleanup failed: {cleanup_response.status_code}")

if __name__ == "__main__":
    try:
        test_autoattendant_creation()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Make sure it's running on http://127.0.0.1:9000")
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        
    print("\n=== TEST COMPLETE ===")