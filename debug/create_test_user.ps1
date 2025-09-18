# Test user creation in Microsoft 365
# Log all output for debugging
$ErrorActionPreference = "Continue"
$VerbosePreference = "Continue"

# Create log file
$logFile = "user_creation_test.log"
"Starting user creation test at $(Get-Date)" | Out-File -FilePath $logFile

# Create a timestamp for unique user names
$timestamp = Get-Date -Format "MMddHHmmss"

# Define user properties
$displayName = "Test User $timestamp"
$userPrincipalName = "testuser$timestamp@cloudwarriors.onmicrosoft.com"
$mailNickname = "testuser$timestamp"
$password = "Test@P@ssw0rd123!"

try {
    # Source the connection script
    . ./connect.ps1 | Tee-Object -Append -FilePath $logFile
    
    "Authentication successful. Creating test user..." | Tee-Object -Append -FilePath $logFile
    
    # Log user creation parameters
    "Creating user with the following parameters:" | Tee-Object -Append -FilePath $logFile
    "DisplayName: $displayName" | Tee-Object -Append -FilePath $logFile
    "UserPrincipalName: $userPrincipalName" | Tee-Object -Append -FilePath $logFile
    "MailNickname: $mailNickname" | Tee-Object -Append -FilePath $logFile
    
    # Create password profile
    $passwordProfile = @{
        Password = $password
        ForceChangePasswordNextSignIn = $true
    }
    
    # Create the user
    try {
        $newUser = New-MgUser `
            -DisplayName $displayName `
            -UserPrincipalName $userPrincipalName `
            -MailNickname $mailNickname `
            -PasswordProfile $passwordProfile `
            -AccountEnabled $true
            
        # Log user creation results
        "User created successfully:" | Tee-Object -Append -FilePath $logFile
        $newUser | Format-List Id, DisplayName, UserPrincipalName | Out-String | Tee-Object -Append -FilePath $logFile
    }
    catch {
        "Error creating user: $_" | Tee-Object -Append -FilePath $logFile
        
        # Check for specific error messages
        if ($_.Exception.Message -like "*already exists*") {
            "User with that name or UPN already exists. Please try a different name." | Tee-Object -Append -FilePath $logFile
        }
        elseif ($_.Exception.Message -like "*permission*" -or $_.Exception.Message -like "*unauthorized*") {
            "Permission error. Please check that your credentials have user creation rights." | Tee-Object -Append -FilePath $logFile
        }
    }
}
catch {
    "Authentication error: $_" | Tee-Object -Append -FilePath $logFile
}

"User creation test completed at $(Get-Date)" | Tee-Object -Append -FilePath $logFile