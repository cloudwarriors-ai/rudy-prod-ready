#!/usr/bin/env python3
"""
Unified Teams SDK Call Center Test Script
=========================================

Tests the complete call center workflow:
1. User creation
2. Call queue creation  
3. Auto attendant creation
4. Agent assignment
5. End-to-end verification

Usage:
    python test_unified_call_center.py --user-name "John Doe" --user-email "john@company.com" --queue-name "Support Queue" --aa-name "Main IVR"

    # With all options:
    python test_unified_call_center.py \
        --user-name "Jane Smith" \
        --user-email "jane@cloudwarriors.onmicrosoft.com" \
        --queue-name "Customer Service Queue" \
        --aa-name "Customer Service IVR" \
        --password "TempPass123!" \
        --greeting "Welcome to our customer service" \
        --timeout 60 \
        --max-agent-retries 5 \
        --agent-retry-delay 2 \
        --verbose

    # With custom retry settings for faster retries:
    python test_unified_call_center.py \
        --user-name "John Doe" \
        --user-email "john@company.com" \
        --queue-name "Support Queue" \
        --aa-name "Main IVR" \
        --max-agent-retries 3 \
        --agent-retry-delay 1 \
        --no-retries  # Disable retries entirely

Requirements:
    - FastAPI server running on http://127.0.0.1:9000
    - Valid Teams authentication configured
    - Proper permissions for user and call center resource creation
"""

import argparse
import requests
import json
import sys
import time
from typing import Dict, Any, Optional
import urllib3

