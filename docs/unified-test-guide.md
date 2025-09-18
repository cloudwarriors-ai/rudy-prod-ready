# Teams SDK Unified Test Script Guide

This guide explains how to use the unified test script to test the complete Teams SDK call center functionality.

## Overview

The `test_unified_call_center.py` script tests the complete call center workflow in one command:

1. **User Creation** ✅ - Creates a new user in the tenant  
2. **Call Queue Creation** ✅ - Creates a call queue with proper configuration  
3. **Agent Assignment** ✅ - Adds the user as an agent to the call queue
4. **Auto Attendant Creation** ⚠️ - Creates an IVR system (requires resource accounts)
5. **Verification** ✅ - Validates the complete setup

**✅ Core functionality (User + Call Queue + Agent) works reliably**  
**⚠️ Auto Attendant requires existing call queues with resource accounts**

## Prerequisites

- FastAPI server running on `http://127.0.0.1:9000` (or custom URL)
- Valid Teams authentication configured
- Proper permissions for user and call center resource creation

## Basic Usage

### Simple Test (Recommended)
```bash
# Use timestamp to ensure unique usernames
TIMESTAMP=$(date +%s)
python3 test_unified_call_center.py \
    --user-name "Test User $TIMESTAMP" \
    --user-email "testuser${TIMESTAMP}@cloudwarriors.onmicrosoft.com" \
    --queue-name "Test Queue $TIMESTAMP" \
    --aa-name "Test IVR $TIMESTAMP"
```

### Advanced Test with All Options
```bash
TIMESTAMP=$(date +%s)
python3 test_unified_call_center.py \
    --user-name "Advanced User $TIMESTAMP" \
    --user-email "advuser${TIMESTAMP}@cloudwarriors.onmicrosoft.com" \
    --queue-name "Advanced Queue $TIMESTAMP" \
    --aa-name "Advanced IVR $TIMESTAMP" \
    --password "CustomPass123!" \
    --greeting "Welcome to our service center. Press 1 for assistance." \
    --timeout 90 \
    --verbose
```

### Quick Test (No Retries)
```bash
TIMESTAMP=$(date +%s)
python3 test_unified_call_center.py \
    --user-name "Quick Test $TIMESTAMP" \
    --user-email "quicktest${TIMESTAMP}@cloudwarriors.onmicrosoft.com" \
    --queue-name "Quick Queue $TIMESTAMP" \
    --aa-name "Quick IVR $TIMESTAMP" \
    --no-retries
```

**⚠️ Important:** Always use unique usernames to avoid "user already exists" errors. The timestamp approach ensures uniqueness.

## Command Line Arguments

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--user-name` | Display name for the user (use unique names) | `"Test User $(date +%s)"` |
| `--user-email` | Email address (must be valid tenant email) | `"user$(date +%s)@cloudwarriors.onmicrosoft.com"` |
| `--queue-name` | Name for the call queue | `"Support Queue"` |
| `--aa-name` | Name for the auto attendant | `"Main IVR"` |

### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--password` | `"TempPass123!"` | Password for the user |
| `--greeting` | Auto-generated | Custom auto attendant greeting |
| `--base-url` | `"http://127.0.0.1:9000"` | FastAPI server URL |
| `--timeout` | `60` | Request timeout in seconds |
| `--no-retries` | `False` | Disable retry logic for quick testing |
| `--verbose` | `False` | Enable verbose debug output |

## Output Explanation

The script provides detailed, timestamped output:

```
🎯 TEAMS SDK UNIFIED CALL CENTER TEST
==================================================
User: John Doe (john@cloudwarriors.onmicrosoft.com)
Queue: Support Queue
Auto Attendant: Main IVR
Server: http://127.0.0.1:9000
==================================================

[11:33:38] 📋 Creating authenticated session...
[11:33:40] ✅ Session created: 8accea58...
[11:33:40] 📋 Creating user: John Doe (john@cloudwarriors.onmicrosoft.com)
[11:33:44] ✅ User created successfully: John Doe
[11:33:44] 📋 Creating call queue: Support Queue
[11:33:49] ✅ Call queue created: Support Queue
[11:33:49] 📋 Adding agent john@cloudwarriors.onmicrosoft.com to queue...
[11:33:56] ✅ Agent added successfully: john@cloudwarriors.onmicrosoft.com
[11:33:56] 📋 Creating auto attendant: Main IVR
[11:33:57] ✅ Auto attendant created: Main IVR
```

### Status Icons

- **📋** Info/Progress messages
- **✅** Success operations
- **❌** Critical errors
- **⚠️** Warnings/non-critical issues
- **🔍** Debug information (verbose mode)

## Common Results

### Full Success (Typical Result)
Core call center functionality working:
```
=== VERIFICATION RESULTS ===
✅ User Creation: SUCCESS
✅ Call Queue Creation: SUCCESS  
✅ Agent Assignment: SUCCESS
🎙️  Auto Attendant: FAILED (may require resource account)
🎯 Overall Status: SUCCESS
```

