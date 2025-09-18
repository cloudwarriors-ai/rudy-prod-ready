# ========================
# Variables
# ========================
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"    # Your tenant (directory) ID
$AppId    = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"    # Your Application (client) ID
$PfxPath  = "/root/code/teams-sdk/teamsfed.pfx"       # Path to your .pfx file
$PfxPass  = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force

Write-Host "===================================================================="
Write-Host "Checking permissions for the application"
Write-Host "===================================================================="

try {
    # ========================
    # Load certificate from file
    # ========================
    Write-Host "Loading certificate..."
    $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
    Write-Host "Certificate loaded successfully: $($Cert.Subject)"
    
    # ========================
    # Connect to Microsoft Graph
    # ========================
    Write-Host "Connecting to Microsoft Graph..."
    Connect-MgGraph `
      -TenantId $TenantId `
      -ClientId $AppId `
      -Certificate $Cert
    
    Write-Host "Connected to Microsoft Graph"
    
    # Check what permissions we have
    Write-Host "Checking current permissions..."
    $context = Get-MgContext
    Write-Host "Context: $($context | Format-List | Out-String)"
    Write-Host "Scopes: $($context.Scopes -join ", ")"
    
    # Try listing users (read operation which should be allowed)
    Write-Host "Trying to list users (read operation)..."
    try {
        $users = Get-MgUser -Top 5
        Write-Host "Successfully listed users:"
        $users | Format-Table DisplayName, UserPrincipalName
    } catch {
        Write-Host "Error listing users: $_"
    }
    
    # Try to get ACS federation configuration which we know works
    Write-Host "Getting ACS federation configuration..."
    try {
        $acsFederation = Get-CsTeamsAcsFederationConfiguration
        Write-Host "ACS Federation Configuration:"
        $acsFederation | Format-List
    } catch {
        Write-Host "Error getting ACS federation: $_"
    }
    
} catch {
    Write-Host "An error occurred:"
    Write-Host $_.Exception.Message
    Write-Host $_.ScriptStackTrace
}

Write-Host "===================================================================="
Write-Host "Permission check completed"
Write-Host "===================================================================="