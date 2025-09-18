# Verify if a user exists in Microsoft 365
# Log all output for debugging
$ErrorActionPreference = "Continue"
$VerbosePreference = "Continue"

# Create log file
$logFile = "verify_user.log"
"Starting user verification at $(Get-Date)" | Out-File -FilePath $logFile

# User to verify
$userPrincipalName = "testuser0917163540@cloudwarriors.onmicrosoft.com"

try {
    # Source the connection script
    . ./connect.ps1 | Tee-Object -Append -FilePath $logFile
    
    "Authentication successful. Verifying user..." | Tee-Object -Append -FilePath $logFile
    
    # Try to get users with names containing "Test User"
    "Searching for users with 'Test User' in their display name..." | Tee-Object -Append -FilePath $logFile
    $users = Get-MgUser -Filter "startswith(DisplayName, 'Test User')" -Top 10
    
    if ($users -and $users.Count -gt 0) {
        "Found users matching 'Test User':" | Tee-Object -Append -FilePath $logFile
        $users | Format-Table DisplayName, UserPrincipalName, Id | Out-String | Tee-Object -Append -FilePath $logFile
    }
    else {
        "No users found with display name containing 'Test User'" | Tee-Object -Append -FilePath $logFile
    }
    
    # Try to directly get the specific user
    "Searching for specific user: $userPrincipalName" | Tee-Object -Append -FilePath $logFile
    try {
        $specificUser = Get-MgUser -Filter "UserPrincipalName eq '$userPrincipalName'"
        
        if ($specificUser) {
            "Found specific user:" | Tee-Object -Append -FilePath $logFile
            $specificUser | Format-List DisplayName, UserPrincipalName, Id | Out-String | Tee-Object -Append -FilePath $logFile
        }
        else {
            "Specific user not found: $userPrincipalName" | Tee-Object -Append -FilePath $logFile
        }
    }
    catch {
        "Error searching for specific user: $_" | Tee-Object -Append -FilePath $logFile
    }
    
    # List all users in the tenant for reference
    "Listing some recent users in the tenant..." | Tee-Object -Append -FilePath $logFile
    $allUsers = Get-MgUser -Top 10
    $allUsers | Format-Table DisplayName, UserPrincipalName | Out-String | Tee-Object -Append -FilePath $logFile
}
catch {
    "Authentication error: $_" | Tee-Object -Append -FilePath $logFile
}

"User verification completed at $(Get-Date)" | Tee-Object -Append -FilePath $logFile