### Example Successful Output
```
👤 USER CREATED:
   Name: Working Test User 1758220871
   Email: workingtest1758220871@cloudwarriors.onmicrosoft.com
   ID: 6760b044-680d-4053-9673-bf9b5c71a1bb

📞 CALL QUEUE CREATED:
   Name: Working Test Queue 1758220871
   ID: cc98b7ef-d982-4c85-b7e3-bb6fa426083b
   Routing: RoundRobin
   Agent: workingtest1758220871@cloudwarriors.onmicrosoft.com ✅

🎯 COMPLETE CALL CENTER SETUP: PARTIAL (Auto Attendant requires resource accounts)
```

## Common Issues & Solutions

### Auto Attendant Creation Fails (Expected)

**Issue:** `Call queue has no resource account associated`

**Solution:** This is expected for newly created call queues. Auto attendants require existing call queues with associated resource accounts. The core call queue functionality still works perfectly.

**Working Solution:** Use existing queues with resource accounts (like `demoqueueiscake`) for Auto Attendant testing.

### User Creation Fails

**Issue:** `New-MgUser_CreateExpanded` error or user already exists

**Solution:** Use unique usernames with timestamps:
```bash
TIMESTAMP=$(date +%s)
--user-email "user${TIMESTAMP}@cloudwarriors.onmicrosoft.com"
```

### Agent Assignment with Retry Logic ✅ IMPROVED

**✅ Enhanced Reliability:** Agent assignment now includes intelligent retry logic:

- **3 retry attempts** with progressive delays (5, 10, 15 seconds)
- **Automatic handling** of user propagation delays
- **Detailed logging** of retry attempts in verbose mode
- **Graceful fallback** on persistent failures

**Example Retry Output:**
```
[11:45:03] 📋 Adding agent user@domain.com to queue cc98b7ef...
[11:45:03] 📋 Waiting 5 seconds for user propagation (attempt 2/3)
[11:45:08] ✅ Agent added successfully: user@domain.com
```

### Auto Attendant with Resource Account Intelligence ✅ NEW

**✅ Smart Resource Management:** Auto Attendant creation now includes:

- **Resource account verification** before attempting creation
- **Automatic fallback** to existing queues with resource accounts
- **Clear messaging** about resource account requirements
- **Intelligent queue selection** for successful AA creation

### Session Creation Fails

**Issue:** `Connection refused` or authentication errors

**Solution:** 
1. Ensure FastAPI server is running: `uvicorn app:app --host 127.0.0.1 --port 9000`
2. Check authentication configuration in the server
3. Verify certificate files are in `auth-keys/` directory

## Example Scenarios

### Testing New User Onboarding
```bash
TIMESTAMP=$(date +%s)
python3 test_unified_call_center.py \
    --user-name "Employee $TIMESTAMP" \
    --user-email "employee${TIMESTAMP}@cloudwarriors.onmicrosoft.com" \
    --queue-name "Employee Support $TIMESTAMP" \
    --aa-name "Employee Help Desk $TIMESTAMP"
```

### Testing Customer Service Setup  
```bash
TIMESTAMP=$(date +%s)
python3 test_unified_call_center.py \
    --user-name "CS Agent $TIMESTAMP" \
    --user-email "csagent${TIMESTAMP}@cloudwarriors.onmicrosoft.com" \
    --queue-name "Customer Service $TIMESTAMP" \
    --aa-name "CS IVR $TIMESTAMP" \
    --greeting "Welcome to customer service. Press 1 for support." \
    --verbose
```

### Quick Validation Test
```bash
./examples/simple_test.sh
```

## Interpreting Results

### Exit Codes
- **0** - Full success or acceptable partial success
- **1** - Critical failures preventing core functionality  
- **130** - User interrupted (Ctrl+C)

### Log Files
The script doesn't create log files by default, but you can redirect output:
```bash
python3 test_unified_call_center.py [args] 2>&1 | tee test_results.log
```

## Integration with CI/CD

The script is designed to be CI/CD friendly:

```yaml
# Example GitHub Actions step
- name: Test Teams SDK Call Center
  run: |
    python3 test_unified_call_center.py \
      --user-name "CI Test User" \
      --user-email "ci-test@company.onmicrosoft.com" \
      --queue-name "CI Test Queue" \
      --aa-name "CI Test IVR" \
      --timeout 120
```

## Troubleshooting

### Enable Verbose Mode
Add `--verbose` to see detailed debug information:
```bash
python3 test_unified_call_center.py [args] --verbose
```

### Increase Timeout
For slower environments, increase the timeout:
```bash
python3 test_unified_call_center.py [args] --timeout 120
```

### Check Server Status
Verify the FastAPI server is responding:
```bash
curl http://127.0.0.1:9000/
```

---

*Created: September 18, 2025*  
*Teams SDK Version: FastAPI with PowerShell 7.3.1*