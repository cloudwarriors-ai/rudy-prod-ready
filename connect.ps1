# ========================
# Variables
# ========================
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"    # Your tenant (directory) ID
$AppId    = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"    # Your Application (client) ID
$PfxPath  = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"       # Path to your .pfx file
$PfxPass  = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force

# ========================
# Load certificate from file (works cross-platform)
# ========================
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

# ========================
# Connect to Teams using the cert object
# ========================
Connect-MicrosoftTeams `
  -TenantId $TenantId `
  -ApplicationId $AppId `
  -Certificate $Cert

# ========================
# Connect to Microsoft Graph using the cert object
# ========================
Connect-MgGraph `
  -TenantId $TenantId `
  -ClientId $AppId `
  -Certificate $Cert `
  -NoWelcome

# ========================
# Enable ACS federation
# ========================
Set-CsTeamsAcsFederationConfiguration -Identity Global -EnableAcsUsers $true

# ========================
# Verify ACS federation
# ========================
Get-CsTeamsAcsFederationConfiguration
