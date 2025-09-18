# ========================
# Variables
# ========================
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"    # Your tenant (directory) ID
$AppId    = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"    # Your Application (client) ID
$PfxPath  = "/root/code/teams-sdk/teamsfed.pfx"       # Path to your .pfx file
$PfxPass  = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force

Write-Host "===================================================================="
Write-Host "Testing team creation"
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
    
    # ========================
    # Connect to Microsoft Graph
    # ========================
    Write-Host "Connecting to Microsoft Graph..."
    Connect-MgGraph `
      -TenantId $TenantId `
      -ClientId $AppId `
      -Certificate $Cert `
      -NoWelcome
    
    Write-Host "Connected to both Teams and Graph APIs"
    
    # Generate a unique timestamp for the team name
    $timestamp = Get-Date -Format "yyyyMMddHHmmss"
    $teamName = "TestTeam$timestamp"
    $teamDescription = "Test team created at $timestamp for API testing"
    
    Write-Host "===================================================================="
    Write-Host "Creating a team with:"
    Write-Host "Name: $teamName"
    Write-Host "Description: $teamDescription"
    Write-Host "===================================================================="
    
    # Try creating a team
    Write-Host "Creating team..."
    try {
        $teamParams = @{
            "template@odata.bind" = "https://graph.microsoft.com/v1.0/teamsTemplates('standard')"
            displayName = $teamName
            description = $teamDescription
            visibility = "private"
        }
        
        $newTeam = New-MgTeam -BodyParameter $teamParams
        
        Write-Host "Team created successfully!"
        Write-Host "Team ID: $($newTeam.Id)"
        Write-Host "Team details:"
        $newTeam | Format-List Id, DisplayName, Description
        
        # List recently created teams
        Write-Host "Listing recent teams:"
        Get-MgTeam -Filter "startswith(DisplayName, 'Test')" -Top 5 | Format-Table DisplayName, Description
        
    } catch {
        Write-Host "Error creating team: $_"
        Write-Host "Exception details:"
        $_.Exception | Format-List -Force
    }
    
} catch {
    Write-Host "An error occurred:"
    Write-Host $_.Exception.Message
    Write-Host $_.ScriptStackTrace
}

Write-Host "===================================================================="
Write-Host "Team creation test completed"
Write-Host "===================================================================="