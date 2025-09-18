# Isolate the exact source of the -Prompts error

# Standard auth setup
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert

# Test each command one by one
Write-Host "1. Creating menu target..."
$menuTarget1 = New-CsAutoAttendantCallableEntity -Identity "aae57acd-8533-4ba0-9a0b-06895e4c6c47" -Type ApplicationEndpoint
Write-Host "✅ Menu target created"

Write-Host "2. Creating menu option..."
$menuOption1 = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone1 -CallTarget $menuTarget1
Write-Host "✅ Menu option created"

Write-Host "3. Testing exact command from API..."
# This is the exact command from the API
try {
    $menu = New-CsAutoAttendantMenu -Name "MainMenu" -MenuOptions @($menuOption1) -EnableDialByName $false
    Write-Host "✅ Menu created successfully"
} catch {
    Write-Host "❌ Exact API command failed: $_"
    Write-Host "Full exception: $($_.Exception)"
    
    # Check what parameters this cmdlet actually accepts
    Write-Host "`nActual parameters for New-CsAutoAttendantMenu:"
    (Get-Command New-CsAutoAttendantMenu).Parameters.Keys | Sort-Object | ForEach-Object { Write-Host "  $_" }
}

# Try variations
Write-Host "`n4. Trying without parameter names..."
try {
    $menu2 = New-CsAutoAttendantMenu "MainMenu2" @($menuOption1) $false
    Write-Host "✅ Menu created without parameter names"
} catch {
    Write-Host "❌ Without parameter names failed: $_"
}

Write-Host "`n5. Trying minimal parameters..."
try {
    $menu3 = New-CsAutoAttendantMenu -Name "MainMenu3" -MenuOptions @($menuOption1)
    Write-Host "✅ Menu created with minimal parameters"
} catch {
    Write-Host "❌ Minimal parameters failed: $_"
}