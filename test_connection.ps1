# Test Microsoft Teams API connection with correct auth keys path
$ErrorActionPreference = "Continue"

Write-Host "=== Testing Microsoft Teams API Connection ===" -ForegroundColor Green

# Correct variables for this environment
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/Users/work/teams-sdk/auth-keys/teamsfed.pfx"  # Corrected path
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force

Write-Host "Loading certificate from: $PfxPath" -ForegroundColor Yellow

try {
    # Load certificate
    $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
    Write-Host "✅ Certificate loaded successfully" -ForegroundColor Green
    Write-Host "   Subject: $($Cert.Subject)" -ForegroundColor Gray
    Write-Host "   Thumbprint: $($Cert.Thumbprint)" -ForegroundColor Gray
    
    # Connect to Microsoft Teams
    Write-Host "Connecting to Microsoft Teams..." -ForegroundColor Yellow
    Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    Write-Host "✅ Teams connection successful" -ForegroundColor Green
    
    # Connect to Microsoft Graph
    Write-Host "Connecting to Microsoft Graph..." -ForegroundColor Yellow
    Connect-MgGraph -TenantId $TenantId -ClientId $AppId -Certificate $Cert -NoWelcome
    Write-Host "✅ Graph connection successful" -ForegroundColor Green
    
    # Verify Teams connection
    Write-Host "Verifying Teams connection..." -ForegroundColor Yellow
    $teamsConfig = Get-CsTeamsAcsFederationConfiguration
    Write-Host "✅ Teams ACS Federation Status: $($teamsConfig.EnableAcsUsers)" -ForegroundColor Green
    
    # Verify Graph connection
    Write-Host "Verifying Graph connection..." -ForegroundColor Yellow
    $context = Get-MgContext
    Write-Host "✅ Graph Context - ClientId: $($context.ClientId), TenantId: $($context.TenantId)" -ForegroundColor Green
    
    # Test basic operations
    Write-Host "Testing basic operations..." -ForegroundColor Yellow
    
    # Test getting users (first 5)
    try {
        $users = Get-MgUser -Top 5
        Write-Host "✅ Successfully retrieved $($users.Count) users" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Error getting users: $_" -ForegroundColor Red
    }
    
    # Test getting call queues
    try {
        $callQueues = Get-CsCallQueue
        Write-Host "✅ Successfully retrieved $($callQueues.Count) call queues" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Error getting call queues: $_" -ForegroundColor Red
    }
    
    Write-Host "=== Connection Test Complete ===" -ForegroundColor Green
    
}
catch {
    Write-Host "❌ Connection failed: $_" -ForegroundColor Red
    Write-Host "Stack trace: $($_.ScriptStackTrace)" -ForegroundColor Red
}