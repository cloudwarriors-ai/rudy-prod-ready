#!/usr/bin/env python3

import requests
import json
import time

# Test the business hours auto attendant endpoint
def test_business_hours_aa():
    base_url = "http://127.0.0.1:9000"
    
    print("=== Testing Business Hours Auto Attendant Creation ===")
    
    # Step 1: Authenticate
    print("1. Authenticating...")
    auth_response = requests.post(f"{base_url}/auth/connect", json={})
    if auth_response.status_code != 200:
        print(f"❌ Authentication failed: {auth_response.text}")
        return
    
    session_data = auth_response.json()
    session_id = session_data["session_id"]
    print(f"✅ Authenticated. Session ID: {session_id}")
    
    # Step 2: Check auth status
    print("2. Checking auth status...")
    status_response = requests.get(f"{base_url}/auth/status", params={"session_id": session_id})
    print(f"Auth status: {status_response.json()}")
    
    # Step 3: Test business hours AA creation with minimal config
    print("3. Creating minimal business hours Auto Attendant...")
    
    aa_request = {
        "name": f"BH-Test-{int(time.time())}",
        "greeting_prompt": "Welcome to our test company",
        "business_hours_greeting": "Business hours are 9 to 5, Monday to Friday",
        "after_hours_greeting": "We are currently closed",
        "menu_options": [],  # Start with no menu options
        "business_hours": {
            "start_time": "09:00",
            "end_time": "17:00", 
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "timezone": "UTC"
        },
        "language_id": "en-US",
        "enable_voice_response": True
    }
    
    print(f"Request payload: {json.dumps(aa_request, indent=2)}")
    
    # Make the request
    create_response = requests.post(
        f"{base_url}/autoattendants/create-with-business-hours",
        params={"session_id": session_id},
        json=aa_request,
        timeout=180
    )
    
    print(f"Response status: {create_response.status_code}")
    print(f"Response body: {create_response.text}")
    
    if create_response.status_code == 200:
        result = create_response.json()
        print("✅ Business Hours Auto Attendant created successfully!")
        print(f"AA ID: {result.get('autoAttendant', {}).get('id')}")
        print(f"Schedule ID: {result.get('businessHours', {}).get('scheduleId')}")
        print(f"Business Hours: {result.get('businessHours', {}).get('hours')}")
        
        # Step 4: Verify by listing auto attendants
        print("4. Verifying creation by listing auto attendants...")
        list_response = requests.get(f"{base_url}/autoattendants", params={"session_id": session_id})
        if list_response.status_code == 200:
            attendants = list_response.json()
            print(f"Total auto attendants: {attendants.get('count', 0)}")
            for aa in attendants.get('attendants', []):
                if aa.get('name') == aa_request['name']:
                    print(f"✅ Found created AA: {aa.get('name')} (ID: {aa.get('identity')})")
                    print(f"   Call Flows: {aa.get('callFlows', 'N/A')}")
                    print(f"   Call Handling Associations: {aa.get('callHandlingAssociations', 'N/A')}")
        
    else:
        print(f"❌ Business Hours Auto Attendant creation failed")
        try:
            error_detail = create_response.json()
            print(f"Error details: {error_detail}")
        except:
            print(f"Raw error: {create_response.text}")

if __name__ == "__main__":
    test_business_hours_aa()