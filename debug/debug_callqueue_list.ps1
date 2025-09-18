# Debug script to test call queue listing functionality
# This mimics exactly what the FastAPI app does

Write-Host "=== Call Queue Listing Debug Script ==="
Write-Host "Starting authentication and listing process..."

# Same authentication as API
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force

Write-Host "Loading certificate from: $PfxPath"
try {
    $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
    Write-Host "✅ Certificate loaded successfully"
    Write-Host "Certificate Subject: $($Cert.Subject)"
    Write-Host "Certificate Thumbprint: $($Cert.Thumbprint)"
} catch {
    Write-Host "❌ Certificate loading failed: $_"
    exit 1
}

# Test Teams connection
Write-Host "`n--- Testing Teams Connection ---"
try {
    Write-Host "Checking if already connected to Teams..."
    $tenant = Get-CsTenant -ErrorAction Stop
    Write-Host "✅ Already connected to Teams"
    Write-Host "Tenant ID: $($tenant.TenantId)"
    Write-Host "Display Name: $($tenant.DisplayName)"
} catch {
    Write-Host "Not connected to Teams, connecting..."
    try {
        Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
        Write-Host "✅ Connected to Teams successfully"
        
        # Verify connection
        $tenant = Get-CsTenant
        Write-Host "Verified - Tenant ID: $($tenant.TenantId)"
    } catch {
        Write-Host "❌ Teams connection failed: $_"
        exit 1
    }
}

# Test call queue listing with detailed output
Write-Host "`n--- Testing Call Queue Listing ---"
try {
    Write-Host "Executing: Get-CsCallQueue"
    $queues = Get-CsCallQueue -ErrorAction Continue
    
    Write-Host "Command completed successfully"
    Write-Host "Queues variable type: $($queues.GetType().FullName)"
    Write-Host "Queues count: $($queues.Count)"
    
    if ($queues.Count -eq 0) {
        Write-Host "⚠️  No call queues returned by Get-CsCallQueue"
        Write-Host "This could mean:"
        Write-Host "  1. No call queues exist in the tenant"
        Write-Host "  2. Application doesn't have permission to list call queues"
        Write-Host "  3. Call queues exist but aren't visible to this authentication context"
    } else {
        Write-Host "✅ Found $($queues.Count) call queue(s):"
        
        foreach ($queue in $queues) {
            Write-Host "`n--- Queue Details ---"
            Write-Host "Identity: $($queue.Identity)"
            Write-Host "Name: $($queue.Name)"
            Write-Host "RoutingMethod: $($queue.RoutingMethod)"
            Write-Host "AgentAlertTime: $($queue.AgentAlertTime)"
            Write-Host "OverflowThreshold: $($queue.OverflowThreshold)"
            Write-Host "TimeoutThreshold: $($queue.TimeoutThreshold)"
        }
    }
    
} catch {
    Write-Host "❌ Get-CsCallQueue failed: $_"
    Write-Host "Error details: $($_.Exception.Message)"
}

# Test if we can create a queue and immediately see it
Write-Host "`n--- Testing Create Then List ---"
$testQueueName = "DebugTestQueue-$(Get-Date -Format 'MMddHHmmss')"

try {
    Write-Host "Creating test call queue: $testQueueName"
    $newQueue = New-CsCallQueue -Name $testQueueName -UseDefaultMusicOnHold $true -RoutingMethod Attendant
    Write-Host "✅ Created queue with ID: $($newQueue.Identity)"
    
    # Immediately try to list and see if it appears
    Write-Host "Immediately listing queues after creation..."
    $queuesAfter = Get-CsCallQueue
    Write-Host "Queues count after creation: $($queuesAfter.Count)"
    
    $foundNewQueue = $false
    foreach ($queue in $queuesAfter) {
        if ($queue.Name -eq $testQueueName) {
            Write-Host "✅ Found newly created queue in listing!"
            $foundNewQueue = $true
            break
        }
    }
    
    if (-not $foundNewQueue -and $queuesAfter.Count -gt 0) {
        Write-Host "⚠️  New queue not found in listing, but other queues exist"
        Write-Host "Existing queue names:"
        foreach ($queue in $queuesAfter) {
            Write-Host "  - $($queue.Name)"
        }
    } elseif (-not $foundNewQueue -and $queuesAfter.Count -eq 0) {
        Write-Host "❌ New queue not found and no queues in listing at all"
    }
    
    # Clean up - remove the test queue
    Write-Host "Cleaning up test queue..."
    Remove-CsCallQueue -Identity $newQueue.Identity -Confirm:$false
    Write-Host "✅ Test queue removed"
    
} catch {
    Write-Host "❌ Create/List test failed: $_"
}

Write-Host "`n=== Debug Script Complete ==="