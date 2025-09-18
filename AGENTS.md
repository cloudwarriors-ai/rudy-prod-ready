# Teams SDK Agent Guidelines

This document outlines how to use AI agents effectively when working with the Teams SDK FastAPI application.

## When to Use Agents

### ✅ **USE AGENTS FOR:**
- **Complex debugging tasks** requiring multiple rounds of investigation
- **Multi-step searches** across codebase and documentation
- **PowerShell script creation and testing** in the `debug/` folder
- **API feature development** that requires research and implementation
- **Documentation generation** from code analysis
- **Troubleshooting investigations** that may require multiple approaches

### ❌ **DON'T USE AGENTS FOR:**
- **Single file reads** - Use Read tool directly
- **Simple edits** - Use Edit tool directly  
- **Known file locations** - Use direct tools instead of search
- **Basic API testing** - Use direct HTTP requests

## Development Infrastructure

### FastAPI Development Mode

**IMPORTANT:** Always run FastAPI in development mode for automatic reload:

```bash
cd /root/code/teams-sdk
source venv/bin/activate
uvicorn app:app --host 127.0.0.1 --port 9000 --reload --log-level debug
```

**Benefits of `--reload` flag:**
- ✅ Auto-reloads server on code changes
- ✅ No need to manually restart after edits
- ✅ Faster development cycle
- ✅ Real-time debugging

**Benefits of `--log-level debug`:**
- ✅ Detailed PowerShell command output
- ✅ Session management logging
- ✅ API request/response tracing

### Debug Directory Structure

Create PowerShell debug scripts in organized structure:

```
/root/code/teams-sdk/debug/
├── powershell/
│   ├── test-callqueue-listing.ps1     # Direct PowerShell testing
│   ├── test-auth.ps1                  # Authentication testing
│   ├── test-autoattendant.ps1         # Auto Attendant debugging
│   └── manual-teams-commands.ps1      # Manual Teams cmdlet testing
├── api/
│   ├── test-endpoints.py              # API endpoint testing
│   ├── debug-sessions.py              # Session debugging
│   └── trace-requests.py              # Request tracing
└── logs/
    ├── debug-powershell.log           # PowerShell debug output
    ├── debug-api.log                  # API debug output
    └── agent-tasks.log                # Agent task results
```

## Agent Task Templates

### PowerShell Debugging Agent Task

```markdown
**Agent Task:** Debug PowerShell Call Queue Listing

**Objective:** Create PowerShell scripts to test call queue operations directly, bypassing the API

**Steps:**
1. Create `/root/code/teams-sdk/debug/powershell/test-callqueue-listing.ps1`
2. Include authentication setup identical to API
3. Test `Get-CsCallQueue` directly with debug output
4. Compare results with `New-CsCallQueue` operations
5. Document findings in debug log file
6. Provide specific recommendations for API fixes

**Expected Output:** 
- Working PowerShell script
- Debug log with findings  
- Specific API code changes needed
```

### API Feature Development Agent Task

```markdown
**Agent Task:** Implement [Feature Name]

**Objective:** Add new API endpoint with proper error handling and documentation

**Requirements:**
1. Research existing similar endpoints in codebase
2. Follow established patterns for authentication and sessions
3. Create PowerShell command with proper error handling
4. Add Pydantic models for request/response
5. Update API documentation in `docs/teamsapi.md`
6. Add troubleshooting section to `docs/troubleshooting.md`
7. Create debug scripts for testing

**Expected Output:**
- Complete API endpoint implementation
- Updated documentation
- Debug/test scripts
- Troubleshooting guide entry
```

## File Locations and Patterns

### PowerShell Script Templates

**Authentication Pattern:**
```powershell
# Standard auth setup for debug scripts
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

try {
    Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    Write-Host "✅ Teams connection successful"
} catch {
    Write-Host "❌ Teams connection failed: $_"
    exit 1
}
```

