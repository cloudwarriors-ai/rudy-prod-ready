# Debug user creation with detailed error handling
# Log all output for debugging
$ErrorActionPreference = "Stop"
$VerbosePreference = "Continue"

# Create log file
$logFile = "debug_user_creation.log"
"Starting debug user creation at $(Get-Date)" | Out-File -FilePath $logFile

# Create a timestamp for unique user names
$timestamp = Get-Date -Format "MMddHHmmss"

# Define user properties
$displayName = "Debug User $timestamp"
$userPrincipalName = "debuguser$timestamp@e7b105b2-720e-4b5b-9310-1a414c06356a.onmicrosoft.com"
$mailNickname = "debuguser$timestamp"
$password = "Test@P@ssw0rd123!"

try {
    # Source the connection script
    . ./connect.ps1 | Tee-Object -Append -FilePath $logFile

    "Authentication successful. Testing permissions..." | Tee-Object -Append -FilePath $logFile

    # Test basic permissions by listing users
    "Testing basic user listing permissions..." | Tee-Object -Append -FilePath $logFile
    $testUsers = Get-MgUser -Top 1
    if ($testUsers) {
        "SUCCESS: Can list users" | Tee-Object -Append -FilePath $logFile
    }
    else {
        "WARNING: Cannot list users" | Tee-Object -Append -FilePath $logFile
    }

    # Test creating a user with detailed error handling
    "Creating user with the following parameters:" | Tee-Object -Append -FilePath $logFile
    "DisplayName: $displayName" | Tee-Object -Append -FilePath $logFile
    "UserPrincipalName: $userPrincipalName" | Tee-Object -Append -FilePath $logFile
    "MailNickname: $mailNickname" | Tee-Object -Append -FilePath $logFile

    # Create password profile as a HashTable
    $PasswordProfile = @{
        Password = $password
        ForceChangePasswordNextSignIn = $true
    }

    "Attempting to create user..." | Tee-Object -Append -FilePath $logFile

    # Try to create the user with detailed error handling
    try {
        $newUser = New-MgUser `
            -DisplayName $displayName `
            -UserPrincipalName $userPrincipalName `
            -MailNickname $mailNickname `
            -PasswordProfile $PasswordProfile `
            -AccountEnabled:$true `
            -ErrorAction Stop

        # Log user creation results
        "SUCCESS: User created successfully:" | Tee-Object -Append -FilePath $logFile
        $newUser | Format-List Id, DisplayName, UserPrincipalName, AccountEnabled | Out-String | Tee-Object -Append -FilePath $logFile

        # Wait a moment for replication
        "Waiting 20 seconds for replication..." | Tee-Object -Append -FilePath $logFile
        Start-Sleep -Seconds 20

        # Verify by retrieving the user
        "Verifying user creation by retrieving user..." | Tee-Object -Append -FilePath $logFile
        $user = Get-MgUser -Filter "UserPrincipalName eq '$userPrincipalName'"
        if ($user) {
            "SUCCESS: User verified in Microsoft 365:" | Tee-Object -Append -FilePath $logFile
            $user | Format-List DisplayName, UserPrincipalName, Id, AccountEnabled | Out-String | Tee-Object -Append -FilePath $logFile
        }
        else {
            "WARNING: Could not verify user in Microsoft 365 after creation" | Tee-Object -Append -FilePath $logFile
        }
    }
    catch [System.Exception] {
        "ERROR: Failed to create user. Exception details:" | Tee-Object -Append -FilePath $logFile
        $_.Exception | Format-List | Out-String | Tee-Object -Append -FilePath $logFile
        $_.Exception.Message | Tee-Object -Append -FilePath $logFile

        # Check for specific error types
        if ($_.Exception.Message -like "*Forbidden*") {
            "PERMISSION ERROR: The application does not have permission to create users." | Tee-Object -Append -FilePath $logFile
        }
        elseif ($_.Exception.Message -like "*Unauthorized*") {
            "AUTHENTICATION ERROR: The application is not properly authenticated." | Tee-Object -Append -FilePath $logFile
        }
        elseif ($_.Exception.Message -like "*BadRequest*") {
            "BAD REQUEST ERROR: The request parameters are invalid." | Tee-Object -Append -FilePath $logFile
        }
        elseif ($_.Exception.Message -like "*already exists*") {
            "DUPLICATE ERROR: User with that name or UPN already exists." | Tee-Object -Append -FilePath $logFile
        }
        else {
            "UNKNOWN ERROR: An unexpected error occurred." | Tee-Object -Append -FilePath $logFile
        }
    }
}
catch {
    "CRITICAL ERROR: Failed to authenticate or initialize. Exception details:" | Tee-Object -Append -FilePath $logFile
    $_.Exception | Format-List | Out-String | Tee-Object -Append -FilePath $logFile
    $_.Exception.Message | Tee-Object -Append -FilePath $logFile
}

"Debug user creation test completed at $(Get-Date)" | Tee-Object -Append -FilePath $logFile