# ========================
# Variables
# ========================
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"    # Your tenant (directory) ID
$AppId    = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"    # Your Application (client) ID
$PfxPath  = "/root/code/teams-sdk/teamsfed.pfx"       # Path to your .pfx file
$PfxPass  = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force

Write-Host "===================================================================="
Write-Host "Starting direct PowerShell test for user creation"
Write-Host "===================================================================="

try {
    # ========================
    # Load certificate from file
    # ========================
    Write-Host "Loading certificate..."
    $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
    Write-Host "Certificate loaded successfully: $($Cert.Subject)"
    
    # ========================
    # Connect to Teams using the cert object
    # ========================
    Write-Host "Connecting to Microsoft Teams..."
    Connect-MicrosoftTeams `
      -TenantId $TenantId `
      -ApplicationId $AppId `
      -Certificate $Cert
      
    # ========================
    # Connect to Microsoft Graph using the cert object
    # ========================
    Write-Host "Connecting to Microsoft Graph..."
    Connect-MgGraph `
      -TenantId $TenantId `
      -ClientId $AppId `
      -Certificate $Cert
    
    Write-Host "Connected to Microsoft Teams"
    
    # Get available commands
    Write-Host "Available commands in Microsoft Graph module:"
    Get-Command -Module Microsoft.Graph.Users | Select-Object -First 10
    
    # Get available auth connections
    Write-Host "Current auth connections:"
    Get-MgContext
    
    # Create a timestamp for unique user
    $timestamp = Get-Date -Format "yyyyMMddHHmmss"
    $displayName = "TestUser$timestamp"
    $upn = "testuser$timestamp@cloudwarriors.onmicrosoft.com"
    $mailNickname = "testuser$timestamp"
    
    Write-Host "===================================================================="
    Write-Host "Creating user with:"
    Write-Host "DisplayName: $displayName"
    Write-Host "UPN: $upn"
    Write-Host "MailNickname: $mailNickname"
    Write-Host "===================================================================="
    
    $passwordProfile = @{
        Password = "Test@P@ssw0rd123!"
        ForceChangePasswordNextSignIn = $true
    }
    
    # Try creating the user
    Write-Host "Creating user..."
    try {
        $newUser = New-MgUser -AccountEnabled:$true `
            -DisplayName $displayName `
            -UserPrincipalName $upn `
            -MailNickname $mailNickname `
            -PasswordProfile $passwordProfile `
            -ErrorAction Stop
        
        Write-Host "User created successfully!"
        $newUser | Format-List Id, DisplayName, UserPrincipalName
    }
    catch {
        Write-Host "Error creating user: $_"
        Write-Host "Exception details:"
        $_.Exception | Format-List -Force
    }
    
    # Try listing users
    Write-Host "Listing recent test users:"
    Get-MgUser -Filter "startswith(DisplayName, 'Test')" -Top 5 | Format-Table DisplayName, UserPrincipalName
    
} catch {
    Write-Host "An error occurred during test:"
    Write-Host $_.Exception.Message
    Write-Host $_.ScriptStackTrace
}

Write-Host "===================================================================="
Write-Host "Test completed"
Write-Host "===================================================================="