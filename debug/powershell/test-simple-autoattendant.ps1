# Simple Auto Attendant Creation Test
# Purpose: Test minimal Auto Attendant with correct PowerShell syntax
# Created: September 18, 2025

Write-Host "=== SIMPLE AUTO ATTENDANT TEST ===" -ForegroundColor Green

# Authentication
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert

# Resource account from investigation 
$resourceAccountId = "aae57acd-8533-4ba0-9a0b-06895e4c6c47"

Write-Host "Creating minimal Auto Attendant..." -ForegroundColor Cyan

try {
    # Create the simplest possible Auto Attendant
    $greetingPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Welcome to our test auto attendant"
    
    # Create menu option - transfer to resource account
    $menuTarget = New-CsAutoAttendantCallableEntity -Identity $resourceAccountId -Type ApplicationEndpoint
    $menuOption = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone1 -CallTarget $menuTarget
    
    # Create menu with single option
    $menu = New-CsAutoAttendantMenu -Name "TestMenu" -MenuOptions $menuOption -EnableDialByName $false
    
    # Create call flow
    $callFlow = New-CsAutoAttendantCallFlow -Name "DefaultFlow" -Menu $menu -Greetings $greetingPrompt
    
    # Create Auto Attendant
    $aaName = "TestAA-$(Get-Date -Format 'MMdd-HHmm')"
    Write-Host "Creating: $aaName"
    
    $autoAttendant = New-CsAutoAttendant -Name $aaName -LanguageId "en-US" -DefaultCallFlow $callFlow
    
    Write-Host "✅ Success! Auto Attendant created:" -ForegroundColor Green
    Write-Host "   Name: $($autoAttendant.Name)" -ForegroundColor White
    Write-Host "   Identity: $($autoAttendant.Identity)" -ForegroundColor White
    
} catch {
    Write-Host "❌ Failed: $_" -ForegroundColor Red
    Write-Host "Error details: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "=== TEST COMPLETE ===" -ForegroundColor Green