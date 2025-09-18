# Test Auto Attendant Creation - Debug Script
# Purpose: Figure out the correct PowerShell parameters for New-CsAutoAttendantMenuOption
# Created: September 18, 2025

Write-Host "=== AUTO ATTENDANT CREATION DEBUG SCRIPT ===" -ForegroundColor Green
Write-Host "Testing PowerShell parameters for Auto Attendant creation" -ForegroundColor Yellow

# Authentication setup
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

try {
    Write-Host "`n1. Connecting to Microsoft Teams..." -ForegroundColor Cyan
    Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    Write-Host "✅ Teams connection successful" -ForegroundColor Green
} catch {
    Write-Host "❌ Teams connection failed: $_" -ForegroundColor Red
    exit 1
}

# Test data - use our existing Alpha Test Queue
$TestQueueId = "ca6cf9b4-55d6-4123-8321-9114a09985dd"
$TestQueueName = "Alpha Test Queue"

Write-Host "`n2. Testing callable entity creation..." -ForegroundColor Cyan

try {
    # Test 1: Create callable entity (this should work)
    Write-Host "   Testing New-CsAutoAttendantCallableEntity..." -ForegroundColor White
    $callableEntity = New-CsAutoAttendantCallableEntity -Identity $TestQueueId -Type HuntGroup
    
    Write-Host "   ✅ Callable entity created successfully" -ForegroundColor Green
    Write-Host "   Type: $($callableEntity.GetType().Name)" -ForegroundColor Gray
    Write-Host "   Properties available:" -ForegroundColor Gray
    $callableEntity | Get-Member -MemberType Property | ForEach-Object {
        $propName = $_.Name
        $propValue = $callableEntity.$propName
        Write-Host "     - $propName = $propValue" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "   ❌ Callable entity creation failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n3. Testing menu prompt creation..." -ForegroundColor Cyan

try {
    # Test 2: Create prompt (this should work)
    $menuPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Press 1 for technical support"
    Write-Host "   ✅ Menu prompt created successfully" -ForegroundColor Green
    
} catch {
    Write-Host "   ❌ Menu prompt creation failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n4. Testing menu option creation with different parameter approaches..." -ForegroundColor Cyan

# Test 3A: Try the BROKEN approach (what's currently in the API)
Write-Host "`n   Test 3A: Using -CallTarget (current broken method)" -ForegroundColor White
try {
    $menuOption1 = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone1 -CallTarget $callableEntity -Prompt $menuPrompt
    Write-Host "   ✅ UNEXPECTED: -CallTarget worked!" -ForegroundColor Green
} catch {
    Write-Host "   ❌ EXPECTED: -CallTarget failed: $_" -ForegroundColor Yellow
    Write-Host "   This confirms the parameter ambiguity issue" -ForegroundColor Yellow
}

# Test 3B: Try explicit parameters
Write-Host "`n   Test 3B: Using explicit -CallTargetId and -CallTargetType" -ForegroundColor White
try {
    # Get the properties we need from the callable entity
    $targetId = $callableEntity.Id
    $targetType = $callableEntity.Type
    
    Write-Host "     Callable Entity ID: $targetId" -ForegroundColor Gray
    Write-Host "     Callable Entity Type: $targetType" -ForegroundColor Gray
    
    $menuOption2 = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone1 -CallTargetId $targetId -CallTargetType $targetType -Prompt $menuPrompt
    Write-Host "   ✅ SUCCESS: Explicit parameters worked!" -ForegroundColor Green
    
} catch {
    Write-Host "   ❌ Explicit parameters failed: $_" -ForegroundColor Red
}

# Test 3C: Try without separate parameters
Write-Host "`n   Test 3C: Using the entity object directly with correct parameter name" -ForegroundColor White
try {
    # Check what the correct parameter name should be
    $help = Get-Help New-CsAutoAttendantMenuOption -Parameter * | Where-Object { $_.Name -like "*Target*" }
    Write-Host "     Available Target-related parameters:" -ForegroundColor Gray
    $help | ForEach-Object { Write-Host "       - $($_.Name)" -ForegroundColor Gray }
    
    # Try different variations
    $menuOption3 = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone1 -CallTargets $callableEntity -Prompt $menuPrompt
    Write-Host "   ✅ SUCCESS: -CallTargets (plural) worked!" -ForegroundColor Green
    
} catch {
    Write-Host "   ❌ -CallTargets failed: $_" -ForegroundColor Red
}

Write-Host "`n5. If we found a working method, test full Auto Attendant creation..." -ForegroundColor Cyan

if ($menuOption2 -or $menuOption3) {
    $workingMenuOption = if ($menuOption2) { $menuOption2 } else { $menuOption3 }
    $workingMethod = if ($menuOption2) { "Explicit Parameters" } else { "CallTargets Plural" }
    
    Write-Host "   Using working method: $workingMethod" -ForegroundColor Green
    
    try {
        # Create greeting prompt
        $greetingPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Welcome to Alpha Test Support Debug"
        
        # Create menu
        $menu = New-CsAutoAttendantMenu -Name "DebugMenu" -MenuOptions @($workingMenuOption) -EnableDialByName $false
        
        # Create call flow
        $defaultCallFlow = New-CsAutoAttendantCallFlow -Name "DebugFlow" -Menu $menu -Greetings @($greetingPrompt)
        
        # Create Auto Attendant
        $autoAttendant = New-CsAutoAttendant -Name "Debug AA Test" -LanguageId "en-US" -DefaultCallFlow $defaultCallFlow -EnableVoiceResponse $true
        
        Write-Host "   ✅ SUCCESS: Full Auto Attendant created!" -ForegroundColor Green
        Write-Host "   AA Identity: $($autoAttendant.Identity)" -ForegroundColor Green
        Write-Host "   AA Name: $($autoAttendant.Name)" -ForegroundColor Green
        
        # Log the successful parameters for the API fix
        $successLog = @"
=== SUCCESSFUL AUTO ATTENDANT CREATION ===
Date: $(Get-Date)
Method: $workingMethod
Queue ID: $TestQueueId
Queue Name: $TestQueueName
Auto Attendant ID: $($autoAttendant.Identity)
Auto Attendant Name: $($autoAttendant.Name)

Working PowerShell Code:
$(if ($menuOption2) {
"menuOption = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone1 -CallTargetId `$targetId -CallTargetType `$targetType -Prompt `$menuPrompt"
} else {
"menuOption = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone1 -CallTargets `$callableEntity -Prompt `$menuPrompt"
})
=== END SUCCESS LOG ===
"@
        
        $successLog | Out-File "/root/code/teams-sdk/debug/logs/autoattendant-success.log" -Append
        Write-Host "`n✅ Success details logged to: debug/logs/autoattendant-success.log" -ForegroundColor Green
        
    } catch {
        Write-Host "   ❌ Full Auto Attendant creation failed: $_" -ForegroundColor Red
    }
}

Write-Host "`n=== DEBUG SCRIPT COMPLETE ===" -ForegroundColor Green
Write-Host "Check the logs and results above to determine the correct API fix." -ForegroundColor Yellow