#### create a new user in MS365

New-MgUser -AccountEnabled $true `
  -DisplayName "John Doe" `
  -UserPrincipalName "john.doe@yourtenant.onmicrosoft.com" `
  -MailNickname "johndoe" `
  -PasswordProfile @{ Password = "TempP@ssw0rd!"; ForceChangePasswordNextSignIn = $true }

### Create a team with Microsoft Graph SDK

$team = @{
  template = "standard"
  displayName = "Support"
  description = "Support Team migrated from RingCentral"
  visibility = "private"
}
New-MgTeam -BodyParameter $team

### Create a team with Microsoft Teams PowerShell SDK

New-Team -DisplayName "Support" -Description "Support Team migrated from RingCentral" -Visibility Private


### Add user to team with Teams PowerShell SDK

Add-TeamUser -GroupId "Support" -User "john.doe@yourtenant.onmicrosoft.com"


### Assign phone number

Set-CsPhoneNumberAssignment -Identity "john.doe@yourtenant.onmicrosoft.com" -PhoneNumber +15555550123 -PhoneNumberType DirectRouting



