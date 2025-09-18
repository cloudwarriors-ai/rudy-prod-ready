# Teams SDK Troubleshooting Guide

This document outlines common issues encountered with the Teams SDK FastAPI application and their solutions.

## Resource Account Issues

### Issue: Auto Attendant Creation Fails Due to Missing Resource Accounts ✅ RESOLVED

**Symptoms:**
- Auto Attendant creation returns error or fails unexpectedly
- Error messages mentioning "CallTarget" parameter issues
- Auto Attendants created successfully but don't route calls properly
- Call queues exist but Auto Attendants can't connect to them

**Root Cause Analysis:**
Auto Attendants require call queues to have associated resource accounts before they can route calls to them. When call queues are created without resource accounts, Auto Attendant creation either fails or creates incomplete configurations.

**Solution Applied:**
Implemented comprehensive resource account verification system that:

1. **Pre-verification**: Checks all call queue targets before attempting Auto Attendant creation
2. **Intelligent Skipping**: Skips AA creation when resource accounts are missing (instead of failing)
3. **Clear Messaging**: Provides detailed reasons and suggestions when AA creation is skipped
4. **Alternative Queues**: Lists available call queues with resource accounts for use as alternatives

**New API Features:**

#### Resource Account Verification Endpoints
```bash
# Check specific queue resource account
GET /callqueues/{queue_identity}/resource-account?session_id={session_id}

# List all queues with resource accounts
GET /callqueues/resource-accounts?session_id={session_id}
```

#### Enhanced Auto Attendant Creation
- **Success Response**: Includes resource verification results
- **Skipped Response**: Provides helpful guidance and alternatives
- **Available Queues**: Lists existing queues with resource accounts

**Example Skipped Response:**
```json
{
  "message": "Auto Attendant creation skipped due to missing resource accounts",
  "status": "skipped",
  "reason": "One or more call queues in the menu options do not have associated resource accounts",
  "available_queues_with_resources": [
    {
      "identity": "existing-queue-guid",
      "name": "Existing Queue with Resource",
      "resource_account_id": "resource-guid"
    }
  ],
  "suggestions": [
    "Create resource accounts for your call queues before creating Auto Attendants",
    "Use existing call queues that already have resource accounts"
  ]
}
```

**Prevention:**
1. Always check resource accounts before creating Auto Attendants
2. Use the new verification endpoints to identify suitable call queues
3. Create resource accounts using: `New-CsOnlineApplicationInstance`
4. Associate resource accounts with call queues using: `New-CsOnlineApplicationInstanceAssociation`

## Call Queue Issues

### Issue: Call Queues Not Being Listed After Creation ✅ RESOLVED

**Symptoms:**
- Call queue creation returns successful response
- `GET /callqueues` returns empty list or count of 0
- API responds with `{"message":"Found 0 call queues","queues":[],"count":0}`

**Root Cause Analysis:**
Initially suspected to be PowerShell parameter issues, but the actual root cause was a **Python parsing logic bug** in the API response handler.

**Two Separate Issues Identified:**

#### 1. PowerShell Parameter Issue (Fixed)
Call queue creation was failing due to invalid default parameter values in Pydantic models.

#### 2. API Parsing Logic Bug (Fixed)
**PRIMARY ISSUE:** The response parser was incorrectly skipping all call queue data due to faulty boolean logic.

**Error Details:**
```
Call queue creation failed: Cannot process argument transformation on parameter 'TimeoutAction'. 
Cannot convert value "DisconnectWithBusy" to type "Microsoft.Rtc.Management.Hosted.HuntGroup.Models.TimeoutAction". 
Error: "Unable to match the identifier name DisconnectWithBusy to a valid enumerator name. 
Specify one of the following enumerator names and try again:
Disconnect, Forward, Voicemail, SharedVoicemail"
```

**Solutions Applied:**

#### Fix 1: PowerShell Parameter Values
Update the default parameter values in `app.py` for the `CreateCallQueueRequest` model:

```python
# FIXED: Updated default values to valid PowerShell enums
overflowAction: str = Field(default="Disconnect", examples=["Disconnect", "Forward", "Voicemail", "SharedVoicemail"])
timeoutAction: str = Field(default="Disconnect", examples=["Disconnect", "Forward", "Voicemail", "SharedVoicemail"])
```

#### Fix 2: API Parsing Logic Bug ⭐ **PRIMARY FIX**
**Location:** `app.py` lines 1188 and 1191 in the `list_call_queues` function

**The Problem:**
```python
# BUGGY CODE (before fix):
elif line == "QUEUE_END" and current_queue:           # ❌ Empty dict {} evaluates to False
elif current_queue and ': ' in line:                 # ❌ Skips all data parsing
```

**The Fix:**
```python
# FIXED CODE:
elif line == "QUEUE_END" and current_queue is not None:    # ✅ Explicitly check for None
elif current_queue is not None and ': ' in line:           # ✅ Correctly parses all data
```

**Why This Happened:**
- `current_queue = {}` (empty dictionary) evaluates to `False` in Python boolean context
- The parser was correctly reading PowerShell output but skipping all queue data
- `Get-CsCallQueue` was working fine - the API just wasn't parsing its response

