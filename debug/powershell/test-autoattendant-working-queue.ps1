# Test Auto Attendant Creation with Working Call Queue
# Purpose: Create Auto Attendant that routes to "demoqueueiscake" queue using resource account
# Created: September 18, 2025

Write-Host "=== AUTO ATTENDANT CREATION TEST - WORKING QUEUE ===" -ForegroundColor Green

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

Write-Host "`n2. Getting working call queue details..." -ForegroundColor Cyan

try {
    # Get the working call queue (demoqueueiscake)
    $workingQueue = Get-CsCallQueue | Where-Object { $_.Name -like "*demoqueueiscake*" }
    
    if ($workingQueue) {
        Write-Host "📞 Found working queue: $($workingQueue.Name)" -ForegroundColor Yellow
        Write-Host "   Identity: $($workingQueue.Identity)" -ForegroundColor Gray
        Write-Host "   ApplicationInstances: $($workingQueue.ApplicationInstances -join ', ')" -ForegroundColor Gray
        
        if ($workingQueue.ApplicationInstances -and $workingQueue.ApplicationInstances.Count -gt 0) {
            $resourceAccountId = $workingQueue.ApplicationInstances[0]
            Write-Host "   ✅ Resource Account ID: $resourceAccountId" -ForegroundColor Green
        } else {
            Write-Host "   ❌ No resource account found!" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "❌ Working queue 'demoqueueiscake' not found!" -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host "❌ Failed to get working queue: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n3. Creating Auto Attendant with proper resource account routing..." -ForegroundColor Cyan

try {
    # Create Auto Attendant that routes to the resource account
    $greetingPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Welcome to our test auto attendant. Press 1 for demo queue."
    
    # Create menu option that routes to the RESOURCE ACCOUNT, not the call queue directly
    # Note: No prompt needed for TransferCallToTarget actions, only for announcements
    $menuTarget1 = New-CsAutoAttendantCallableEntity -Identity $resourceAccountId -Type ApplicationEndpoint
    $menuOption1 = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone1 -CallTarget $menuTarget1
    
    # Create menu
    $menu = New-CsAutoAttendantMenu -Name "TestMenu" -MenuOptions @($menuOption1) -EnableDialByName $false
    
    # Create default call flow
    $defaultCallFlow = New-CsAutoAttendantCallFlow -Name "DefaultFlow" -Menu $menu -Greetings $greetingPrompt
    
    # Create Auto Attendant
    $autoAttendantName = "Test AA - Resource Account - $(Get-Date -Format 'MMdd-HHmm')"
    $autoAttendant = New-CsAutoAttendant -Name $autoAttendantName -LanguageId "en-US" -DefaultCallFlow $defaultCallFlow -EnableVoiceResponse $true
    
    Write-Host "✅ Auto Attendant created successfully!" -ForegroundColor Green
    Write-Host "   Name: $($autoAttendant.Name)" -ForegroundColor White
    Write-Host "   Identity: $($autoAttendant.Identity)" -ForegroundColor White
    Write-Host "   Routes to Resource Account: $resourceAccountId" -ForegroundColor White
    Write-Host "   Which serves Call Queue: $($workingQueue.Name)" -ForegroundColor White
    
    # Log success details
    $successInfo = @{
        Timestamp = Get-Date
        AutoAttendantName = $autoAttendant.Name
        AutoAttendantId = $autoAttendant.Identity
        CallQueueName = $workingQueue.Name
        CallQueueId = $workingQueue.Identity
        ResourceAccountId = $resourceAccountId
        Status = "SUCCESS - Fixed routing using resource account"
    }
    
    $successInfo | ConvertTo-Json -Depth 2 | Out-File "/root/code/teams-sdk/debug/logs/autoattendant-success.log" -Append
    
} catch {
    Write-Host "❌ Auto Attendant creation failed: $_" -ForegroundColor Red
    
    # Log failure details
    $errorInfo = @{
        Timestamp = Get-Date
        Error = $_.Exception.Message
        ResourceAccountId = $resourceAccountId
        CallQueueName = $workingQueue.Name
        Status = "FAILED"
    }
    
    $errorInfo | ConvertTo-Json -Depth 2 | Out-File "/root/code/teams-sdk/debug/logs/autoattendant-errors.log" -Append
    exit 1
}

Write-Host "`n4. Verifying Auto Attendant was created..." -ForegroundColor Cyan

try {
    $createdAA = Get-CsAutoAttendant | Where-Object { $_.Name -eq $autoAttendantName }
    if ($createdAA) {
        Write-Host "✅ Verification successful - Auto Attendant exists in tenant" -ForegroundColor Green
    } else {
        Write-Host "❌ Verification failed - Auto Attendant not found in listing" -ForegroundColor Red
    }
} catch {
    Write-Host "⚠️  Verification error: $_" -ForegroundColor Yellow
}

Write-Host "`n=== TEST COMPLETE ===" -ForegroundColor Green
Write-Host "📋 KEY FINDINGS:" -ForegroundColor Yellow
Write-Host "   • Auto Attendants must route to Resource Account ObjectIds, not Call Queue IDs" -ForegroundColor White
Write-Host "   • Use -Type ApplicationEndpoint for resource accounts" -ForegroundColor White
Write-Host "   • Resource Account ID: $resourceAccountId" -ForegroundColor White
Write-Host "   • This approach should be implemented in the FastAPI code" -ForegroundColor White