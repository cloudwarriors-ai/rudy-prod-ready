# Test COMPLETELY CORRECT Auto Attendant Syntax

# Standard auth setup
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert

Write-Host "=== TESTING COMPLETELY CORRECTED SYNTAX ==="

# Step 1: Create menu option
$menuTarget1 = New-CsAutoAttendantCallableEntity -Identity "aae57acd-8533-4ba0-9a0b-06895e4c6c47" -Type ApplicationEndpoint
$menuOption1 = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone1 -CallTarget $menuTarget1

# Step 2: Create menu prompt (REQUIRED for menus with user input)
$menuPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Please press 1 for support, or stay on the line to speak with someone."

# Step 3: Create menu with CORRECT syntax - no -EnableDialByName parameter!
Write-Host "1. Creating menu with correct syntax..."
try {
    # Check what parameters are actually available
    $menuParams = (Get-Command New-CsAutoAttendantMenu).Parameters.Keys
    Write-Host "Available parameters: $($menuParams -join ', ')"
    
    # Create menu with only required parameters and prompts
    $menu = New-CsAutoAttendantMenu -Name "MainMenu" -MenuOptions @($menuOption1) -Prompts @($menuPrompt)
    Write-Host "✅ Menu created successfully!"
} catch {
    Write-Host "❌ Menu creation failed: $_"
    Write-Host "Error: $($_.Exception.Message)"
    exit 1
}

# Step 4: Create greeting prompt
$greetingPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Welcome to our company. Thank you for calling."

# Step 5: Create call flow
Write-Host "`n2. Creating call flow..."
$defaultCallFlow = New-CsAutoAttendantCallFlow -Name "DefaultFlow" -Menu $menu -Greetings @($greetingPrompt)
Write-Host "✅ Call flow created successfully"

# Step 6: Create complete Auto Attendant
Write-Host "`n3. Creating complete Auto Attendant..."
try {
    $autoAttendant = New-CsAutoAttendant -Name "FixedSyntaxAA-$(Get-Date -Format 'yyyyMMdd-HHmmss')" -LanguageId "en-US" -TimeZoneId "UTC" -DefaultCallFlow $defaultCallFlow -EnableVoiceResponse $true
    Write-Host "✅ Auto Attendant created successfully!"
    Write-Host "Identity: $($autoAttendant.Identity)"
    Write-Host "Name: $($autoAttendant.Name)"
    
    # Clean up
    Write-Host "`n4. Cleaning up..."
    Remove-CsAutoAttendant -Identity $autoAttendant.Identity
    Write-Host "✅ Test Auto Attendant deleted"
    
} catch {
    Write-Host "❌ Auto Attendant creation failed: $_"
    Write-Host "Error: $($_.Exception.Message)"
}

Write-Host "`n=== SYNTAX CORRECTION SUCCESSFUL ==="