**Valid PowerShell Enum Values:**
- **OverflowAction/TimeoutAction:** `Disconnect`, `Forward`, `Voicemail`, `SharedVoicemail`
- **RoutingMethod:** `Attendant`, `Serial`, `RoundRobin`, `LongestIdle`

**Debugging Process Used:**
1. **Initial Hypothesis:** PowerShell command failure (incorrect)
2. **Agent Investigation:** Created debug scripts in `/root/code/teams-sdk/debug/powershell/`
3. **Direct PowerShell Testing:** `Get-CsCallQueue` returned 13 queues successfully
4. **API Comparison:** API returned 0 queues - identified parsing bug
5. **Root Cause:** Boolean logic error in Python response parser
6. **Fix Applied:** Changed boolean checks to explicit `is not None` comparisons

**Development Infrastructure Added:**
- **Debug Scripts:** `/root/code/teams-sdk/debug/powershell/test-callqueue-listing.ps1`
- **Development Mode:** FastAPI with `--reload --log-level debug`
- **Debug Logging:** Comprehensive PowerShell execution logs
- **Validation Tools:** API vs direct PowerShell comparison scripts

**Verification Results:**
- ✅ Direct PowerShell: 13 call queues found
- ✅ API after fix: 13 call queues found  
- ✅ Perfect match between direct and API results

## Authentication Issues

### Issue: Teams PowerShell Commands Fail

**Symptoms:**
- Graph API operations work fine
- Teams-specific commands (Get-CsCallQueue, New-CsCallQueue) fail
- Error: "Session not authenticated for Teams operations"

**Root Cause:**
Session is authenticated to Microsoft Graph (`Connect-MgGraph`) but not to Microsoft Teams PowerShell (`Connect-MicrosoftTeams`).

**Solution:**
The application automatically attempts Teams authentication when needed. Verify:

1. Certificate file exists at: `/root/code/teams-sdk/auth-keys/teamsfed.pfx`
2. Certificate password is correct: `P@ssw0rd!`
3. Application ID has proper Teams PowerShell permissions
4. Tenant ID is correct: `e7b105b2-720e-4b5b-9310-1a414c06356a`

**Debug Steps:**
```python
# Test authentication status
response = requests.get('http://127.0.0.1:9000/auth/status', params={'session_id': session_id})
print(response.json())
```

### Issue: Certificate Path Errors

**Symptoms:**
- Error: `error:10000080:BIO routines::no such file`
- PowerShell fails to load certificate

**Root Cause:**
Old certificate paths still referenced in code after repository reorganization.

**Solution:**
Ensure all certificate paths use the new location:
```
OLD: /root/code/teams-sdk/teamsfed.pfx
NEW: /root/code/teams-sdk/auth-keys/teamsfed.pfx
```

Search and replace all occurrences in `app.py`:
```bash
grep -n "/root/code/teams-sdk/teamsfed.pfx" app.py
# Replace all instances with new path
```

## Auto Attendant Issues

### Issue: Auto Attendant Creation Fails

**Symptoms:**
- Error: `Parameter cannot be processed because the parameter name 'CallTarget' is ambiguous`
- Auto attendant creation returns 400 or 500 error

**Root Cause:**
PowerShell parameter `-CallTarget` is ambiguous in newer Teams PowerShell modules.

**Current Workaround:**
The issue is in line 1424 of `app.py`:
```powershell
$menuOption{i} = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone{option.dtmfResponse} -CallTarget $menuTarget{i} -Prompt $menuPrompt{i}
```

**Potential Fix:**
Replace `-CallTarget` with more specific parameters:
```powershell
$menuOption{i} = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone{option.dtmfResponse} -CallTargetId $menuTarget{i}.Id -CallTargetType $menuTarget{i}.Type -Prompt $menuPrompt{i}
```

## General Debugging

### Enable Debug Logging

Add debug output to see actual PowerShell commands and responses:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test PowerShell Commands Manually

Connect to PowerShell manually to test commands:
```powershell
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26" 
$PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert

# Test commands
Get-CsTenant
Get-CsCallQueue
```

### Verify Teams Module Version

Check PowerShell module version:
```powershell
Get-Module MicrosoftTeams -ListAvailable
```

Expected version: 7.3.1 or later

## Repository Structure Issues

### After Reorganization Checklist

When reorganizing the repository structure, verify:

1. ✅ All certificate paths updated to `auth-keys/` folder
2. ✅ Documentation moved to `docs/` folder  
3. ✅ Logs directory created and accessible
4. ✅ Python scripts reference correct relative paths
5. ✅ FastAPI server starts without import errors
6. ✅ Authentication works with new certificate path
7. ✅ API endpoints respond correctly

### Common File Locations

```
/root/code/teams-sdk/
├── app.py                          # Main FastAPI application
├── auth-keys/
│   └── teamsfed.pfx               # Certificate file
├── docs/
│   ├── teamsapi.md                # API documentation  
│   └── troubleshooting.md         # This file
├── logs/                          # Application logs
├── python-testing/                # Test scripts
└── venv/                          # Python virtual environment
```

