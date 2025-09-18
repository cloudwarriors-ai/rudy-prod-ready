# Investigate Call Queue Resource Account Requirements
# Purpose: Understand why call queue ID is not recognized for Auto Attendant
# Created: September 18, 2025

Write-Host "=== CALL QUEUE RESOURCE ACCOUNT INVESTIGATION ===" -ForegroundColor Green

# Authentication setup
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

try {
    Write-Host "`n1. Connecting to Microsoft Teams..." -ForegroundColor Cyan
    Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    Write-Host "✅ Teams connection successful" -ForegroundColor Green
} catch {
    Write-Host "❌ Teams connection failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n2. Getting all call queues to examine their structure..." -ForegroundColor Cyan

try {
    $allQueues = Get-CsCallQueue
    Write-Host "Found $($allQueues.Count) call queues" -ForegroundColor White
    
    foreach ($queue in $allQueues) {
        if ($queue.Name -like "*Alpha*" -or $queue.Name -like "*Test*") {
            Write-Host "`n📞 Queue: $($queue.Name)" -ForegroundColor Yellow
            Write-Host "   Identity: $($queue.Identity)" -ForegroundColor Gray
            Write-Host "   ApplicationInstances: $($queue.ApplicationInstances -join ', ')" -ForegroundColor Gray
            
            # Check if this queue has resource accounts
            if ($queue.ApplicationInstances -and $queue.ApplicationInstances.Count -gt 0) {
                Write-Host "   ✅ Has Application Instances (Resource Accounts)" -ForegroundColor Green
                foreach ($appInstance in $queue.ApplicationInstances) {
                    Write-Host "     - Resource Account: $appInstance" -ForegroundColor Cyan
                }
            } else {
                Write-Host "   ❌ NO Application Instances found!" -ForegroundColor Red
                Write-Host "   This is likely why Auto Attendant creation fails" -ForegroundColor Red
            }
        }
    }
    
} catch {
    Write-Host "❌ Failed to get call queues: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n3. Checking resource accounts in the tenant..." -ForegroundColor Cyan

try {
    $resourceAccounts = Get-CsOnlineApplicationInstance
    Write-Host "Found $($resourceAccounts.Count) resource accounts" -ForegroundColor White
    
    foreach ($resAccount in $resourceAccounts) {
        Write-Host "`n🏷️  Resource Account: $($resAccount.DisplayName)" -ForegroundColor Yellow
        Write-Host "   ObjectId: $($resAccount.ObjectId)" -ForegroundColor Gray
        Write-Host "   UserPrincipalName: $($resAccount.UserPrincipalName)" -ForegroundColor Gray
        Write-Host "   ApplicationId: $($resAccount.ApplicationId)" -ForegroundColor Gray
        Write-Host "   PhoneNumber: $($resAccount.PhoneNumber)" -ForegroundColor Gray
        
        # Check what this resource account is associated with
        $associations = Get-CsOnlineApplicationInstanceAssociation -Identity $resAccount.ObjectId 2>$null
        if ($associations) {
            Write-Host "   Associations: $($associations.Count)" -ForegroundColor Cyan
            foreach ($assoc in $associations) {
                Write-Host "     - Associated with: $($assoc.ConfigurationId) (Type: $($assoc.ConfigurationType))" -ForegroundColor Cyan
            }
        } else {
            Write-Host "   ❌ No associations found" -ForegroundColor Red
        }
    }
    
} catch {
    Write-Host "❌ Failed to get resource accounts: $_" -ForegroundColor Red
}

Write-Host "`n4. Understanding the issue..." -ForegroundColor Cyan
Write-Host @"
🔍 ANALYSIS:
For Auto Attendants to route to Call Queues, the call queue needs:
1. A Resource Account (Application Instance) associated with it
2. The Resource Account should be used in Auto Attendant routing, not the Call Queue ID

The error 'application endpoint with specified ID not found' suggests:
- Our call queue doesn't have a proper resource account
- Or we need to use the resource account ID, not the call queue ID

NEXT STEPS:
1. Create a resource account for the Alpha Test Queue
2. Associate the resource account with the call queue  
3. Use the resource account ID in Auto Attendant routing
"@ -ForegroundColor Yellow

Write-Host "`n=== INVESTIGATION COMPLETE ===" -ForegroundColor Green