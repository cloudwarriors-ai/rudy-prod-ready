# Debug script to verify test agent was added to call queue and get user GUID
# Date: September 18, 2025

$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

# Connect to Teams and Graph
Write-Host "=== CONNECTING TO SERVICES ==="
Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
Connect-MgGraph -ClientId $AppId -TenantId $TenantId -Certificate $Cert

# Get user information
Write-Host "`n=== USER INFORMATION ==="
$userEmail = "testagent@cloudwarriors.onmicrosoft.com"
Write-Host "Looking up user: $userEmail"

try {
    $user = Get-MgUser -Filter "userPrincipalName eq '$userEmail'"
    if ($user) {
        Write-Host "✅ User found:"
        Write-Host "  Display Name: $($user.DisplayName)"
        Write-Host "  User Principal Name: $($user.UserPrincipalName)"
        Write-Host "  User GUID: $($user.Id)"
        Write-Host "  Account Enabled: $($user.AccountEnabled)"
        
        # Store GUID for later use
        $userGuid = $user.Id
    } else {
        Write-Host "❌ User not found"
        exit 1
    }
} catch {
    Write-Host "❌ Error looking up user: $_"
    exit 1
}

# Get call queue information
Write-Host "`n=== CALL QUEUE INFORMATION ==="
$queueId = "ca6cf9b4-55d6-4123-8321-9114a09985dd"
Write-Host "Getting call queue: $queueId"

try {
    $callQueue = Get-CsCallQueue -Identity $queueId
    if ($callQueue) {
        Write-Host "✅ Call queue found:"
        Write-Host "  Name: $($callQueue.Name)"
        Write-Host "  Identity: $($callQueue.Identity)"
        Write-Host "  Routing Method: $($callQueue.RoutingMethod)"
        
        # Check agents
        Write-Host "`n=== AGENT VERIFICATION ==="
        if ($callQueue.Users) {
            Write-Host "  Current agents (GUIDs):"
            foreach ($agentGuid in $callQueue.Users) {
                Write-Host "    - $agentGuid"
                
                # Try to get user details for each GUID
                try {
                    $agentUser = Get-MgUser -UserId $agentGuid -ErrorAction SilentlyContinue
                    if ($agentUser) {
                        Write-Host "      ↳ $($agentUser.DisplayName) ($($agentUser.UserPrincipalName))"
                    }
                } catch {
                    Write-Host "      ↳ Could not resolve user details"
                }
            }
            
            # Check if our test agent is in the list
            if ($callQueue.Users -contains $userGuid) {
                Write-Host "  ✅ Test agent IS present in call queue"
            } else {
                Write-Host "  ❌ Test agent is NOT in call queue"
            }
        } else {
            Write-Host "  ❌ No agents assigned to this call queue"
        }
    } else {
        Write-Host "❌ Call queue not found"
    }
} catch {
    Write-Host "❌ Error getting call queue: $_"
}

# Summary for documentation
Write-Host "`n=== SUMMARY FOR DOCUMENTATION ==="
Write-Host "User Email: $userEmail"
Write-Host "User GUID: $userGuid"
Write-Host "Call Queue: Alpha Test Queue"
Write-Host "Queue ID: $queueId"
Write-Host "Status: $(if ($callQueue.Users -contains $userGuid) { 'Agent Successfully Added' } else { 'Agent Not Found in Queue' })"

# Disconnect
Disconnect-MgGraph -ErrorAction SilentlyContinue
Disconnect-MicrosoftTeams -ErrorAction SilentlyContinue

Write-Host "`n=== VERIFICATION COMPLETE ==="