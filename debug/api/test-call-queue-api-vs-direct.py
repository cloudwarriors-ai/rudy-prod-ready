#!/usr/bin/env python3
"""
API vs Direct PowerShell Call Queue Comparison Test
Purpose: Compare API call queue listing with direct PowerShell results
Date: September 18, 2025
"""

import requests
import json
import subprocess
import time
from datetime import datetime

API_BASE = "http://127.0.0.1:9000"
LOG_FILE = "/root/code/teams-sdk/debug/logs/api-comparison.log"

def log_message(message, data=None):
    """Log message with timestamp"""
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "message": message,
        "data": data
    }
    
    print(f"[{timestamp}] {message}")
    if data:
        print(f"  Data: {data}")
    
    # Write to log file
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry, indent=2) + "\n")

def test_api_auth():
    """Test API authentication"""
    log_message("Testing API authentication...")
    
    try:
        response = requests.post(f"{API_BASE}/auth/connect")
        log_message("API auth response", {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        })
        return response.status_code == 200
    except Exception as e:
        log_message("API auth failed", {"error": str(e)})
        return False

def test_api_call_queues():
    """Test API call queue listing"""
    log_message("Testing API call queue listing...")
    
    # First connect
    auth_response = requests.post(f"{API_BASE}/auth/connect")
    if auth_response.status_code != 200:
        log_message("API auth failed", {"response": auth_response.text})
        return None
    
    session_id = auth_response.json().get("session_id")
    log_message("API authenticated", {"session_id": session_id})
    
    # List call queues
    try:
        params = {"session_id": session_id}
        response = requests.get(f"{API_BASE}/callqueues", params=params)
        log_message("API call queue listing", {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        })
        
        if response.status_code == 200:
            queues_data = response.json()
            return queues_data
        else:
            return None
            
    except Exception as e:
        log_message("API call queue listing failed", {"error": str(e)})
        return None
    finally:
        # Disconnect
        try:
            requests.post(f"{API_BASE}/auth/disconnect", params={"session_id": session_id})
        except:
            pass

def compare_results():
    """Compare direct PowerShell vs API results"""
    log_message("=== STARTING COMPARISON TEST ===")
    
    # Load direct PowerShell results from our previous test
    direct_results = {
        "success": True,
        "count": 13,
        "queues": [
            "Alpha Test Queue", "Debug Test Queue", "Finance Call Queue",
            "Fixed Alpha Queue", "Greg ETL 1 Queue", "Sales Call Queue", 
            "Support Call Queue", "Support Team", "Test Queue 2",
            "biggasscallqueue", "demoqueueiscake", "imppressivestuff",
            "superduper callqueue"
        ]
    }
    
    log_message("Direct PowerShell results (from previous test)", direct_results)
    
    # Test API
    api_results = test_api_call_queues()
    log_message("API results", api_results)
    
    # Compare
    if api_results is None:
        log_message("❌ COMPARISON FAILED: API returned no data")
        return
    
    if api_results.get("queues"):
        api_queue_names = [q.get("name", "Unknown") for q in api_results["queues"]]
        api_count = len(api_queue_names)
        
        log_message("✅ COMPARISON RESULTS", {
            "direct_count": direct_results["count"],
            "api_count": api_count,
            "match": api_count == direct_results["count"],
            "api_queue_names": api_queue_names,
            "direct_queue_names": direct_results["queues"]
        })
        
        if api_count == direct_results["count"]:
            log_message("🎯 SUCCESS: API and Direct PowerShell returned same number of queues!")
        else:
            log_message("⚠️  MISMATCH: Different number of queues returned")
            
    else:
        log_message("❌ API ISSUE: No queues in API response", api_results)

def main():
    """Main test execution"""
    print("🧪 Teams SDK API vs Direct PowerShell Comparison")
    print("=" * 60)
    
    # Clear log file
    with open(LOG_FILE, "w") as f:
        f.write("")
    
    # Run comparison
    compare_results()
    
    print("\n📝 Full log available at:", LOG_FILE)

if __name__ == "__main__":
    main()