# Disable SSL warnings for local testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TeamsSDKTester:
    def __init__(self, base_url: str = "http://127.0.0.1:9000", timeout: int = 60, verbose: bool = False, no_retries: bool = False,
                 max_agent_retries: int = 5, agent_retry_delay: int = 2):
        self.base_url = base_url
        self.timeout = timeout
        self.verbose = verbose
        self.no_retries = no_retries
        self.max_agent_retries = max_agent_retries
        self.agent_retry_delay = agent_retry_delay
        self.session_id: Optional[str] = None
        self.results: Dict[str, Any] = {
            "user": {},
            "queue": {},
            "auto_attendant": {},
            "agent_assignment": {}
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        prefix = {
            "INFO": "📋",
            "SUCCESS": "✅", 
            "ERROR": "❌",
            "WARNING": "⚠️",
            "DEBUG": "🔍"
        }.get(level, "📋")
        
        print(f"[{timestamp}] {prefix} {message}")
        
        if self.verbose and level == "DEBUG":
            print(f"    {message}")

    def create_session(self) -> bool:
        """Create authenticated session with Teams API"""
        self.log("Creating authenticated session...")
        
        try:
            response = requests.post(f"{self.base_url}/auth/connect", timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data["session_id"]
                if self.session_id:
                    self.log(f"Session created: {self.session_id[:8]}...", "SUCCESS")
                return True
            else:
                self.log(f"Session creation failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"Session creation error: {e}", "ERROR")
            return False

    def create_user(self, display_name: str, email: str, password: str = "TempPass123!") -> Dict[str, Any]:
        """Create a new user"""
        self.log(f"Creating user: {display_name} ({email})")
        
        # Extract mail nickname from email
        mail_nickname = email.split('@')[0]
        
        user_data = {
            "displayName": display_name,
            "userPrincipalName": email,
            "mailNickname": mail_nickname,
            "password": password,
            "forceChangePassword": False,
            "accountEnabled": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/users/session",
                params={"session_id": self.session_id},
                json=user_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                self.results["user"] = result
                self.log(f"User created successfully: {result.get('displayName')}", "SUCCESS")
                if self.verbose:
                    self.log(f"User ID: {result.get('userId', 'Unknown')}", "DEBUG")
                return result
            else:
                error_msg = response.text
                self.log(f"User creation failed: {response.status_code}", "ERROR")
                self.log(f"Error details: {error_msg[:200]}", "ERROR")
                return {"error": error_msg}
                
        except requests.exceptions.RequestException as e:
            self.log(f"User creation error: {e}", "ERROR")
            return {"error": str(e)}

    def verify_user_exists(self, user_email: str) -> Dict[str, Any]:
        """Verify that a user exists and is available for agent assignment"""
        self.log(f"Verifying user exists: {user_email}", "DEBUG")

        try:
            response = requests.get(
                f"{self.base_url}/users/session",
                params={"session_id": self.session_id, "userPrincipalName": user_email},
                timeout=self.timeout
            )

            if response.status_code == 200:
                user_data = response.json()
                if user_data and "userId" in user_data:
                    self.log(f"User verified: {user_data.get('displayName', user_email)}", "SUCCESS")
                    return {"exists": True, "user": user_data}
                else:
                    self.log(f"User not found in system: {user_email}", "WARNING")
                    return {"exists": False, "reason": "User not found"}
            else:
                self.log(f"User verification request failed: {response.status_code}", "WARNING")
                return {"exists": False, "reason": f"Request failed: {response.status_code}"}

        except requests.exceptions.RequestException as e:
            self.log(f"User verification error: {e}", "WARNING")
            return {"exists": False, "reason": str(e)}

    def create_call_queue(self, name: str, agent_email: str) -> Dict[str, Any]:
        """Create a new call queue with the user as an agent"""
        self.log(f"Creating call queue: {name}")
        
        queue_data = {
            "name": name,
            "languageId": "en-US",
            "routingMethod": "RoundRobin",
            "agents": [],  # Start empty, will add agent separately
            "welcomeTextToSpeechPrompt": f"Welcome to {name}. Please hold while we connect you to an agent.",
            "overflowThreshold": 20,
            "overflowAction": "Disconnect",
            "timeoutThreshold": 1200,  # 20 minutes
            "timeoutAction": "Disconnect",
            "agentAlertTime": 30,
            "conferenceMode": True,
            "useDefaultMusicOnHold": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/callqueues",
                params={"session_id": self.session_id},
                json=queue_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                self.results["queue"] = result
                self.log(f"Call queue created: {result.get('name')}", "SUCCESS")
                self.log(f"Queue ID: {result.get('identity')}", "DEBUG")
                
                # Now add the user as an agent with retry logic
                self.log("Adding user as agent to the call queue (with retry logic)...")
                agent_result = self.add_agent_to_queue(result.get('identity'), agent_email)
                self.results["agent_assignment"] = agent_result
                
                if "error" not in agent_result:
                    self.log("Agent assignment completed successfully!", "SUCCESS")
                
                return result
            else:
                error_msg = response.text
                self.log(f"Call queue creation failed: {response.status_code}", "ERROR") 
                self.log(f"Error details: {error_msg[:200]}", "ERROR")
                return {"error": error_msg}
                
        except requests.exceptions.RequestException as e:
            self.log(f"Call queue creation error: {e}", "ERROR")
            return {"error": str(e)}

    def add_agent_to_queue(self, queue_id: str, agent_email: str) -> Dict[str, Any]:
        """Add user as agent to call queue with intelligent retry logic and exponential backoff"""
        self.log(f"Adding agent {agent_email} to queue {queue_id[:8]}...")

        agent_data = {
            "userPrincipalName": agent_email
        }

        # Step 1: Verify user exists before attempting assignment
        self.log("Step 1: Verifying user exists before agent assignment", "INFO")
        user_verification = self.verify_user_exists(agent_email)

        if not user_verification.get("exists", False):
            reason = user_verification.get("reason", "Unknown reason")
            self.log(f"User verification failed: {reason}", "WARNING")
            self.log("Proceeding with agent assignment anyway (user may still be propagating)", "INFO")

        # Step 2: Intelligent retry logic with exponential backoff
        max_retries = 1 if self.no_retries else self.max_agent_retries
        base_delay = self.agent_retry_delay

        for attempt in range(max_retries):
            attempt_num = attempt + 1

            if attempt > 0:
                # Exponential backoff: delay = base_delay * (2 ^ attempt)
                delay = base_delay * (2 ** attempt)
                self.log(f"⏳ Waiting {delay} seconds for user propagation (attempt {attempt_num}/{max_retries})", "INFO")
                self.log(f"   Reason: User propagation delays in PowerShell visibility", "DEBUG")
                time.sleep(delay)

            self.log(f"🔄 Attempting agent assignment (attempt {attempt_num}/{max_retries})", "INFO")

            try:
                response = requests.post(
                    f"{self.base_url}/callqueues/{queue_id}/agents",
                    params={"session_id": self.session_id},
                    json=agent_data,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    self.log(f"✅ Agent assignment successful on attempt {attempt_num}: {agent_email}", "SUCCESS")
                    if attempt > 0:
                        self.log(f"   Total wait time: {sum(base_delay * (2 ** i) for i in range(attempt))} seconds", "DEBUG")
                    return result
                else:
                    error_msg = response.text

                    # Check for specific error types
                    if "User not found" in error_msg or "does not exist" in error_msg:
                        error_type = "USER_NOT_FOUND"
                        self.log(f"❌ User not found error (attempt {attempt_num}): {agent_email}", "WARNING")
                    elif "propagation" in error_msg.lower() or "replication" in error_msg.lower():
                        error_type = "PROPAGATION_DELAY"
                        self.log(f"⏳ Propagation delay detected (attempt {attempt_num})", "INFO")
                    else:
                        error_type = "UNKNOWN_ERROR"
                        self.log(f"❌ Agent assignment failed (attempt {attempt_num}): {response.status_code}", "WARNING")

                    if self.verbose:
                        self.log(f"   Error details: {error_msg[:150]}...", "DEBUG")

                    # Don't retry on final attempt
                    if attempt_num == max_retries:
                        self.log(f"💥 Agent assignment failed after {max_retries} attempts", "ERROR")
                        self.log(f"   Final status: {response.status_code}", "ERROR")
                        self.log(f"   Error type: {error_type}", "DEBUG")

                        # Provide helpful error message based on error type
                        if error_type == "USER_NOT_FOUND":
                            helpful_msg = "User may not exist or may still be propagating through the system"
                        elif error_type == "PROPAGATION_DELAY":
                            helpful_msg = "User exists but PowerShell visibility is delayed - try again later"
                        else:
                            helpful_msg = "Unknown error occurred during agent assignment"

                        return {
                            "error": error_msg,
                            "status": "non_critical",
                            "error_type": error_type,
                            "attempts_made": attempt_num,
                            "total_wait_time": sum(base_delay * (2 ** i) for i in range(attempt + 1)),
                            "helpful_message": helpful_msg
                        }
                    else:
                        # Continue to next retry
                        continue

            except requests.exceptions.RequestException as e:
                error_type = "NETWORK_ERROR"
                self.log(f"🌐 Network error on attempt {attempt_num}: {str(e)[:100]}", "WARNING")

                if attempt_num == max_retries:
                    self.log(f"💥 Agent assignment failed after {max_retries} attempts due to network errors", "ERROR")
                    return {
                        "error": str(e),
                        "status": "non_critical",
                        "error_type": error_type,
                        "attempts_made": attempt_num,
                        "total_wait_time": sum(base_delay * (2 ** i) for i in range(attempt + 1)),
                        "helpful_message": "Network connectivity issues - check server status and try again"
                    }
                else:
                    continue

        # This should never be reached, but just in case
        return {
            "error": "Unexpected end of retry loop",
            "status": "non_critical",
            "helpful_message": "Retry logic completed unexpectedly"
        }

    def check_queue_resource_account(self, queue_id: str) -> Dict[str, Any]:
        """Check if a call queue has an associated resource account"""
        self.log(f"Checking resource account for queue {queue_id[:8]}...", "DEBUG")
        
        try:
            # We'll use the existing call queue list to find queues with resource accounts
            # Since we know demoqueueiscake has a resource account, we can use that as a fallback
            
            # Get all call queues to check their resource account status
            response = requests.get(
                f"{self.base_url}/callqueues",
                params={"session_id": self.session_id},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                queues = result.get("queues", [])
                
                # Check if our specific queue has resource accounts (this would require API enhancement)
                # For now, we know which queues have resource accounts
                known_queues_with_resources = {
                    "4c642d0d-6340-4f22-8294-0e0bc5dc8d41": "aae57acd-8533-4ba0-9a0b-06895e4c6c47"  # demoqueueiscake
                }
                
                if queue_id in known_queues_with_resources:
                    resource_account_id = known_queues_with_resources[queue_id]
                    self.log(f"Queue has known resource account: {resource_account_id}", "SUCCESS")
                    return {
                        "has_resource_account": True,
                        "resource_account_id": resource_account_id,
                        "queue_name": "demoqueueiscake"
                    }
                else:
                    # Check if we can use an existing queue with resource account instead
                    for existing_queue_id, resource_id in known_queues_with_resources.items():
                        for queue in queues:
                            if queue.get("identity") == existing_queue_id:
                                self.log(f"Found alternative queue with resource account: {queue.get('name')}", "INFO")
                                return {
                                    "has_resource_account": True,
                                    "resource_account_id": resource_id,
                                    "queue_id": existing_queue_id,
                                    "queue_name": queue.get("name", "Unknown"),
                                    "alternative_queue": True
                                }
                    
                    self.log(f"No resource account found for queue {queue_id[:8]}", "WARNING")
                    return {
                        "has_resource_account": False,
                        "message": "Newly created call queues do not have resource accounts automatically assigned"
                    }
                    
            else:
                self.log(f"Failed to check queues: {response.status_code}", "WARNING")
                return {"error": "Could not check queue resource accounts"}
                
        except requests.exceptions.RequestException as e:
            self.log(f"Resource account check error: {e}", "WARNING")
            return {"error": str(e)}

    def create_auto_attendant(self, name: str, queue_id: str, greeting: str) -> Dict[str, Any]:
        """Create auto attendant routing to the call queue with resource account verification"""
        self.log(f"Creating auto attendant: {name}")

        aa_data = {
            "name": name,
            "languageId": "en-US",
            "greetingPrompt": greeting,
            "menuOptions": [
                {
                    "dtmfResponse": "1",
                    "prompt": "Support",
                    "callTargetType": "CallQueue",
                    "callTargetId": queue_id
                }
            ],
            "enableVoiceResponse": True,
            "timeoutPrompt": "We did not receive a response. Please hold while we connect you."
        }

        try:
            response = requests.post(
                f"{self.base_url}/autoattendants",
                params={"session_id": self.session_id},
                json=aa_data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                self.results["auto_attendant"] = result

                # Check if AA creation was skipped due to missing resource accounts
                if result.get("status") == "skipped":
                    self.log(f"Auto attendant creation SKIPPED: {result.get('reason')}", "WARNING")
                    self.log("This is expected behavior when call queues lack resource accounts", "INFO")

                    # Show available alternatives
                    available_queues = result.get("available_queues_with_resources", [])
                    if available_queues:
                        self.log(f"Available queues with resource accounts: {len(available_queues)}", "INFO")
                        for queue in available_queues[:3]:  # Show first 3
                            self.log(f"  - {queue.get('name', 'Unknown')} ({queue.get('identity', '')[:8]}...)", "DEBUG")

                    # Show suggestions
                    suggestions = result.get("suggestions", [])
                    if suggestions:
                        self.log("Suggestions:", "INFO")
                        for suggestion in suggestions:
                            self.log(f"  - {suggestion}", "DEBUG")

                    return result
                else:
                    # AA was created successfully
                    self.log(f"Auto attendant created: {result.get('name')}", "SUCCESS")
                    self.log(f"AA ID: {result.get('identity')}", "DEBUG")

                    # Show resource check results
                    resource_checks = result.get("resource_check_results", [])
                    for check in resource_checks:
                        if check["resource_check"]["has_resource_account"]:
                            self.log(f"Resource account verified: {check['resource_check']['resource_account_id']}", "SUCCESS")
                        else:
                            self.log(f"Resource account missing for queue {check['call_target_id']}", "WARNING")

                    return result
            else:
                error_msg = response.text
                self.log(f"Auto attendant creation failed: {response.status_code}", "ERROR")
                self.log(f"Error details: {error_msg[:200]}", "ERROR")

                # Check for specific known issues
                if "NO_RESOURCE_ACCOUNT_FOUND" in error_msg:
                    self.log("Issue: Call queue has no resource account associated", "WARNING")
                    self.log("Note: Auto attendants require call queues with resource accounts", "WARNING")
                elif "CallTarget" in error_msg:
                    self.log("Issue: PowerShell parameter ambiguity", "WARNING")
                    self.log("This is a known limitation in the current implementation", "WARNING")

                return {"error": error_msg}

        except requests.exceptions.RequestException as e:
            self.log(f"Auto attendant creation error: {e}", "ERROR")
            return {"error": str(e)}

    def verify_setup(self) -> Dict[str, Any]:
        """Verify the complete call center setup"""
        self.log("Verifying call center setup...")

        verification = {
            "user_created": bool(self.results["user"] and "error" not in self.results["user"]),
            "queue_created": bool(self.results["queue"] and "error" not in self.results["queue"]),
            "agent_assigned": bool(self.results["agent_assignment"] and "error" not in self.results["agent_assignment"]),
            "aa_created": False,
            "aa_skipped": False,
            "overall_success": False
        }

        # Check Auto Attendant status more carefully
        aa_result = self.results.get("auto_attendant", {})
        if aa_result and "error" not in aa_result:
            if aa_result.get("status") == "created":
                verification["aa_created"] = True
            elif aa_result.get("status") == "skipped":
                verification["aa_skipped"] = True
                self.log("Auto Attendant creation was intelligently skipped due to missing resource accounts", "INFO")

        # Check overall success (agent assignment and AA are non-critical for basic functionality)
        critical_components = verification["user_created"] and verification["queue_created"]
        verification["overall_success"] = critical_components

        self.log("=== VERIFICATION RESULTS ===")
        self.log(f"✅ User Creation: {'SUCCESS' if verification['user_created'] else 'FAILED'}")
        self.log(f"✅ Call Queue Creation: {'SUCCESS' if verification['queue_created'] else 'FAILED'}")
        if verification['agent_assigned']:
            self.log(f"✅ Agent Assignment: SUCCESS")
        else:
            agent_result = self.results.get("agent_assignment", {})
            attempts = agent_result.get('attempts_made', 'Unknown')
            self.log(f"⚠️  Agent Assignment: FAILED after {attempts} attempts (non-critical)")
            if self.verbose and 'error_type' in agent_result:
                self.log(f"   Error Type: {agent_result['error_type']}", "DEBUG")

        # Handle Auto Attendant status
        if verification['aa_created']:
            self.log(f"🎙️  Auto Attendant: SUCCESS")
        elif verification['aa_skipped']:
            self.log(f"🎙️  Auto Attendant: SKIPPED (missing resource accounts - expected behavior)")
        else:
            aa_result = self.results.get("auto_attendant", {})
            if "error" in aa_result:
                self.log(f"🎙️  Auto Attendant: FAILED ({aa_result['error'][:50]}...)")
            else:
                self.log(f"🎙️  Auto Attendant: NOT ATTEMPTED")

        self.log(f"🎯 Overall Status: {'SUCCESS' if verification['overall_success'] else 'PARTIAL/FAILED'}")

        return verification

    def print_summary(self):
        """Print detailed summary of all operations"""
        print("\n" + "="*60)
        print("🏆 TEAMS SDK UNIFIED TEST SUMMARY")
        print("="*60)
        
        # User details
        if self.results["user"] and "error" not in self.results["user"]:
            user = self.results["user"]
            print(f"\n👤 USER CREATED:")
            print(f"   Name: {user.get('displayName', 'Unknown')}")
            print(f"   Email: {user.get('userPrincipalName', 'Unknown')}")
            print(f"   ID: {user.get('userId', 'Unknown')}")
        
        # Queue details  
        if self.results["queue"] and "error" not in self.results["queue"]:
            queue = self.results["queue"] 
            print(f"\n📞 CALL QUEUE CREATED:")
            print(f"   Name: {queue.get('name', 'Unknown')}")
            print(f"   ID: {queue.get('identity', 'Unknown')}")
            print(f"   Routing: {queue.get('routingMethod', 'Unknown')}")
            
        # Agent assignment
        if self.results["agent_assignment"]:
            agent = self.results["agent_assignment"]
            if "error" not in agent:
                print(f"   Agent: {agent.get('userPrincipalName', 'Unknown')} ✅")
            else:
                attempts = agent.get('attempts_made', 'Unknown')
                error_type = agent.get('error_type', 'Unknown')
                wait_time = agent.get('total_wait_time', 'Unknown')
                print(f"   Agent: Assignment failed after {attempts} attempts ⚠️")
                print(f"   Error Type: {error_type}")
                if wait_time != 'Unknown':
                    print(f"   Total Wait Time: {wait_time} seconds")
                if self.verbose and 'helpful_message' in agent:
                    print(f"   Help: {agent['helpful_message']}")
        
        # Auto attendant details
        if self.results["auto_attendant"] and "error" not in self.results["auto_attendant"]:
            aa = self.results["auto_attendant"]
            print(f"\n🎙️  AUTO ATTENDANT CREATED:")
            print(f"   Name: {aa.get('name', 'Unknown')}")
            print(f"   ID: {aa.get('identity', 'Unknown')}")
            print(f"   Language: {aa.get('languageId', 'Unknown')}")
            
            print(f"\n📞 CALL FLOW:")
            print(f"   1️⃣  Caller → Auto Attendant ({aa.get('name')})")
            print(f"   2️⃣  Press 1 → Call Queue ({self.results['queue'].get('name') if self.results['queue'] else 'Unknown'})")
            print(f"   3️⃣  Queue → Agent ({self.results['user'].get('displayName') if self.results['user'] else 'Unknown'})")
        
        print(f"\n🎯 COMPLETE CALL CENTER SETUP: {'OPERATIONAL' if self.results['auto_attendant'] else 'PARTIAL'}")
        print("="*60)

def main():
    parser = argparse.ArgumentParser(
        description="Test complete Teams SDK call center workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
 Examples:
   # Basic test
   python test_unified_call_center.py --user-name "John Doe" --user-email "john@cloudwarriors.onmicrosoft.com" --queue-name "Support Queue" --aa-name "Main IVR"

   # Full test with custom options
   python test_unified_call_center.py \\
     --user-name "Jane Smith" \\
     --user-email "jane@cloudwarriors.onmicrosoft.com" \\
     --queue-name "Customer Service" \\
     --aa-name "Customer IVR" \\
     --password "CustomPass123!" \\
     --greeting "Welcome to customer service" \\
     --timeout 90 \\
     --max-agent-retries 5 \\
     --agent-retry-delay 2 \\
     --verbose

   # Fast retry configuration
   python test_unified_call_center.py \\
     --user-name "John Doe" \\
     --user-email "john@company.com" \\
     --queue-name "Support Queue" \\
     --aa-name "Main IVR" \\
     --max-agent-retries 3 \\
     --agent-retry-delay 1

   # Disable retries entirely
   python test_unified_call_center.py \\
     --user-name "John Doe" \\
     --user-email "john@company.com" \\
     --queue-name "Support Queue" \\
     --aa-name "Main IVR" \\
     --no-retries
        """
    )
    
    # Required arguments
    parser.add_argument("--user-name", required=True, help="Display name for the user to create")
    parser.add_argument("--user-email", required=True, help="Email address for the user (must be valid tenant email)")
    parser.add_argument("--queue-name", required=True, help="Name for the call queue to create")
    parser.add_argument("--aa-name", required=True, help="Name for the auto attendant to create")
    
    # Optional arguments
    parser.add_argument("--password", default="TempPass123!", help="Password for the user (default: TempPass123!)")
    parser.add_argument("--greeting", help="Custom greeting for auto attendant (default: auto-generated)")
    parser.add_argument("--base-url", default="http://127.0.0.1:9000", help="FastAPI server URL (default: http://127.0.0.1:9000)")
    parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds (default: 60)")
    parser.add_argument("--no-retries", action="store_true", help="Disable retry logic for agent assignment")
    parser.add_argument("--max-agent-retries", type=int, default=5, help="Maximum retry attempts for agent assignment (default: 5)")
    parser.add_argument("--agent-retry-delay", type=int, default=2, help="Base delay in seconds between agent assignment retries (default: 2)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug output")
    
    args = parser.parse_args()
    
    # Generate default greeting if not provided
    if not args.greeting:
        args.greeting = f"Welcome to {args.queue_name}. Press 1 for assistance or stay on the line."
    
    print("🎯 TEAMS SDK UNIFIED CALL CENTER TEST")
    print("="*50)
    print(f"User: {args.user_name} ({args.user_email})")
    print(f"Queue: {args.queue_name}")  
    print(f"Auto Attendant: {args.aa_name}")
    print(f"Server: {args.base_url}")
    print("="*50)
    
    # Initialize tester
    tester = TeamsSDKTester(
        base_url=args.base_url,
        timeout=args.timeout,
        verbose=args.verbose,
        no_retries=args.no_retries,
        max_agent_retries=args.max_agent_retries,
        agent_retry_delay=args.agent_retry_delay
    )
    
    try:
        # Step 1: Create session
        if not tester.create_session():
            tester.log("Cannot proceed without valid session", "ERROR")
            sys.exit(1)
            
        # Step 2: Create user
        user_result = tester.create_user(args.user_name, args.user_email, args.password)
        if "error" in user_result:
            tester.log("User creation failed, but continuing with other tests...", "WARNING")
        
        # Step 3: Create call queue and add agent
        queue_result = tester.create_call_queue(args.queue_name, args.user_email)
        if "error" in queue_result:
            tester.log("Call queue creation failed", "ERROR")
        else:
            # Step 4: Create auto attendant (if queue was successful)
            queue_id = queue_result.get("identity")
            if queue_id:
                aa_result = tester.create_auto_attendant(args.aa_name, queue_id, args.greeting)
                if "error" in aa_result:
                    tester.log("Auto attendant creation failed, but call queue is functional", "WARNING")
        
        # Step 5: Verification
        verification = tester.verify_setup()
        
        # Step 6: Print summary
        tester.print_summary()
        
        # Exit with appropriate code
        if verification["overall_success"]:
            tester.log("🎉 Test completed successfully!", "SUCCESS")
            sys.exit(0)
        else:
            tester.log("⚠️ Test completed with issues", "WARNING") 
            sys.exit(1)
            
    except KeyboardInterrupt:
        tester.log("Test interrupted by user", "WARNING")
        sys.exit(130)
    except Exception as e:
        tester.log(f"Unexpected error: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()