# Auto Attendant PowerShell Scripts

Collection of PowerShell scripts for testing and debugging Auto Attendant functionality.

## 📂 Available Scripts

### **Auto Attendant Creation Scripts**
Located in `../../debug/powershell/`:

#### Core Testing Scripts
- `test-autoattendant-creation.ps1` - Basic auto attendant creation testing
- `test-minimal-aa.ps1` - Minimal configuration testing
- `test-simple-autoattendant.ps1` - Simple auto attendant examples
- `test-final-working.ps1` - Final working configuration

#### Business Hours Scripts  
- `test-business-hours-schedules.ps1` - Business hours and schedule testing
- `debug-rudy-etl-business-hours.ps1` - Rudy ETL business hours debugging
- `fix-rudy-etl-business-hours.ps1` - Business hours fixes and updates

#### Syntax and Validation Scripts
- `test-autoattendant-syntax.ps1` - PowerShell syntax validation
- `test-correct-syntax.ps1` - Corrected syntax examples
- `test-fixed-syntax.ps1` - Fixed parameter issues
- `test-final-autoattendant-fix.ps1` - Final syntax corrections

#### Menu and Prompt Scripts
- `test-menu-prompts.ps1` - Menu creation and prompt testing
- `test-autoattendant-working-queue.ps1` - Queue integration testing

#### Resource Account Scripts
- `test-resource-account-lookup.ps1` - Resource account discovery
- `test-resource-account-verification.ps1` - Resource account validation

## 🔧 **Standard Authentication Template**

All scripts use this authentication pattern:

```powershell
# Standard auth setup for debug scripts
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/Users/work/teams-sdk/auth-keys/teamsfed.pfx"
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

## 📝 **Script Usage Patterns**

### **Debug Output Pattern**
```powershell
# Enhanced debug output for troubleshooting
Write-Host "=== DEBUG INFORMATION ==="
Write-Host "Command: Get-CsAutoAttendant"
Write-Host "Timestamp: $(Get-Date)"
Write-Host "Session: $(Get-PSSession | Select-Object -First 1)"

$result = Get-CsAutoAttendant
Write-Host "Result Type: $($result.GetType())"
Write-Host "Result Count: $($result.Count)"
Write-Host "========================="

# Log to file
$debugInfo = @{
    Timestamp = Get-Date
    Command = "Get-CsAutoAttendant"
    ResultType = $result.GetType().FullName
    ResultCount = $result.Count
    Results = $result
}
$debugInfo | ConvertTo-Json -Depth 3 | Out-File "/Users/work/teams-sdk/debug/logs/debug-powershell.log" -Append
```

### **Error Handling Pattern**
```powershell
try {
    $autoAttendant = New-CsAutoAttendant -Name $name -DefaultCallFlow $callFlow -LanguageId "en-US" -TimeZoneId "UTC" -EnableVoiceResponse
    Write-Host "✅ Auto Attendant created successfully"
    Write-Host "ID: $($autoAttendant.Identity)"
    Write-Host "Name: $($autoAttendant.Name)"
} catch {
    Write-Host "❌ Auto Attendant creation failed: $_"
    Write-Host "Error Details: $($_.Exception.Message)"
    Write-Host "Stack Trace: $($_.ScriptStackTrace)"
}
```

### **Call Queue Resolution Pattern**
```powershell
# Get available call queues for routing
$callQueues = Get-CsCallQueue
Write-Host "Available Call Queues:"
foreach ($queue in $callQueues) {
    Write-Host "  - $($queue.Name) (ID: $($queue.Identity))"
}

# Create callable entity for first queue
if ($callQueues.Count -gt 0) {
    $queueEntity = New-CsAutoAttendantCallableEntity -Identity $callQueues[0].Identity -Type CallQueue
    Write-Host "✅ Queue entity created for: $($callQueues[0].Name)"
} else {
    Write-Host "❌ No call queues available for routing"
    exit 1
}
```

## 🧪 **Testing Workflow**

### 1. **Basic Testing**
```bash
# Run basic auto attendant creation
./test-minimal-aa.ps1

# Check results in Teams Admin Center
```

### 2. **Business Hours Testing**
```bash
# Test business hours configuration
./test-business-hours-schedules.ps1

# Validate schedule associations
./debug-rudy-etl-business-hours.ps1
```

### 3. **Syntax Validation**
```bash
# Test PowerShell syntax
./test-autoattendant-syntax.ps1

# Verify parameter compatibility
./test-correct-syntax.ps1
```

### 4. **Resource Account Testing**
```bash
# Verify resource accounts
./test-resource-account-verification.ps1

# Look up existing accounts
./test-resource-account-lookup.ps1
```

## 📊 **Script Results Interpretation**

### **Success Indicators**
- ✅ "Teams connection successful"
- ✅ "Auto Attendant created successfully"
- ✅ "Schedule created successfully"
- ✅ Valid Identity/GUID returned

### **Failure Indicators**
- ❌ "Teams connection failed"
- ❌ "Auto Attendant creation failed"
- ❌ "Parameter validation failed"
- ❌ Empty results or null responses

### **Common Issues**
1. **Authentication Failures** - Check certificate path and credentials
2. **Parameter Validation** - Verify PowerShell module version compatibility
3. **Resource Dependencies** - Ensure call queues exist before referencing
4. **Syntax Errors** - Check parameter names and data types

## 🔗 **Related Resources**

- **API Documentation**: `../auto-attendant-build-process.md`
- **Field Definitions**: `../auto-attendant-fields.md`
- **Business Hours Guide**: `../BUSINESS_HOURS_SOLUTION.md`
- **Troubleshooting**: `../../troubleshooting.md`

---

**Script Location**: `/Users/work/teams-sdk/debug/powershell/`  
**Log Output**: `/Users/work/teams-sdk/debug/logs/`  
**Last Updated**: September 26, 2025