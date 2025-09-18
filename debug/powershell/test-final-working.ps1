# FINAL WORKING Auto Attendant Creation

# Standard auth setup
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert

Write-Host "=== FINAL WORKING AUTO ATTENDANT CREATION ==="

try {
    Write-Host "Creating Auto Attendant: FinalTestAA"
    
    # Create greeting prompt
    $greetingPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Welcome to our company. Please listen to the following options."
    
    # Create menu option for call queue routing
    $menuTarget1 = New-CsAutoAttendantCallableEntity -Identity "aae57acd-8533-4ba0-9a0b-06895e4c6c47" -Type ApplicationEndpoint
    $menuOption1 = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone1 -CallTarget $menuTarget1
    
    # Create menu prompt (REQUIRED - this was missing!)
    $menuPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Please press 1 to connect to our support team, or stay on the line to speak with an operator."
    
    # Create menu (with prompts and without EnableDialByName parameter issues)
    $menu = New-CsAutoAttendantMenu -Name "MainMenu" -MenuOptions @($menuOption1) -Prompts @($menuPrompt)
    
    # Create default call flow
    $defaultCallFlow = New-CsAutoAttendantCallFlow -Name "DefaultFlow" -Menu $menu -Greetings @($greetingPrompt)
    
    # Create Auto Attendant (without -EnableVoiceResponse parameter causing issues)
    $autoAttendant = New-CsAutoAttendant -Name "FinalTestAA-$(Get-Date -Format 'yyyyMMdd-HHmmss')" -LanguageId "en-US" -TimeZoneId "UTC" -DefaultCallFlow $defaultCallFlow
    
    Write-Host "AUTOATTENDANT_CREATED_SUCCESS"
    Write-Host "Identity: $($autoAttendant.Identity)"
    Write-Host "Name: $($autoAttendant.Name)"
    Write-Host "LanguageId: $($autoAttendant.LanguageId)"
    
    # Don't clean up - let's keep this one for testing
    Write-Host "Auto Attendant left for manual testing/cleanup"
    
} catch {
    Write-Host "AUTOATTENDANT_CREATION_FAILED: $_"
    Write-Host "Full error: $($_.Exception.Message)"
}