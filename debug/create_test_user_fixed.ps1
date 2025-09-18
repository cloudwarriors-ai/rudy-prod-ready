# Test user creation in Microsoft 365 with fixed parameters
# Log all output for debugging
$ErrorActionPreference = "Continue"
$VerbosePreference = "Continue"

# Create log file
$logFile = "user_creation_fixed.log"
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
    
    # Create password profile as a proper HashTable
    $PasswordProfile = @{
        Password = $password
        ForceChangePasswordNextSignIn = $true
    }
    
    # Create the user with proper parameter format
    try {
        "Executing New-MgUser command with parameters..." | Tee-Object -Append -FilePath $logFile
        
        # Show the command we're going to execute
        $command = "New-MgUser -DisplayName '$displayName' -UserPrincipalName '$userPrincipalName' -MailNickname '$mailNickname' -PasswordProfile `$PasswordProfile -AccountEnabled:`$true"
        "Command: $command" | Tee-Object -Append -FilePath $logFile
        
        # Execute the command with proper parameter format
        $newUser = New-MgUser `
            -DisplayName $displayName `
            -UserPrincipalName $userPrincipalName `
            -MailNickname $mailNickname `
            -PasswordProfile $PasswordProfile `
            -AccountEnabled:$true
            
        # Log user creation results
        "User created successfully:" | Tee-Object -Append -FilePath $logFile
        $newUser | Format-List Id, DisplayName, UserPrincipalName | Out-String | Tee-Object -Append -FilePath $logFile
        
        # Verify by retrieving the user
        "Verifying user creation by retrieving user..." | Tee-Object -Append -FilePath $logFile
        $user = Get-MgUser -Filter "UserPrincipalName eq '$userPrincipalName'"
        if ($user) {
            "User verified in Microsoft 365:" | Tee-Object -Append -FilePath $logFile
            $user | Format-List DisplayName, UserPrincipalName, Id | Out-String | Tee-Object -Append -FilePath $logFile
        }
        else {
            "Warning: Could not verify user in Microsoft 365 after creation" | Tee-Object -Append -FilePath $logFile
        }
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