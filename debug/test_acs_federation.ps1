# ========================
# Variables
# ========================
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"    # Your tenant (directory) ID
$AppId    = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"    # Your Application (client) ID
$PfxPath  = "/root/code/teams-sdk/teamsfed.pfx"       # Path to your .pfx file
$PfxPass  = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force

Write-Host "===================================================================="
Write-Host "Testing ACS Federation Configuration"
Write-Host "===================================================================="

try {
    # ========================
    # Load certificate from file
    # ========================
    Write-Host "Loading certificate..."
    $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
    Write-Host "Certificate loaded successfully: $($Cert.Subject)"
    
    # ========================
    # Connect to Teams
    # ========================
    Write-Host "Connecting to Microsoft Teams..."
    Connect-MicrosoftTeams `
      -TenantId $TenantId `
      -ApplicationId $AppId `
      -Certificate $Cert
    
    Write-Host "Connected to Microsoft Teams"
    
    # ========================
    # Get current ACS federation configuration
    # ========================
    Write-Host "Getting current ACS federation configuration..."
    $acsFederation = Get-CsTeamsAcsFederationConfiguration
    Write-Host "Current ACS Federation Configuration:"
    $acsFederation | Format-List
    
    # ========================
    # Update ACS federation configuration
    # ========================
    Write-Host "Updating ACS federation configuration..."
    
    # First, toggle the setting to ensure a change
    $currentValue = $acsFederation.EnableAcsUsers
    $newValue = -not $currentValue
    
    # Update the setting
    Set-CsTeamsAcsFederationConfiguration -Identity Global -EnableAcsUsers $newValue
    Write-Host "Updated ACS federation to EnableAcsUsers: $newValue"
    
    # Verify the change
    $updatedConfig = Get-CsTeamsAcsFederationConfiguration
    Write-Host "Updated ACS Federation Configuration:"
    $updatedConfig | Format-List
    
    # Change it back to the original value
    Set-CsTeamsAcsFederationConfiguration -Identity Global -EnableAcsUsers $currentValue
    Write-Host "Restored ACS federation to EnableAcsUsers: $currentValue"
    
    # Final verification
    $finalConfig = Get-CsTeamsAcsFederationConfiguration
    Write-Host "Final ACS Federation Configuration:"
    $finalConfig | Format-List
    
} catch {
    Write-Host "An error occurred:"
    Write-Host $_.Exception.Message
    Write-Host $_.ScriptStackTrace
}

Write-Host "===================================================================="
Write-Host "ACS Federation test completed"
Write-Host "===================================================================="