# Test Resource Account Lookup - Simplified
# Purpose: Get the exact working PowerShell commands for resource account lookup
# Created: September 18, 2025

Write-Host "=== RESOURCE ACCOUNT LOOKUP TEST ===" -ForegroundColor Green

# Authentication setup
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

try {
    Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    Write-Host "✅ Teams connection successful" -ForegroundColor Green
} catch {
    Write-Host "❌ Teams connection failed: $_" -ForegroundColor Red
    exit 1
}

# Test queue - demoqueueiscake
$TestQueueId = "4c642d0d-6340-4f22-8294-0e0bc5dc8d41"

Write-Host "`n=== METHOD 1: Check Queue ApplicationInstances ===" -ForegroundColor Cyan
try {
    $queue = Get-CsCallQueue -Identity $TestQueueId
    Write-Host "Queue Name: $($queue.Name)"
    Write-Host "ApplicationInstances Count: $($queue.ApplicationInstances.Count)"
    
    if ($queue.ApplicationInstances -and $queue.ApplicationInstances.Count -gt 0) {
        $resourceAccountId = $queue.ApplicationInstances[0]
        Write-Host "✅ METHOD 1 SUCCESS: $resourceAccountId" -ForegroundColor Green
        
        # Output for API
        Write-Host "API_RESULT_METHOD1: $resourceAccountId"
    } else {
        Write-Host "❌ METHOD 1 FAILED: No ApplicationInstances" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ METHOD 1 ERROR: $_" -ForegroundColor Red
}

Write-Host "`n=== METHOD 2: Search Resource Account Associations ===" -ForegroundColor Cyan
try {
    Write-Host "Getting all resource accounts..."
    $resourceAccounts = Get-CsOnlineApplicationInstance
    Write-Host "Found $($resourceAccounts.Count) resource accounts"
    
    $foundResourceAccount = $null
    
    foreach ($resAccount in $resourceAccounts) {
        Write-Host "Checking: $($resAccount.DisplayName) - $($resAccount.ObjectId)"
        
        try {
            $associations = Get-CsOnlineApplicationInstanceAssociation -Identity $resAccount.ObjectId -ErrorAction SilentlyContinue
            
            if ($associations) {
                foreach ($assoc in $associations) {
                    Write-Host "  Association: $($assoc.ConfigurationId) (Type: $($assoc.ConfigurationType))"
                    
                    if ($assoc.ConfigurationId -eq $TestQueueId -and $assoc.ConfigurationType -eq "CallQueue") {
                        $foundResourceAccount = $resAccount.ObjectId
                        Write-Host "✅ METHOD 2 SUCCESS: Found association!" -ForegroundColor Green
                        Write-Host "   Resource Account: $($resAccount.DisplayName)"
                        Write-Host "   ObjectId: $foundResourceAccount"
                        
                        # Output for API
                        Write-Host "API_RESULT_METHOD2: $foundResourceAccount"
                        break
                    }
                }
            }
        } catch {
            Write-Host "  Skipping due to error: $_" -ForegroundColor Yellow
        }
        
        if ($foundResourceAccount) { break }
    }
    
    if (-not $foundResourceAccount) {
        Write-Host "❌ METHOD 2 FAILED: No associations found" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ METHOD 2 ERROR: $_" -ForegroundColor Red
}

Write-Host "`n=== SIMPLE API COMMAND TEST ===" -ForegroundColor Cyan

# Test the simplest possible command that could work in the API
if ($foundResourceAccount) {
    Write-Host "Testing simple resource account lookup for API..."
    
    # This is what we want to use in the API
    $SimpleTestCommand = @"
`$queue = Get-CsCallQueue -Identity '$TestQueueId'
if (`$queue.ApplicationInstances -and `$queue.ApplicationInstances.Count -gt 0) {
    Write-Host 'RESOURCE_FOUND:' `$queue.ApplicationInstances[0]
} else {
    `$resourceAccounts = Get-CsOnlineApplicationInstance
    foreach (`$resAccount in `$resourceAccounts) {
        `$associations = Get-CsOnlineApplicationInstanceAssociation -Identity `$resAccount.ObjectId -ErrorAction SilentlyContinue 2>`$null
        if (`$associations) {
            foreach (`$assoc in `$associations) {
                if (`$assoc.ConfigurationId -eq '$TestQueueId' -and `$assoc.ConfigurationType -eq 'CallQueue') {
                    Write-Host 'RESOURCE_FOUND:' `$resAccount.ObjectId
                    break
                }
            }
        }
        if (`$?) { break }
    }
}
"@

    Write-Host "Simple API Command:" -ForegroundColor Yellow
    Write-Host $SimpleTestCommand -ForegroundColor Gray
    
    Write-Host "`nExecuting simple command..."
    try {
        Invoke-Expression $SimpleTestCommand
    } catch {
        Write-Host "❌ Simple command failed: $_" -ForegroundColor Red
    }
}

Write-Host "`n=== SUMMARY ===" -ForegroundColor Green
Write-Host "Test complete. Check output above for API_RESULT lines."