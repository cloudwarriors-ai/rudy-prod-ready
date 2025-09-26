# Check available users and create Rudy API Test call queue
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

    # Check available users
    Write-Host "`nChecking available users..." -ForegroundColor Cyan
    $users = Get-CsOnlineUser | Where-Object { $_.Enabled -eq $true }
    
    Write-Host "Available users in tenant:"
    foreach ($user in $users) {
        Write-Host "  - $($user.DisplayName) ($($user.UserPrincipalName))" -ForegroundColor White
    }
    
    # Look for Rudy specifically
    $rudyUser = $users | Where-Object { 
        $_.DisplayName -like "*Rudy*" -or 
        $_.UserPrincipalName -like "*rudy*" -or 
        $_.DisplayName -like "*Agent*" -or
        $_.UserPrincipalName -like "*agent*"
    }
    
    if ($rudyUser) {
        Write-Host "`n✅ Found Rudy/Agent user:" -ForegroundColor Green
        $selectedUser = $rudyUser[0]  # Take first match if multiple
        Write-Host "  Selected: $($selectedUser.DisplayName) - $($selectedUser.UserPrincipalName)" -ForegroundColor Green
    } else {
        Write-Host "`n⚠️ No 'Rudy' or 'Agent' user found. Using first available user:" -ForegroundColor Yellow
        $selectedUser = $users[0]
        Write-Host "  Selected: $($selectedUser.DisplayName) - $($selectedUser.UserPrincipalName)" -ForegroundColor Yellow
    }

    # Create call queue
    Write-Host "`nCreating call queue: 'Rudy API Test'..." -ForegroundColor Cyan
    
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
        Users = @($selectedUser.Identity)
    }
    
    $callQueue = New-CsCallQueue @params
    
    Write-Host "✅ Call queue created successfully!" -ForegroundColor Green
    Write-Host "  Identity: $($callQueue.Identity)" -ForegroundColor White
    Write-Host "  Name: $($callQueue.Name)" -ForegroundColor White
    Write-Host "  Agent: $($selectedUser.DisplayName)" -ForegroundColor White
    
    # Verify the queue was created
    Write-Host "`nVerifying call queue creation..." -ForegroundColor Cyan
    $verification = Get-CsCallQueue -Identity $callQueue.Identity
    if ($verification) {
        Write-Host "✅ Verification successful - Call queue exists" -ForegroundColor Green
        Write-Host "  Queue Name: $($verification.Name)" -ForegroundColor White
        Write-Host "  Agent Count: $($verification.Users.Count)" -ForegroundColor White
    } else {
        Write-Host "❌ Verification failed - Call queue not found" -ForegroundColor Red
    }

} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host "Exception Type: $($_.Exception.GetType().FullName)" -ForegroundColor Red
    Write-Host "Stack Trace: $($_.Exception.StackTrace)" -ForegroundColor Red
} finally {
    Write-Host "`nDisconnecting..." -ForegroundColor Yellow
    try {
        Disconnect-MicrosoftTeams
        Write-Host "✅ Disconnected successfully" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Disconnect warning: $_" -ForegroundColor Yellow
    }
}