**Debug Output Pattern:**
```powershell
# Enhanced debug output for troubleshooting
Write-Host "=== DEBUG INFORMATION ==="
Write-Host "Command: Get-CsCallQueue"
Write-Host "Timestamp: $(Get-Date)"
Write-Host "Session: $(Get-PSSession | Select-Object -First 1)"

$result = Get-CsCallQueue
Write-Host "Result Type: $($result.GetType())"
Write-Host "Result Count: $($result.Count)"
Write-Host "========================="

# Log to file
$debugInfo = @{
    Timestamp = Get-Date
    Command = "Get-CsCallQueue"
    ResultType = $result.GetType().FullName
    ResultCount = $result.Count
    Results = $result
}
$debugInfo | ConvertTo-Json -Depth 3 | Out-File "/root/code/teams-sdk/debug/logs/debug-powershell.log" -Append
```

### API Code Patterns

**Error Handling Pattern:**
```python
try:
    output, error = session.run_command(cmd, timeout=60)
    logger.debug(f"Command output: {output}")
    logger.debug(f"Command error: {error}")
    
    if error:
        raise HTTPException(status_code=400, detail=f"PowerShell error: {error}")
        
    # Parse results with detailed logging
    if "SUCCESS_MARKER" in output:
        # Success path
        pass
    else:
        # Error path with debug info
        raise HTTPException(status_code=400, detail=f"Command failed. Debug output: {output[:500]}")
        
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
```

### Documentation Update Pattern

**Always Update These Files:**
1. **`docs/teamsapi.md`** - API endpoint documentation
2. **`docs/troubleshooting.md`** - Common issues and solutions  
3. **`AGENTS.md`** - This file with new patterns/discoveries
4. **`README.md`** - High-level project changes

## Debugging Workflow with Agents

### 1. Issue Investigation
```markdown
Agent Task: Investigate [Issue Description]
- Create debug scripts to isolate the problem
- Test components independently  
- Document findings in debug logs
- Provide specific reproduction steps
```

### 2. Root Cause Analysis
```markdown
Agent Task: Analyze Root Cause of [Issue]
- Review debug script outputs
- Compare working vs non-working scenarios
- Identify the exact point of failure
- Research Teams PowerShell documentation for correct usage
```

### 3. Solution Implementation  
```markdown
Agent Task: Implement Fix for [Issue]
- Apply code changes based on root cause analysis
- Update error handling and validation
- Add preventive measures
- Update documentation
```

### 4. Validation and Documentation
```markdown
Agent Task: Validate Fix and Update Documentation
- Test fix with various scenarios
- Update troubleshooting guide
- Create prevention guidelines
- Document the resolution process
```

## Current Known Issues

### Call Queue Listing Issue
- **Status:** Under investigation
- **Symptoms:** `Get-CsCallQueue` returns empty results despite successful creation
- **Debug Scripts:** Need to create `debug/powershell/test-callqueue-listing.ps1`
- **Agent Task:** Required for PowerShell investigation

### Auto Attendant Parameter Issue  
- **Status:** Identified but needs fix
- **Issue:** `-CallTarget` parameter ambiguity in PowerShell
- **Location:** `app.py:1424`
- **Agent Task:** Research proper parameter usage

### FastAPI Development Mode
- **Status:** Needs implementation
- **Current:** Manual server restarts required
- **Needed:** `--reload` flag usage
- **Agent Task:** Update deployment documentation

## Agent Usage Examples

### Debugging Agent Usage
```python
# Use agent for complex debugging
task(
    description="Debug call queue listing",
    prompt="Create PowerShell debug scripts to test call queue listing directly. Set up proper debug logging and compare with API behavior. Document all findings.",
    subagent_type="general"
)
```

### Development Agent Usage  
```python
# Use agent for feature development
task(
    description="Add new API feature",
    prompt="Research and implement [feature] following existing patterns. Update documentation and create debug scripts for testing.",
    subagent_type="general"
)
```

---

*Last Updated: September 18, 2025*
*Teams SDK Version: FastAPI with Teams PowerShell 7.3.1*