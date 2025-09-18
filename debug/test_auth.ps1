# Test authentication and connection to Microsoft 365
# Log all output for debugging
$ErrorActionPreference = "Continue"
$VerbosePreference = "Continue"

# Create log file
$logFile = "auth_test.log"
"Starting authentication test at $(Get-Date)" | Out-File -FilePath $logFile

try {
    # Source the connection script
    . ./connect.ps1 | Tee-Object -Append -FilePath $logFile
    
    "Authentication successful. Testing connection..." | Tee-Object -Append -FilePath $logFile
    
    # Test connection by listing some basic info
    "Getting Teams ACS Federation Configuration:" | Tee-Object -Append -FilePath $logFile
    Get-CsTeamsAcsFederationConfiguration | Format-List | Out-String | Tee-Object -Append -FilePath $logFile
    
    # Check if we can access user management
    "Testing access to user management..." | Tee-Object -Append -FilePath $logFile
    try {
        # Try to get a list of users to test if our permissions are correct
        Get-MgUser -Top 5 | Format-Table DisplayName, UserPrincipalName | Out-String | Tee-Object -Append -FilePath $logFile
        "Successfully accessed user data" | Tee-Object -Append -FilePath $logFile
    }
    catch {
        "Error accessing user data: $_" | Tee-Object -Append -FilePath $logFile
    }
}
catch {
    "Authentication error: $_" | Tee-Object -Append -FilePath $logFile
}

"Authentication test completed at $(Get-Date)" | Tee-Object -Append -FilePath $logFile