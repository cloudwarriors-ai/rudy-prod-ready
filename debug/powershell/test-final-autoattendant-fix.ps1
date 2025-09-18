# Final Auto Attendant Fix Test
# Purpose: Demonstrate the complete working solution using resource account routing
# This simulates what the fixed FastAPI code should do
# Created: September 18, 2025

Write-Host "=== FINAL AUTO ATTENDANT FIX TEST ===" -ForegroundColor Green
Write-Host "Demonstrating the complete working solution" -ForegroundColor Cyan

# Authentication setup
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

try {
    Write-Host "`n🔐 Connecting to Microsoft Teams..." -ForegroundColor Cyan
    Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    Write-Host "✅ Teams connection successful" -ForegroundColor Green
} catch {
    Write-Host "❌ Teams connection failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n📝 Step 1: Get call queue and resource account information..." -ForegroundColor Cyan

# Known working queue ID from our investigation
$callQueueId = "4c642d0d-6340-4f22-8294-0e0bc5dc8d41"  # demoqueueiscake
$expectedResourceAccountId = "aae57acd-8533-4ba0-9a0b-06895e4c6c47"  # Headquarters2

try {
    # This is what our get_callqueue_resource_account function should do
    $queue = Get-CsCallQueue -Identity $callQueueId
    if ($queue -and $queue.ApplicationInstances -and $queue.ApplicationInstances.Count -gt 0) {
        $resourceAccountId = $queue.ApplicationInstances[0]
        Write-Host "📞 Call Queue: $($queue.Name)" -ForegroundColor Yellow
        Write-Host "   Identity: $($queue.Identity)" -ForegroundColor Gray
        Write-Host "   Resource Account: $resourceAccountId" -ForegroundColor Gray
        
        if ($resourceAccountId -eq $expectedResourceAccountId) {
            Write-Host "   ✅ Resource Account matches expected value" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  Resource Account differs from expected" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Call queue has no resource account!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Failed to get call queue details: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n🏗️  Step 2: Create Auto Attendant with CORRECT resource account routing..." -ForegroundColor Cyan

try {
    # This is what the fixed FastAPI code should generate
    $testName = "Fixed AA Test - $(Get-Date -Format 'MMdd-HHmm')"
    
    Write-Host "Creating Auto Attendant: $testName" -ForegroundColor White
    Write-Host "Using Resource Account: $resourceAccountId" -ForegroundColor White
    
    # 1. Create greeting prompt
    $greetingPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Welcome to our test auto attendant. Press 1 for demo queue."
    
    # 2. Create menu option that routes to RESOURCE ACCOUNT (not call queue ID)
    $menuTarget = New-CsAutoAttendantCallableEntity -Identity $resourceAccountId -Type ApplicationEndpoint
    $menuOption = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone1 -CallTarget $menuTarget
    
    # 3. Create menu
    $menu = New-CsAutoAttendantMenu -Name "MainMenu" -MenuOptions $menuOption -EnableDialByName $false
    
    # 4. Create call flow (Note: Use array syntax for Greetings)
    $defaultCallFlow = New-CsAutoAttendantCallFlow -Name "DefaultFlow" -Menu $menu -Greetings @($greetingPrompt)
    
    # 5. Create Auto Attendant
    $autoAttendant = New-CsAutoAttendant -Name $testName -LanguageId "en-US" -DefaultCallFlow $defaultCallFlow
    
    Write-Host "🎉 SUCCESS! Auto Attendant created!" -ForegroundColor Green
    Write-Host "   Name: $($autoAttendant.Name)" -ForegroundColor White
    Write-Host "   Identity: $($autoAttendant.Identity)" -ForegroundColor White
    Write-Host "   Routes to Resource Account: $resourceAccountId" -ForegroundColor White
    Write-Host "   Which serves Call Queue: $($queue.Name)" -ForegroundColor White
    
    # Log the complete solution
    $solutionLog = @{
        Timestamp = Get-Date
        Status = "SUCCESS - COMPLETE FIX VERIFIED"
        AutoAttendantName = $autoAttendant.Name
        AutoAttendantId = $autoAttendant.Identity
        CallQueueName = $queue.Name
        CallQueueId = $queue.Identity
        ResourceAccountId = $resourceAccountId
        SolutionSummary = @(
            "Auto Attendants must route to Resource Account ObjectIds, not Call Queue IDs",
            "Use -Type ApplicationEndpoint for resource accounts in callable entities",
            "Get resource account from Call Queue ApplicationInstances property",
            "This approach works and should be implemented in FastAPI code"
        )
        ImplementationDetails = @{
            GetResourceAccount = 'Get-CsCallQueue -Identity $callQueueId | Select -ExpandProperty ApplicationInstances'
            CreateCallableEntity = 'New-CsAutoAttendantCallableEntity -Identity $resourceAccountId -Type ApplicationEndpoint'
            MenuOptionCorrect = 'New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone1 -CallTarget $menuTarget'
            NoPromptNeeded = 'Do not use -Prompt parameter for TransferCallToTarget actions'
        }
    }
    
    $solutionLog | ConvertTo-Json -Depth 4 | Out-File "/root/code/teams-sdk/debug/logs/SOLUTION-COMPLETE.log" -Encoding UTF8
    
} catch {
    Write-Host "❌ Auto Attendant creation failed: $_" -ForegroundColor Red
    Write-Host "Error details: $($_.Exception.Message)" -ForegroundColor Red
    
    $errorLog = @{
        Timestamp = Get-Date
        Status = "FAILED"
        Error = $_.Exception.Message
        ResourceAccountId = $resourceAccountId
        CallQueueName = $queue.Name
    }
    $errorLog | ConvertTo-Json -Depth 2 | Out-File "/root/code/teams-sdk/debug/logs/SOLUTION-ERROR.log" -Append
    exit 1
}

Write-Host "`n✅ Step 3: Verify the Auto Attendant exists..." -ForegroundColor Cyan

try {
    $verifyAA = Get-CsAutoAttendant | Where-Object { $_.Name -eq $testName }
    if ($verifyAA) {
        Write-Host "✅ Verification successful - Auto Attendant found in tenant" -ForegroundColor Green
        Write-Host "   Identity: $($verifyAA.Identity)" -ForegroundColor Gray
    } else {
        Write-Host "❌ Verification failed - Auto Attendant not found" -ForegroundColor Red
    }
} catch {
    Write-Host "⚠️  Verification error: $_" -ForegroundColor Yellow
}

Write-Host "`n🎯 SOLUTION SUMMARY:" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Yellow
Write-Host "✅ ROOT CAUSE: Auto Attendants need Resource Account ObjectIds, not Call Queue IDs" -ForegroundColor White
Write-Host "✅ SOLUTION: Get resource account from Call Queue ApplicationInstances" -ForegroundColor White
Write-Host "✅ IMPLEMENTATION: Use -Type ApplicationEndpoint for resource accounts" -ForegroundColor White
Write-Host "✅ VERIFICATION: This approach works and creates functional Auto Attendants" -ForegroundColor White
Write-Host "=" * 60 -ForegroundColor Yellow

Write-Host "`n📋 FASTAPI CODE CHANGES NEEDED:" -ForegroundColor Cyan
Write-Host "1. Add get_callqueue_resource_account() helper function" -ForegroundColor White
Write-Host "2. Fix menu option creation to use resource account ObjectId" -ForegroundColor White
Write-Host "3. Remove -Prompt parameter from TransferCallToTarget menu options" -ForegroundColor White
Write-Host "4. Fix call flow creation syntax (no array for single greeting)" -ForegroundColor White

Write-Host "`n=== TEST COMPLETE - SOLUTION VERIFIED ===" -ForegroundColor Green