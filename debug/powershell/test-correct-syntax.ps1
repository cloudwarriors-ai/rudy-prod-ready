# Test Correct Auto Attendant Syntax
# Based on the parameter discovery, let's test the correct approach

# Standard auth setup
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

Write-Host "=== TESTING CORRECT AUTO ATTENDANT SYNTAX ==="

# Step 1: Create greeting prompt (this works)
Write-Host "`n1. Creating greeting prompt..."
try {
    $greetingPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Welcome to our test system. Please select an option."
    Write-Host "✅ Greeting prompt created successfully"
} catch {
    Write-Host "❌ Greeting prompt creation failed: $_"
    exit 1
}

# Step 2: Create menu option (this works)
Write-Host "`n2. Creating menu option..."
try {
    $menuTarget1 = New-CsAutoAttendantCallableEntity -Identity "aae57acd-8533-4ba0-9a0b-06895e4c6c47" -Type ApplicationEndpoint
    Write-Host "✅ Menu target created"
    
    $menuOption1 = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone1 -CallTarget $menuTarget1
    Write-Host "✅ Menu option created"
} catch {
    Write-Host "❌ Menu option creation failed: $_"
    exit 1
}

# Step 3: Create menu WITHOUT -Prompts parameter (the issue was here!)
Write-Host "`n3. Creating menu (correct syntax)..."
try {
    # The issue was trying to use -Prompts parameter which doesn't exist
    # New-CsAutoAttendantMenu should NOT have prompts - those go in the CallFlow!
    $menu = New-CsAutoAttendantMenu -Name "TestMenu" -MenuOptions @($menuOption1) -EnableDialByName $false
    Write-Host "✅ Menu created successfully (without prompts)"
} catch {
    Write-Host "❌ Menu creation failed: $_"
    exit 1
}

# Step 4: Create call flow with -Greetings parameter (this is where prompts go!)
Write-Host "`n4. Creating call flow..."
try {
    $defaultCallFlow = New-CsAutoAttendantCallFlow -Name "TestFlow" -Menu $menu -Greetings @($greetingPrompt)
    Write-Host "✅ Call flow created successfully with greetings"
} catch {
    Write-Host "❌ Call flow creation failed: $_"
    Write-Host "Error details: $($_.Exception.Message)"
    exit 1
}

# Step 5: Try to create a complete Auto Attendant
Write-Host "`n5. Creating complete Auto Attendant..."
try {
    $autoAttendant = New-CsAutoAttendant -Name "TestAutoAttendant-$(Get-Date -Format 'yyyyMMdd-HHmmss')" -LanguageId "en-US" -TimeZoneId "UTC" -DefaultCallFlow $defaultCallFlow -EnableVoiceResponse $true
    Write-Host "✅ Auto Attendant created successfully!"
    Write-Host "Identity: $($autoAttendant.Identity)"
    Write-Host "Name: $($autoAttendant.Name)"
    
    # Clean up - delete the test auto attendant
    Write-Host "`n6. Cleaning up test Auto Attendant..."
    Remove-CsAutoAttendant -Identity $autoAttendant.Identity
    Write-Host "✅ Test Auto Attendant deleted"
    
} catch {
    Write-Host "❌ Auto Attendant creation failed: $_"
    Write-Host "Error details: $($_.Exception.Message)"
}

Write-Host "`n=== SYNTAX TEST COMPLETED SUCCESSFULLY ==="