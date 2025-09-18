# Minimal Auto Attendant Test - Step by step debugging
# Purpose: Find the correct PowerShell syntax by building incrementally
# Created: September 18, 2025

$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert

$resourceAccountId = "aae57acd-8533-4ba0-9a0b-06895e4c6c47"

Write-Host "Step 1: Create greeting prompt"
try {
    $greetingPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Welcome"
    Write-Host "✅ Greeting prompt created"
} catch {
    Write-Host "❌ Greeting prompt failed: $_"
    exit 1
}

Write-Host "`nStep 2: Create callable entity"
try {
    $menuTarget = New-CsAutoAttendantCallableEntity -Identity $resourceAccountId -Type ApplicationEndpoint
    Write-Host "✅ Callable entity created"
} catch {
    Write-Host "❌ Callable entity failed: $_"
    exit 1
}

Write-Host "`nStep 3: Create menu option"
try {
    $menuOption = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone1 -CallTarget $menuTarget
    Write-Host "✅ Menu option created"
} catch {
    Write-Host "❌ Menu option failed: $_"
    exit 1
}

Write-Host "`nStep 4: Create menu with prompt"
try {
    # The menu needs a prompt for user input
    $menuPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Press 1 for our demo queue"
    $menu = New-CsAutoAttendantMenu -Name "TestMenu" -MenuOptions @($menuOption) -Prompts @($menuPrompt)
    Write-Host "✅ Menu created with proper prompts"
} catch {
    Write-Host "❌ Menu creation failed: $_"
    exit 1
}

Write-Host "`nStep 5: Create call flow"
try {
    # Try different variants of the call flow creation
    Write-Host "Trying variant A: -Greetings `$greetingPrompt"
    $defaultCallFlow = New-CsAutoAttendantCallFlow -Name "DefaultFlow" -Menu $menu -Greetings $greetingPrompt
    Write-Host "✅ Call flow created with variant A"
} catch {
    Write-Host "❌ Variant A failed: $_"
    try {
        Write-Host "Trying variant B: -Greetings @(`$greetingPrompt)"
        $defaultCallFlow = New-CsAutoAttendantCallFlow -Name "DefaultFlow" -Menu $menu -Greetings @($greetingPrompt)
        Write-Host "✅ Call flow created with variant B"
    } catch {
        Write-Host "❌ Variant B failed: $_"
        try {
            Write-Host "Trying variant C: No Greetings parameter"
            $defaultCallFlow = New-CsAutoAttendantCallFlow -Name "DefaultFlow" -Menu $menu
            Write-Host "✅ Call flow created with variant C"
        } catch {
            Write-Host "❌ All variants failed: $_"
            exit 1
        }
    }
}

Write-Host "`nStep 6: Create Auto Attendant"
try {
    $testName = "Minimal AA Test - $(Get-Date -Format 'MMdd-HHmm')"
    $autoAttendant = New-CsAutoAttendant -Name $testName -LanguageId "en-US" -TimeZoneId "Eastern Standard Time" -DefaultCallFlow $defaultCallFlow
    Write-Host "✅ Auto Attendant created successfully!"
    Write-Host "   Name: $($autoAttendant.Name)"
    Write-Host "   Identity: $($autoAttendant.Identity)"
} catch {
    Write-Host "❌ Auto Attendant creation failed: $_"
}

Write-Host "`n=== Test Complete ==="