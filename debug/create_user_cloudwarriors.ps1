# Test user creation using cloudwarriors.onmicrosoft.com domain
# Log all output for debugging
$ErrorActionPreference = "Continue"
$VerbosePreference = "Continue"

# Create log file
$logFile = "cloudwarriors_user_creation.log"
"Starting user creation with cloudwarriors domain at $(Get-Date)" | Out-File -FilePath $logFile

# Create a timestamp for unique user names
$timestamp = Get-Date -Format "MMddHHmmss"

# Define user properties using cloudwarriors.onmicrosoft.com domain
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

    # Create password profile as a HashTable
    $PasswordProfile = @{
        Password = $password
        ForceChangePasswordNextSignIn = $true
    }

    # Create the user using Microsoft Graph
    "Executing New-MgUser command..." | Tee-Object -Append -FilePath $logFile

    $newUser = New-MgUser `
        -DisplayName $displayName `
        -UserPrincipalName $userPrincipalName `
        -MailNickname $mailNickname `
        -PasswordProfile $PasswordProfile `
        -AccountEnabled:$true

    # Log user creation results
    "User created successfully:" | Tee-Object -Append -FilePath $logFile
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
catch {
    "Error creating user: $_" | Tee-Object -Append -FilePath $logFile

    # Check for specific error messages
    if ($_.Exception.Message -like "*already exists*") {
        "User with that name or UPN already exists. Please try a different name." | Tee-Object -Append -FilePath $logFile
    }
    elseif ($_.Exception.Message -like "*permission*" -or $_.Exception.Message -like "*unauthorized*") {
        "Permission error. Please check that your credentials have user creation rights." | Tee-Object -Append -FilePath $logFile
    }
    elseif ($_.Exception.Message -like "*domain*" -or $_.Exception.Message -like "*tenant*") {
        "Domain or tenant error. Please check the domain name." | Tee-Object -Append -FilePath $logFile
    }
}

"User creation test with cloudwarriors domain completed at $(Get-Date)" | Tee-Object -Append -FilePath $logFile