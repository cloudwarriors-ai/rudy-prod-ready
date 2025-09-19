$TenantId = 'e7b105b2-720e-4b5b-9310-1a414c06356a'
$AppId = '968fafbb-27b8-400a-b8c3-a90eb3c2de26'
$PfxPath = '/Users/cloudwarriors/MS-Teams-ETL/teams-sdk/auth-keys/teamsfed.pfx'
$PfxPass = ConvertTo-SecureString 'P@ssw0rd!' -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

Write-Host 'Connecting to Microsoft Teams...'
Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert

Write-Host 'Getting user information for gkiger@cloudwarriors.onmicrosoft.com...'
try {
    $user = Get-CsOnlineUser -Identity 'gkiger@cloudwarriors.onmicrosoft.com'
    if (-not $user) {
        Write-Host 'ERROR: User gkiger@cloudwarriors.onmicrosoft.com not found'
        exit 1
    }
    Write-Host "Found user: $($user.DisplayName) - ID: $($user.Identity)"
    
    # Call queue identities from the previous creation
    $queueIdentities = @(
        '826f8e6d-21dd-404c-9506-9ec9eb46ffc9',  # Red
        'de4cc8fc-0c8f-4528-be9d-002c607a565d',  # Blue
        '4ac5f35b-c265-49ec-a7b0-53fd5207c092',  # Green
        'e32fcc03-32fb-4016-aaf8-98e32f80ae5b',  # Yellow
        '0a66aa5f-a29d-4e03-bcb4-fdc643a58233',  # Purple
        'a94e3b70-76a7-4ce7-96a8-625df6a2457e',  # Orange
        '6e93e0a1-2dfb-45b3-8383-e9c6f9994209',  # Pink
        'c5674910-b615-4f20-b27b-309989c4ab93',  # Cyan
        'f2e50fc6-ddd7-4659-9366-b0939055600f',  # Magenta
        '7345e168-747f-4e8a-a614-60b6ca9c9495'   # Lime
    )
    
    $successCount = 0
    $errorCount = 0
    
    foreach ($queueId in $queueIdentities) {
        try {
            Write-Host "Adding user to queue: $queueId"
            
            # Get current call queue configuration
            $callQueue = Get-CsCallQueue -Identity $queueId
            Write-Host "Queue name: $($callQueue.Name)"
            
            # Get current users list
            $currentUsers = @()
            if ($callQueue.Users) {
                $currentUsers = $callQueue.Users
            }
            
            # Add the new user if not already present
            $userId = $user.Identity
            if ($currentUsers -notcontains $userId) {
                $newUsers = $currentUsers + $userId
                
                Set-CsCallQueue -Identity $queueId -Users $newUsers
                Write-Host "SUCCESS: Added gkiger@cloudwarriors.onmicrosoft.com to $($callQueue.Name)"
                $successCount++
            } else {
                Write-Host "INFO: User already present in $($callQueue.Name)"
                $successCount++
            }
            
            Start-Sleep -Seconds 1
            
        } catch {
            Write-Host "ERROR adding user to queue ${queueId}: $($_.Exception.Message)"
            $errorCount++
        }
    }
    
    Write-Host ""
    Write-Host "=== SUMMARY ==="
    Write-Host "Successfully added agent to $successCount queues"
    Write-Host "Errors: $errorCount"
    Write-Host "User gkiger@cloudwarriors.onmicrosoft.com (Greg Kiger) is now an agent in all color call queues!"
    
} catch {
    Write-Host "ERROR getting user: $($_.Exception.Message)"
}