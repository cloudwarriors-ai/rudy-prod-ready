# PowerShell Debug Script: Test Call Queue Listing
# Purpose: Investigate why Get-CsCallQueue returns empty results
# Created: $(Get-Date)

Write-Host "=== Teams SDK Call Queue Listing Debug ===" -ForegroundColor Cyan
Write-Host "Script: test-callqueue-listing.ps1"
Write-Host "Timestamp: $(Get-Date)"
Write-Host "============================================" -ForegroundColor Cyan

# Authentication Configuration (from API patterns)
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force

# Debug log file
$DebugLogPath = "/root/code/teams-sdk/debug/logs/debug-powershell.log"

# Initialize debug log
$debugStart = @{
    Timestamp = Get-Date
    ScriptName = "test-callqueue-listing.ps1"
    Action = "START_DEBUG_SESSION"
    TenantId = $TenantId
    AppId = $AppId
} | ConvertTo-Json -Depth 2

Write-Host "📝 Logging to: $DebugLogPath"
$debugStart | Out-File $DebugLogPath -Append

try {
    Write-Host "🔑 Loading certificate..." -ForegroundColor Yellow
    $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
    Write-Host "✅ Certificate loaded successfully"
    Write-Host "   - Thumbprint: $($Cert.Thumbprint)"
    Write-Host "   - Subject: $($Cert.Subject)"
    
    # Log certificate info
    @{
        Timestamp = Get-Date
        Action = "CERTIFICATE_LOADED"
        Thumbprint = $Cert.Thumbprint
        Subject = $Cert.Subject
        HasPrivateKey = $Cert.HasPrivateKey
    } | ConvertTo-Json -Depth 2 | Out-File $DebugLogPath -Append

} catch {
    Write-Host "❌ Certificate loading failed: $_" -ForegroundColor Red
    @{
        Timestamp = Get-Date
        Action = "CERTIFICATE_ERROR"
        Error = $_.Exception.Message
    } | ConvertTo-Json -Depth 2 | Out-File $DebugLogPath -Append
    exit 1
}

try {
    Write-Host "🔗 Connecting to Microsoft Teams..." -ForegroundColor Yellow
    Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    Write-Host "✅ Teams connection successful" -ForegroundColor Green
    
    # Log connection success
    @{
        Timestamp = Get-Date
        Action = "TEAMS_CONNECTION_SUCCESS"
        TenantId = $TenantId
        AppId = $AppId
    } | ConvertTo-Json -Depth 2 | Out-File $DebugLogPath -Append

} catch {
    Write-Host "❌ Teams connection failed: $_" -ForegroundColor Red
    @{
        Timestamp = Get-Date
        Action = "TEAMS_CONNECTION_ERROR"
        Error = $_.Exception.Message
    } | ConvertTo-Json -Depth 2 | Out-File $DebugLogPath -Append
    exit 1
}

# Test Get-CsCallQueue with extensive debug output
Write-Host "📞 Testing Get-CsCallQueue..." -ForegroundColor Yellow

try {
    # Check current PowerShell session info
    $sessionInfo = Get-PSSession
    Write-Host "Current PS Sessions: $($sessionInfo.Count)"
    
    # Log session info
    @{
        Timestamp = Get-Date
        Action = "POWERSHELL_SESSION_INFO"
        SessionCount = $sessionInfo.Count
        Sessions = $sessionInfo | ForEach-Object { @{
            Id = $_.Id
            Name = $_.Name
            State = $_.State
            ConfigurationName = $_.ConfigurationName
        }}
    } | ConvertTo-Json -Depth 3 | Out-File $DebugLogPath -Append

    # Execute Get-CsCallQueue with timing
    $startTime = Get-Date
    Write-Host "⏱️  Starting Get-CsCallQueue at: $startTime"
    
    $callQueues = Get-CsCallQueue
    
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    Write-Host "⏱️  Completed Get-CsCallQueue at: $endTime"
    Write-Host "⏱️  Duration: $duration seconds"
    
    # Analyze results
    if ($callQueues) {
        Write-Host "✅ Call queues retrieved successfully" -ForegroundColor Green
        Write-Host "   - Result Type: $($callQueues.GetType().FullName)"
        Write-Host "   - Count: $($callQueues.Count)"
        
        if ($callQueues.Count -gt 0) {
            Write-Host "📋 First call queue details:"
            $firstQueue = $callQueues[0]
            Write-Host "   - Name: $($firstQueue.Name)"
            Write-Host "   - Identity: $($firstQueue.Identity)"
            Write-Host "   - Id: $($firstQueue.Id)"
        }
        
        # Log successful results
        @{
            Timestamp = Get-Date
            Action = "GET_CALLQUEUE_SUCCESS"
            Duration = $duration
            ResultType = $callQueues.GetType().FullName
            Count = $callQueues.Count
            FirstQueueName = if ($callQueues.Count -gt 0) { $callQueues[0].Name } else { $null }
            AllQueueNames = $callQueues | ForEach-Object { $_.Name }
        } | ConvertTo-Json -Depth 3 | Out-File $DebugLogPath -Append
        
    } else {
        Write-Host "⚠️  No call queues returned" -ForegroundColor Yellow
        Write-Host "   - Result is null or empty"
        Write-Host "   - Result Type: $($callQueues.GetType().FullName)"
        
        # Log empty results
        @{
            Timestamp = Get-Date
            Action = "GET_CALLQUEUE_EMPTY"
            Duration = $duration
            ResultType = if ($callQueues) { $callQueues.GetType().FullName } else { "NULL" }
            IsNull = ($callQueues -eq $null)
            IsEmpty = if ($callQueues) { $callQueues.Count -eq 0 } else { $false }
        } | ConvertTo-Json -Depth 3 | Out-File $DebugLogPath -Append
    }

} catch {
    Write-Host "❌ Get-CsCallQueue failed: $_" -ForegroundColor Red
    Write-Host "❌ Exception Type: $($_.Exception.GetType().FullName)"
    Write-Host "❌ Stack Trace: $($_.Exception.StackTrace)"
    
    # Log error details
    @{
        Timestamp = Get-Date
        Action = "GET_CALLQUEUE_ERROR"
        Error = $_.Exception.Message
        ExceptionType = $_.Exception.GetType().FullName
        StackTrace = $_.Exception.StackTrace
    } | ConvertTo-Json -Depth 3 | Out-File $DebugLogPath -Append
}

