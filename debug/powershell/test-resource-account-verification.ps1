# Test Resource Account Verification - New API Implementation
# Purpose: Test the new resource account verification methods
# Created: September 18, 2025

Write-Host "=== RESOURCE ACCOUNT VERIFICATION TEST ===" -ForegroundColor Green

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

# Test queue - demoqueueiscake (known to have resource account)
$TestQueueId = "4c642d0d-6340-4f22-8294-0e0bc5dc8d41"

Write-Host "`n=== TESTING NEW check_queue_has_resource_account METHOD ===" -ForegroundColor Cyan

# This simulates the new check_queue_has_resource_account function
function Test-ResourceAccountCheck {
    param($QueueId)

    Write-Host "CHECKING_QUEUE_RESOURCE_ACCOUNT_START"

    try {
        $queue = Get-CsCallQueue -Identity $QueueId
        Write-Host "QUEUE_FOUND: $($queue.Name)"

        if ($queue.ApplicationInstances -and $queue.ApplicationInstances.Count -gt 0) {
            $resourceAccountId = $queue.ApplicationInstances[0]
            Write-Host "RESOURCE_ACCOUNT_FOUND_METHOD1: $resourceAccountId"
            Write-Host "RESOURCE_ACCOUNT_TYPE: ApplicationEndpoint"
        } else {
            Write-Host "NO_RESOURCE_ACCOUNT_METHOD1"

            Write-Host "SEARCHING_RESOURCE_ACCOUNTS_START"
            $resourceAccounts = Get-CsOnlineApplicationInstance
            Write-Host "TOTAL_RESOURCE_ACCOUNTS_FOUND: $($resourceAccounts.Count)"

            $foundResourceAccount = $null
            foreach ($resAccount in $resourceAccounts) {
                try {
                    $associations = Get-CsOnlineApplicationInstanceAssociation -Identity $resAccount.ObjectId -ErrorAction SilentlyContinue 2>$null
                    if ($associations) {
                        foreach ($assoc in $associations) {
                            if ($assoc.ConfigurationId -eq $QueueId -and $assoc.ConfigurationType -eq "CallQueue") {
                                $foundResourceAccount = $resAccount.ObjectId
                                Write-Host "RESOURCE_ACCOUNT_FOUND_METHOD2: $foundResourceAccount"
                                Write-Host "RESOURCE_ACCOUNT_DISPLAY_NAME: $($resAccount.DisplayName)"
                                break
                            }
                        }
                    }
                } catch {
                    continue
                }
                if ($foundResourceAccount) { break }
            }

            if (-not $foundResourceAccount) {
                Write-Host "NO_RESOURCE_ACCOUNT_FOUND"
            }
        }

        Write-Host "CHECKING_QUEUE_RESOURCE_ACCOUNT_END"
    } catch {
        Write-Host "ERROR_CHECKING_RESOURCE_ACCOUNT: $_"
    }
}

# Test the function
Test-ResourceAccountCheck -QueueId $TestQueueId

Write-Host "`n=== TESTING get_queues_with_resource_accounts METHOD ===" -ForegroundColor Cyan

# This simulates the get_queues_with_resource_accounts function
Write-Host "GETTING_QUEUES_WITH_RESOURCES_START"

try {
    $queues = Get-CsCallQueue
    Write-Host "TOTAL_QUEUES_FOUND: $($queues.Count)"

    $resourceAccounts = Get-CsOnlineApplicationInstance
    Write-Host "TOTAL_RESOURCE_ACCOUNTS_FOUND: $($resourceAccounts.Count)"

    foreach ($queue in $queues) {
        $hasResource = $false
        $resourceAccountId = $null
        $resourceAccountName = $null

        if ($queue.ApplicationInstances -and $queue.ApplicationInstances.Count -gt 0) {
            $hasResource = $true
            $resourceAccountId = $queue.ApplicationInstances[0]

            foreach ($resAccount in $resourceAccounts) {
                if ($resAccount.ObjectId -eq $resourceAccountId) {
                    $resourceAccountName = $resAccount.DisplayName
                    break
                }
            }
        } else {
            foreach ($resAccount in $resourceAccounts) {
                try {
                    $associations = Get-CsOnlineApplicationInstanceAssociation -Identity $resAccount.ObjectId -ErrorAction SilentlyContinue 2>$null
                    if ($associations) {
                        foreach ($assoc in $associations) {
                            if ($assoc.ConfigurationId -eq $queue.Identity -and $assoc.ConfigurationType -eq "CallQueue") {
                                $hasResource = $true
                                $resourceAccountId = $resAccount.ObjectId
                                $resourceAccountName = $resAccount.DisplayName
                                break
                            }
                        }
                    }
                } catch {
                    continue
                }
                if ($hasResource) { break }
            }
        }

        if ($hasResource) {
            Write-Host "QUEUE_WITH_RESOURCE_FOUND"
            Write-Host "QueueId: $($queue.Identity)"
            Write-Host "QueueName: $($queue.Name)"
            Write-Host "ResourceAccountId: $resourceAccountId"
            Write-Host "ResourceAccountName: $resourceAccountName"
        }
    }

    Write-Host "GETTING_QUEUES_WITH_RESOURCES_END"
} catch {
    Write-Host "ERROR_GETTING_QUEUES_WITH_RESOURCES: $_"
}

Write-Host "`n=== TESTING AUTO ATTENDANT CREATION WITH VERIFICATION ===" -ForegroundColor Cyan

# Test what happens when we try to create an AA with a queue that has no resource account
# First, let's create a test queue without a resource account
Write-Host "Creating a test call queue without resource account..."
try {
    $testQueueParams = @{
        Name = "TestQueue-NoResource-$(Get-Random)"
        LanguageId = "en-US"
        RoutingMethod = "Attendant"
        OverflowThreshold = 20
        OverflowAction = "Disconnect"
        TimeoutThreshold = 1200
        TimeoutAction = "Disconnect"
        AgentAlertTime = 30
        ConferenceMode = $true
        UseDefaultMusicOnHold = $true
    }

    $newQueue = New-CsCallQueue @testQueueParams
    Write-Host "✅ Test queue created: $($newQueue.Name)" -ForegroundColor Green
    Write-Host "   Identity: $($newQueue.Identity)"

    # Now test the resource account check on this new queue
    Write-Host "`nTesting resource account check on new queue..."
    Test-ResourceAccountCheck -QueueId $newQueue.Identity

    # Clean up
    Write-Host "`nCleaning up test queue..."
    Remove-CsCallQueue -Identity $newQueue.Identity -Force
    Write-Host "✅ Test queue removed" -ForegroundColor Green

} catch {
    Write-Host "❌ Error testing with new queue: $_" -ForegroundColor Red
}

Write-Host "`n=== SUMMARY ===" -ForegroundColor Green
Write-Host "Resource account verification test complete."
Write-Host "Check the output above for verification results."