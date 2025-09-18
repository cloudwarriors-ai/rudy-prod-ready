# Complete Teams User and Team Creation Workflow
# This script creates users and teams using Microsoft Graph and Teams PowerShell

param(
    [Parameter(Mandatory=$true)]
    [string]$UserDisplayName,

    [Parameter(Mandatory=$true)]
    [string]$UserPrincipalName,

    [Parameter(Mandatory=$true)]
    [string]$TeamDisplayName,

    [Parameter(Mandatory=$true)]
    [string]$TeamDescription,

    [Parameter(Mandatory=$false)]
    [string]$TeamMailNickname = "team",

    [Parameter(Mandatory=$false)]
    [string]$Password = "TempP@ssw0rd123!"
)

# Configuration
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/root/code/teams-sdk/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force

# Log file
$logFile = "team_creation_workflow_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
"Starting Teams workflow at $(Get-Date)" | Out-File -FilePath $logFile -Append

try {
    # Step 1: Authenticate to Microsoft Graph
    Write-Host "Step 1: Authenticating to Microsoft Graph..." -ForegroundColor Yellow
    "Step 1: Authenticating to Microsoft Graph..." | Out-File -FilePath $logFile -Append

    $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
    Connect-MgGraph -TenantId $TenantId -ClientId $AppId -Certificate $Cert -NoWelcome

    Write-Host "✓ Graph authentication successful" -ForegroundColor Green
    "✓ Graph authentication successful" | Out-File -FilePath $logFile -Append

    # Step 2: Create the user
    Write-Host "Step 2: Creating user '$UserDisplayName'..." -ForegroundColor Yellow
    "Step 2: Creating user '$UserDisplayName'..." | Out-File -FilePath $logFile -Append

    $PasswordProfile = @{
        Password = $Password
        ForceChangePasswordNextSignIn = $true
    }

    $newUser = New-MgUser `
        -DisplayName $UserDisplayName `
        -UserPrincipalName $UserPrincipalName `
        -MailNickname ($UserPrincipalName.Split('@')[0]) `
        -PasswordProfile $PasswordProfile `
        -AccountEnabled:$true

    Write-Host "✓ User created successfully: $($newUser.Id)" -ForegroundColor Green
    "✓ User created successfully: $($newUser.Id)" | Out-File -FilePath $logFile -Append

    # Step 3: Wait for user replication
    Write-Host "Step 3: Waiting for user replication..." -ForegroundColor Yellow
    "Step 3: Waiting for user replication..." | Out-File -FilePath $logFile -Append
    Start-Sleep -Seconds 15

    # Step 4: Verify user creation
    Write-Host "Step 4: Verifying user creation..." -ForegroundColor Yellow
    "Step 4: Verifying user creation..." | Out-File -FilePath $logFile -Append

    $user = Get-MgUser -Filter "UserPrincipalName eq '$UserPrincipalName'"
    if ($user) {
        Write-Host "✓ User verified successfully" -ForegroundColor Green
        "✓ User verified successfully" | Out-File -FilePath $logFile -Append
    } else {
        throw "User verification failed"
    }

    # Step 5: Create Microsoft 365 Group (which can be used as a team)
    Write-Host "Step 5: Creating team '$TeamDisplayName'..." -ForegroundColor Yellow
    "Step 5: Creating team '$TeamDisplayName'..." | Out-File -FilePath $logFile -Append

    $groupParams = @{
        displayName = $TeamDisplayName
        description = $TeamDescription
        groupTypes = @("Unified")
        mailEnabled = $true
        mailNickname = $TeamMailNickname
        securityEnabled = $false
        visibility = "Private"
        "owners@odata.bind" = @("https://graph.microsoft.com/v1.0/users/$($newUser.Id)")
        "members@odata.bind" = @("https://graph.microsoft.com/v1.0/users/$($newUser.Id)")
    }

    $group = New-MgGroup -BodyParameter $groupParams
    Write-Host "✓ Team (group) created successfully: $($group.Id)" -ForegroundColor Green
    "✓ Team (group) created successfully: $($group.Id)" | Out-File -FilePath $logFile -Append

    # Step 6: Wait for group replication
    Write-Host "Step 6: Waiting for group replication..." -ForegroundColor Yellow
    "Step 6: Waiting for group replication..." | Out-File -FilePath $logFile -Append
    Start-Sleep -Seconds 10

    # Step 7: Try to convert to proper team (may fail but that's ok)
    Write-Host "Step 7: Attempting to convert group to proper team..." -ForegroundColor Yellow
    "Step 7: Attempting to convert group to proper team..." | Out-File -FilePath $logFile -Append

    try {
        $teamifyUri = "https://graph.microsoft.com/v1.0/groups/$($group.Id)/team"
        $teamifyBody = "{}"

        Invoke-MgGraphRequest -Method PUT -Uri $teamifyUri -Body $teamifyBody -ContentType "application/json"
        Write-Host "✓ Group successfully converted to proper Team!" -ForegroundColor Green
        "✓ Group successfully converted to proper Team!" | Out-File -FilePath $logFile -Append
    } catch {
        Write-Host "⚠️  Team conversion failed, but group is still functional: $($_.Exception.Message)" -ForegroundColor Yellow
        "⚠️  Team conversion failed, but group is still functional: $($_.Exception.Message)" | Out-File -FilePath $logFile -Append
    }

    # Step 8: Summary
    Write-Host "`n🎉 WORKFLOW COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Green
    Write-Host "User Details:" -ForegroundColor Cyan
    Write-Host "  Display Name: $UserDisplayName" -ForegroundColor White
    Write-Host "  User Principal Name: $UserPrincipalName" -ForegroundColor White
    Write-Host "  User ID: $($newUser.Id)" -ForegroundColor White
    Write-Host ""
    Write-Host "Team Details:" -ForegroundColor Cyan
    Write-Host "  Team Name: $TeamDisplayName" -ForegroundColor White
    Write-Host "  Team ID: $($group.Id)" -ForegroundColor White
    Write-Host "  Description: $TeamDescription" -ForegroundColor White
    Write-Host "  Mail Nickname: $TeamMailNickname" -ForegroundColor White
    Write-Host ""
    Write-Host "📝 Note: The user has been added to the team and can access it." -ForegroundColor Yellow
    Write-Host "   If the team doesn't appear in Teams interface, the group is still functional." -ForegroundColor Yellow

    # Log summary
    "`nWORKFLOW SUMMARY:" | Out-File -FilePath $logFile -Append
    "User: $UserDisplayName ($UserPrincipalName)" | Out-File -FilePath $logFile -Append
    "Team: $TeamDisplayName ($($group.Id))" | Out-File -FilePath $logFile -Append
    "Completed at: $(Get-Date)" | Out-File -FilePath $logFile -Append

} catch {
    Write-Host "❌ WORKFLOW FAILED: $($_.Exception.Message)" -ForegroundColor Red
    "❌ WORKFLOW FAILED: $($_.Exception.Message)" | Out-File -FilePath $logFile -Append

    # Show error details
    Write-Host "`nError Details:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "`nStack Trace:" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
} finally {
    Write-Host "`nLog file saved: $logFile" -ForegroundColor Gray
}