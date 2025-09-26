# Debug script to create Rudy API Test call queue
# Test direct PowerShell approach

$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/Users/work/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force

try {
    Write-Host "Loading certificate..." -ForegroundColor Yellow
    $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
    Write-Host "✅ Certificate loaded"

    Write-Host "Connecting to Teams..." -ForegroundColor Yellow
    Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    Write-Host "✅ Teams connection successful"

    # First check if user exists
    Write-Host "Checking if user exists..." -ForegroundColor Yellow
    $user = Get-CsOnlineUser -Identity "gkiger@cloudwarriors.onmicrosoft.com" -ErrorAction SilentlyContinue
    if ($user) {
        Write-Host "✅ User found: $($user.DisplayName)"
    } else {
        Write-Host "❌ User not found, will proceed without agent for now"
    }

    # Create call queue
    Write-Host "Creating call queue: Rudy API Test" -ForegroundColor Yellow
    
    $params = @{
        Name = "Rudy API Test"
        LanguageId = "en-US"
        RoutingMethod = "Attendant"
        OverflowThreshold = 20
        OverflowAction = "Disconnect"
        TimeoutThreshold = 1200
        TimeoutAction = "Disconnect"
        AgentAlertTime = 30
        ConferenceMode = $true
        UseDefaultMusicOnHold = $true
        WelcomeTextToSpeechPrompt = "Welcome to Rudy API Test queue"
    }
    
    # Add user if found
    if ($user) {
        $params.Users = @($user.Identity)
        Write-Host "Adding user as agent: $($user.Identity)"
    }
    
    $callQueue = New-CsCallQueue @params
    
    Write-Host "✅ Call queue created successfully!" -ForegroundColor Green
    Write-Host "Identity: $($callQueue.Identity)"
    Write-Host "Name: $($callQueue.Name)"
    
    # Now try to add Rudy Agent if it exists as a separate step
    Write-Host "Checking for 'Rudy Agent' user..." -ForegroundColor Yellow
    $rudyUser = Get-CsOnlineUser | Where-Object { $_.DisplayName -like "*Rudy*" -or $_.UserPrincipalName -like "*rudy*" }
    
    if ($rudyUser) {
        Write-Host "Found Rudy user: $($rudyUser.DisplayName) - $($rudyUser.UserPrincipalName)"
        
        # Get current users and add Rudy
        $currentUsers = @()
        if ($callQueue.Users) {
            $currentUsers = $callQueue.Users
        }
        
        if ($currentUsers -notcontains $rudyUser.Identity) {
            $newUsers = $currentUsers + $rudyUser.Identity
            Set-CsCallQueue -Identity $callQueue.Identity -Users $newUsers
            Write-Host "✅ Added Rudy Agent to call queue"
        } else {
            Write-Host "ℹ️ Rudy Agent already in call queue"
        }
    } else {
        Write-Host "❌ No 'Rudy Agent' user found in the system"
        Write-Host "Available users:"
        Get-CsOnlineUser | Select-Object DisplayName, UserPrincipalName | ForEach-Object {
            Write-Host "  - $($_.DisplayName) ($($_.UserPrincipalName))"
        }
    }

} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host "Exception: $($_.Exception.GetType().FullName)"
} finally {
    Write-Host "Disconnecting..." -ForegroundColor Yellow
    Disconnect-MicrosoftTeams -ErrorAction SilentlyContinue
}