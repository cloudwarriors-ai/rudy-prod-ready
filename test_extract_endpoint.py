#!/usr/bin/env python3
"""
Test script for the new comprehensive Teams data extraction endpoint
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:9000"

def test_extract_endpoint():
    """Test the /extract/all endpoint"""
    print("🧪 Testing Teams Data Extraction Endpoint")
    print("=" * 50)
    
    try:
        # Connect and get session
        print("1. Connecting to Teams...")
        auth_response = requests.post(f"{BASE_URL}/auth/connect")
        
        if auth_response.status_code != 200:
            print(f"❌ Authentication failed: {auth_response.text}")
            return False
            
        session_data = auth_response.json()
        session_id = session_data["session_id"]
        print(f"✅ Connected with session: {session_id}")
        
        # Test the extraction endpoint
        print("\n2. Testing extraction endpoint...")
        extract_response = requests.get(f"{BASE_URL}/extract/all", params={"session_id": session_id})
        
        if extract_response.status_code != 200:
            print(f"❌ Extraction failed: {extract_response.text}")
            return False
            
        data = extract_response.json()
        print("✅ Extraction successful!")
        
        # Print summary
        print("\n📊 EXTRACTION SUMMARY")
        print("-" * 30)
        summary = data.get("summary", {})
        for key, value in summary.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        
        # Print warnings
        warnings = data.get("warnings", [])
        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)})")
            print("-" * 20)
            for warning in warnings:
                print(f"• {warning}")
        
        # Print counts by category
        print(f"\n📋 DETAILED COUNTS")
        print("-" * 20)
        print(f"Voice Users: {len(data.get('voiceUsers', []))}")
        print(f"Phone Numbers: {len(data.get('phoneNumbers', []))}")
        print(f"Auto Attendants: {len(data.get('autoAttendants', []))}")
        print(f"Call Queues: {len(data.get('callQueues', []))}")
        print(f"Application Instances: {len(data.get('applicationInstances', []))}")
        
        # Show sample data
        if data.get('phoneNumbers'):
            print(f"\n📞 PHONE NUMBERS")
            print("-" * 20)
            for phone in data['phoneNumbers']:
                assigned = "✅ Assigned" if phone.get('assignedPstnTargetId') else "❌ Unassigned"
                print(f"{phone.get('telephoneNumber')} - {phone.get('numberType')} - {assigned}")
        
        if data.get('voiceUsers'):
            print(f"\n👥 VOICE USERS")
            print("-" * 15)
            for user in data['voiceUsers']:
                phone = user.get('lineURI') or "No phone"
                print(f"{user.get('displayName')} ({user.get('userPrincipalName')}) - {phone}")
        
        print(f"\n✅ Test completed successfully!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running on port 9000?")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_extract_endpoint()
    if success:
        print("\n🎉 All tests passed! The extraction endpoint is working correctly.")
    else:
        print("\n💥 Tests failed. Check the server logs for details.")