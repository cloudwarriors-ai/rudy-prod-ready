# Test user creation using AzureAD module
# Log all output for debugging
$ErrorActionPreference = "Continue"
$VerbosePreference = "Continue"

# Create log file
$logFile = "azuread_user_creation.log"
"Starting AzureAD user creation at $(Get-Date)" | Out-File -FilePath $logFile

# Create a timestamp for unique user names
$timestamp = Get-Date -Format "MMddHHmmss"

# Define user properties
$displayName = "Test User $timestamp"
$userPrincipalName = "testuser$timestamp@e7b105b2-720e-4b5b-9310-1a414c06356a.onmicrosoft.com"
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

    # Create password profile as a SecureString
    $securePassword = ConvertTo-SecureString $password -AsPlainText -Force

    # Try using AzureAD module if available
    "Checking if AzureAD module is available..." | Tee-Object -Append -FilePath $logFile
    if (Get-Module -ListAvailable -Name AzureAD) {
        "AzureAD module found. Importing..." | Tee-Object -Append -FilePath $logFile
        Import-Module AzureAD | Tee-Object -Append -FilePath $logFile

        # Connect to AzureAD
        "Connecting to AzureAD..." | Tee-Object -Append -FilePath $logFile
        Connect-AzureAD | Tee-Object -Append -FilePath $logFile

        # Create the user using AzureAD
        "Executing New-AzureADUser command..." | Tee-Object -Append -FilePath $logFile

        $newUser = New-AzureADUser `
            -DisplayName $displayName `
            -UserPrincipalName $userPrincipalName `
            -MailNickName $mailNickname `
            -PasswordProfile $securePassword `
            -AccountEnabled $true

        # Log user creation results
        "User created successfully with AzureAD:" | Tee-Object -Append -FilePath $logFile
        $newUser | Format-List ObjectId, DisplayName, UserPrincipalName, AccountEnabled | Out-String | Tee-Object -Append -FilePath $logFile

        # Wait a moment for replication
        "Waiting 15 seconds for replication..." | Tee-Object -Append -FilePath $logFile
        Start-Sleep -Seconds 15

        # Verify by retrieving the user
        "Verifying user creation by retrieving user..." | Tee-Object -Append -FilePath $logFile
        $user = Get-AzureADUser -ObjectId $userPrincipalName
        if ($user) {
            "SUCCESS: User verified in AzureAD:" | Tee-Object -Append -FilePath $logFile
            $user | Format-List DisplayName, UserPrincipalName, ObjectId, AccountEnabled | Out-String | Tee-Object -Append -FilePath $logFile
        }
        else {
            "WARNING: Could not verify user in AzureAD after creation" | Tee-Object -Append -FilePath $logFile
        }
    }
    else {
        "AzureAD module not found. Trying Microsoft Graph again..." | Tee-Object -Append -FilePath $logFile

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
        "Waiting 15 seconds for replication..." | Tee-Object -Append -FilePath $logFile
        Start-Sleep -Seconds 15

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

"AzureAD user creation test completed at $(Get-Date)" | Tee-Object -Append -FilePath $logFile