#!/usr/bin/env python3
"""
Test Resource Account Verification API
Tests the new resource account verification endpoints
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:9000"

def test_resource_account_verification():
    """Test the resource account verification functionality"""

    print("=== RESOURCE ACCOUNT VERIFICATION TEST ===")

    # First, create a session
    print("\n1. Creating authentication session...")
    try:
        response = requests.post(f"{BASE_URL}/auth/connect", timeout=30)
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data["session_id"]
            print(f"✅ Session created: {session_id}")
        else:
            print(f"❌ Failed to create session: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return

    # Test 1: Check resource account for a known queue
    print("\n2. Testing resource account check for known queue...")
    test_queue_id = "4c642d0d-6340-4f22-8294-0e0bc5dc8d41"  # demoqueueiscake

    try:
        response = requests.get(
            f"{BASE_URL}/callqueues/{test_queue_id}/resource-account",
            params={"session_id": session_id},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Resource account check successful")
            print(f"   Queue: {result.get('queue_name', 'Unknown')}")
            print(f"   Has resource account: {result['has_resource_account']}")
            if result['has_resource_account']:
                print(f"   Resource account ID: {result['resource_account_id']}")
                print(f"   Method used: {result['method_used']}")
        else:
            print(f"❌ Resource account check failed: {response.status_code}")
            print(f"   Error: {response.text}")

    except Exception as e:
        print(f"❌ Error checking resource account: {e}")

    # Test 2: List all queues with resource accounts
    print("\n3. Testing list of queues with resource accounts...")

    try:
        response = requests.get(
            f"{BASE_URL}/callqueues/resource-accounts",
            params={"session_id": session_id},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Found {result['count']} queues with resource accounts")
            for queue in result['queues'][:3]:  # Show first 3
                print(f"   - {queue.get('name', 'Unknown')} ({queue.get('identity', '')[:8]}...)")
                print(f"     Resource: {queue.get('resource_account_name', 'Unknown')}")
        else:
            print(f"❌ Failed to list queues: {response.status_code}")
            print(f"   Error: {response.text}")

    except Exception as e:
        print(f"❌ Error listing queues: {e}")

    # Test 3: Try to create Auto Attendant with a queue that has resource account
    print("\n4. Testing Auto Attendant creation with verified queue...")

    aa_data = {
        "name": f"Test-AA-With-Resource-{int(time.time())}",
        "languageId": "en-US",
        "greetingPrompt": "Welcome to our test auto attendant",
        "menuOptions": [
            {
                "dtmfResponse": "1",
                "prompt": "Support",
                "callTargetType": "CallQueue",
                "callTargetId": test_queue_id
            }
        ],
        "enableVoiceResponse": True
    }

    try:
        response = requests.post(
            f"{BASE_URL}/autoattendants",
            params={"session_id": session_id},
            json=aa_data,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "created":
                print(f"✅ Auto Attendant created successfully")
                print(f"   Name: {result.get('name')}")
                print(f"   Identity: {result.get('identity')}")
            elif result.get("status") == "skipped":
                print(f"⚠️  Auto Attendant creation skipped")
                print(f"   Reason: {result.get('reason')}")
                available_queues = result.get("available_queues_with_resources", [])
                print(f"   Available alternatives: {len(available_queues)}")
            else:
                print(f"❌ Unexpected status: {result.get('status')}")
        else:
            print(f"❌ Auto Attendant creation failed: {response.status_code}")
            print(f"   Error: {response.text}")

    except Exception as e:
        print(f"❌ Error creating Auto Attendant: {e}")

    # Test 4: Try to create Auto Attendant with a queue that has NO resource account
    print("\n5. Testing Auto Attendant creation with queue without resource account...")

    # First, create a call queue without resource account
    print("   Creating test call queue without resource account...")

    queue_data = {
        "name": f"Test-Queue-No-Resource-{int(time.time())}",
        "languageId": "en-US",
        "routingMethod": "Attendant",
        "agents": ["demo@company.com"],  # This might not exist, but that's ok for testing
        "overflowThreshold": 20,
        "overflowAction": "Disconnect",
        "timeoutThreshold": 1200,
        "timeoutAction": "Disconnect",
        "agentAlertTime": 30,
        "conferenceMode": True,
        "useDefaultMusicOnHold": True
    }

    try:
        response = requests.post(
            f"{BASE_URL}/callqueues",
            params={"session_id": session_id},
            json=queue_data,
            timeout=60
        )

        if response.status_code == 200:
            queue_result = response.json()
            new_queue_id = queue_result.get("identity")
            print(f"   ✅ Test queue created: {queue_result.get('name')}")

            # Now try to create AA with this queue
            aa_data_no_resource = {
                "name": f"Test-AA-No-Resource-{int(time.time())}",
                "languageId": "en-US",
                "greetingPrompt": "Welcome to our test auto attendant",
                "menuOptions": [
                    {
                        "dtmfResponse": "1",
                        "prompt": "Support",
                        "callTargetType": "CallQueue",
                        "callTargetId": new_queue_id
                    }
                ],
                "enableVoiceResponse": True
            }

            response = requests.post(
                f"{BASE_URL}/autoattendants",
                params={"session_id": session_id},
                json=aa_data_no_resource,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "skipped":
                    print(f"   ✅ Auto Attendant creation correctly skipped")
                    print(f"   Reason: {result.get('reason')}")
                    suggestions = result.get("suggestions", [])
                    print(f"   Suggestions provided: {len(suggestions)}")
                else:
                    print(f"   ❌ Expected 'skipped' status, got: {result.get('status')}")
            else:
                print(f"   ❌ Auto Attendant creation failed: {response.status_code}")

        else:
            print(f"   ❌ Failed to create test queue: {response.status_code}")

    except Exception as e:
        print(f"❌ Error in test: {e}")

    # Clean up session
    print("\n6. Cleaning up session...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/disconnect",
            params={"session_id": session_id},
            timeout=30
        )
        if response.status_code == 200:
            print("✅ Session disconnected")
        else:
            print(f"⚠️  Failed to disconnect session: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Error disconnecting session: {e}")

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_resource_account_verification()