## Resolution Timeline

1. **Identify Issue:** Call queues created but not listed
2. **Debug Authentication:** Verified Teams PowerShell connectivity working
3. **Find Root Cause:** Invalid default parameter values in Pydantic models
4. **Apply Fix:** Update `overflowAction` and `timeoutAction` defaults
5. **Test Resolution:** Restart server and verify call queue creation/listing

## Prevention

- Always test enum parameter values against PowerShell documentation
- Use debug endpoints to see actual PowerShell command output
- Validate API responses match expected format
- Test both creation AND listing operations after changes

## User Management and Call Queue Agents

### Issue: Adding Users to Call Queues ✅ RESOLVED

**Problem:**
Need to add users as agents to call queues, but PowerShell commands require user GUID rather than email address.

**Solution:**
The FastAPI application has a built-in endpoint that automatically handles email-to-GUID conversion.

**API Endpoint:**
```http
POST /callqueues/{queue_identity}/agents?session_id={session_id}
Content-Type: application/json

{
  "userPrincipalName": "user@domain.com"
}
```

**Process Flow:**
1. **User GUID Lookup:** Uses `Get-MgUser -Filter "userPrincipalName eq '{email}'"` to get user GUID
2. **Queue Retrieval:** Gets current queue configuration with `Get-CsCallQueue -Identity "{queue_identity}"`
3. **Agent Addition:** Adds user GUID to the queue's Users array with `Set-CsCallQueue -Identity "{queue_identity}" -Users $newUsers`

**Example Usage:**
```bash
# Create session
SESSION_ID=$(curl -X POST "http://127.0.0.1:9000/auth/connect" | jq -r '.session_id')

# Add user to call queue
curl -X POST "http://127.0.0.1:9000/callqueues/ca6cf9b4-55d6-4123-8321-9114a09985dd/agents?session_id=$SESSION_ID" \
-H "Content-Type: application/json" \
-d '{"userPrincipalName": "testagent@cloudwarriors.onmicrosoft.com"}'
```

**Success Response:**
```json
{
  "message": "User added to call queue successfully",
  "userPrincipalName": "testagent@cloudwarriors.onmicrosoft.com", 
  "callQueueIdentity": "ca6cf9b4-55d6-4123-8321-9114a09985dd",
  "status": "added"
}
```

**Verification Method:**
Create a PowerShell verification script to confirm agent addition:

```powershell
# Get user GUID
$user = Get-MgUser -Filter "userPrincipalName eq 'user@domain.com'"
$userGuid = $user.Id

# Check if user is in call queue
$queue = Get-CsCallQueue -Identity "{queue-id}"
$isAgent = $queue.Users -contains $userGuid

Write-Host "User is agent: $isAgent"
```

**Test Case Completed:**
- ✅ **User:** testagent@cloudwarriors.onmicrosoft.com (GUID: 3a220043-c755-4be7-a6a5-846771b7af52)
- ✅ **Queue:** Alpha Test Queue (ID: ca6cf9b4-55d6-4123-8321-9114a09985dd)
- ✅ **Status:** Agent successfully added and verified
- ✅ **Ready for:** End-to-end call flow testing

---

*Last Updated: September 18, 2025*
*Teams SDK Version: FastAPI with Teams PowerShell 7.3.1*

## Unified Test Script Issues

### Issue: User Creation Fails with 'User Already Exists'

**Symptoms:**
- `New-MgUser_CreateExpanded` error
- Test script fails at user creation step
- Error message unclear about duplicate user

**Root Cause:**
Attempting to create a user with an email address that already exists in the tenant.

**Solution:**
Use unique usernames with timestamps:

```bash
TIMESTAMP=$(date +%s)
python3 test_unified_call_center.py \
    --user-name "Test User $TIMESTAMP" \
    --user-email "testuser${TIMESTAMP}@cloudwarriors.onmicrosoft.com" \
    --queue-name "Test Queue $TIMESTAMP" \
    --aa-name "Test IVR $TIMESTAMP"
```

**Verification:**
When working correctly, you should see:
- ✅ User created with proper ID (not "Unknown")
- ✅ Call queue created successfully
- ✅ Agent assignment succeeds
- ⚠️ Auto Attendant fails (expected - needs resource accounts)

### Issue: Script Shows Success But Features Don't Work

**Problem:**
Script may report success but created resources aren't functional or visible.

**Diagnosis Steps:**
1. Check user ID is returned (not "Unknown")
2. Verify agent assignment succeeds 
3. Use verbose mode (`--verbose`) for detailed output
4. Test with unique usernames to avoid conflicts

**Working Output Example:**
```
✅ User Creation: SUCCESS
✅ Call Queue Creation: SUCCESS  
✅ Agent Assignment: SUCCESS
🎙️ Auto Attendant: FAILED (may require resource account)
🎯 Overall Status: SUCCESS
```

---

*Last Updated: September 18, 2025*
*Teams SDK Version: FastAPI with Teams PowerShell 7.3.1*