# Additional diagnostic commands
Write-Host "🔍 Running additional diagnostics..." -ForegroundColor Yellow

try {
    # Test if we can create a call queue (similar to what works in API)
    Write-Host "🧪 Testing call queue creation capability..."
    
    # Check available cmdlets
    $teamsCmdlets = Get-Command -Module MicrosoftTeams | Where-Object { $_.Name -like "*CallQueue*" }
    Write-Host "Available CallQueue cmdlets: $($teamsCmdlets.Count)"
    $teamsCmdlets | ForEach-Object { Write-Host "   - $($_.Name)" }
    
    # Log available cmdlets
    @{
        Timestamp = Get-Date
        Action = "AVAILABLE_CMDLETS"
        CallQueueCmdlets = $teamsCmdlets | ForEach-Object { $_.Name }
    } | ConvertTo-Json -Depth 2 | Out-File $DebugLogPath -Append
    
    # Check Teams connection status
    $context = Get-CsTenant
    if ($context) {
        Write-Host "✅ Teams tenant context available"
        Write-Host "   - Tenant ID: $($context.TenantId)"
        Write-Host "   - Display Name: $($context.DisplayName)"
        
        @{
            Timestamp = Get-Date
            Action = "TENANT_CONTEXT"
            TenantId = $context.TenantId
            DisplayName = $context.DisplayName
        } | ConvertTo-Json -Depth 2 | Out-File $DebugLogPath -Append
    } else {
        Write-Host "❌ No Teams tenant context available"
        @{
            Timestamp = Get-Date
            Action = "NO_TENANT_CONTEXT"
        } | ConvertTo-Json -Depth 2 | Out-File $DebugLogPath -Append
    }

} catch {
    Write-Host "❌ Diagnostics failed: $_" -ForegroundColor Red
    @{
        Timestamp = Get-Date
        Action = "DIAGNOSTICS_ERROR"
        Error = $_.Exception.Message
    } | ConvertTo-Json -Depth 2 | Out-File $DebugLogPath -Append
}

# Clean up
try {
    Write-Host "🧹 Disconnecting from Teams..." -ForegroundColor Yellow
    Disconnect-MicrosoftTeams
    Write-Host "✅ Disconnected successfully" -ForegroundColor Green
    
    @{
        Timestamp = Get-Date
        Action = "TEAMS_DISCONNECT_SUCCESS"
    } | ConvertTo-Json -Depth 2 | Out-File $DebugLogPath -Append

} catch {
    Write-Host "⚠️  Disconnect warning: $_" -ForegroundColor Yellow
    @{
        Timestamp = Get-Date
        Action = "TEAMS_DISCONNECT_WARNING"
        Warning = $_.Exception.Message
    } | ConvertTo-Json -Depth 2 | Out-File $DebugLogPath -Append
}

Write-Host "=== Debug Session Complete ===" -ForegroundColor Cyan
Write-Host "📝 Full debug log available at: $DebugLogPath"

# Final log entry
@{
    Timestamp = Get-Date
    Action = "DEBUG_SESSION_COMPLETE"
    ScriptName = "test-callqueue-listing.ps1"
} | ConvertTo-Json -Depth 2 | Out-File $DebugLogPath -Append