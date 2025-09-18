# Test Menu Prompts - The REAL Issue!

# Standard auth setup
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert

Write-Host "=== TESTING MENU PROMPTS REQUIREMENT ==="

# Step 1: Create menu option
$menuTarget1 = New-CsAutoAttendantCallableEntity -Identity "aae57acd-8533-4ba0-9a0b-06895e4c6c47" -Type ApplicationEndpoint
$menuOption1 = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone1 -CallTarget $menuTarget1
Write-Host "✅ Menu option created"

# Step 2: Create a menu prompt (this is what was missing!)
Write-Host "`n1. Creating menu prompt..."
try {
    $menuPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Please press 1 for support, or stay on the line to speak with someone."
    Write-Host "✅ Menu prompt created successfully"
} catch {
    Write-Host "❌ Menu prompt creation failed: $_"
    exit 1
}

# Step 3: Create menu WITH prompts
Write-Host "`n2. Creating menu with prompts..."
try {
    $menu = New-CsAutoAttendantMenu -Name "MainMenu" -MenuOptions @($menuOption1) -Prompts @($menuPrompt) -EnableDialByName $false
    Write-Host "✅ Menu created successfully with prompts!"
} catch {
    Write-Host "❌ Menu creation with prompts failed: $_"
    exit 1
}

# Step 4: Create greeting prompt (separate from menu prompt)
Write-Host "`n3. Creating greeting prompt for call flow..."
$greetingPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Welcome to our company. Thank you for calling."
Write-Host "✅ Greeting prompt created"

# Step 5: Create call flow
Write-Host "`n4. Creating call flow..."
try {
    $defaultCallFlow = New-CsAutoAttendantCallFlow -Name "DefaultFlow" -Menu $menu -Greetings @($greetingPrompt)
    Write-Host "✅ Call flow created successfully"
} catch {
    Write-Host "❌ Call flow creation failed: $_"
    Write-Host "Error: $($_.Exception.Message)"
    exit 1
}

# Step 6: Create complete Auto Attendant
Write-Host "`n5. Creating complete Auto Attendant..."
try {
    $autoAttendant = New-CsAutoAttendant -Name "TestAA-$(Get-Date -Format 'yyyyMMdd-HHmmss')" -LanguageId "en-US" -TimeZoneId "UTC" -DefaultCallFlow $defaultCallFlow -EnableVoiceResponse $true
    Write-Host "✅ Auto Attendant created successfully!"
    Write-Host "Identity: $($autoAttendant.Identity)"
    Write-Host "Name: $($autoAttendant.Name)"
    
    # Clean up
    Write-Host "`n6. Cleaning up..."
    Remove-CsAutoAttendant -Identity $autoAttendant.Identity
    Write-Host "✅ Test Auto Attendant cleaned up"
    
} catch {
    Write-Host "❌ Auto Attendant creation failed: $_"
    Write-Host "Error: $($_.Exception.Message)"
}

Write-Host "`n=== MENU PROMPTS TEST COMPLETED ==="
Write-Host "Key findings:"
Write-Host "1. Menu requires -Prompts parameter when using DTMF options"
Write-Host "2. Menu prompts are DIFFERENT from greeting prompts"
Write-Host "3. Menu prompts tell user which keys to press"
Write-Host "4. Greeting prompts welcome the caller"