# Microsoft Teams Auto Attendant - Complete Fields Reference

Generated on: September 25, 2025  
Source: Microsoft Teams PowerShell Module  
Tenant: Cloud Warriors (e7b105b2-720e-4b5b-9310-1a414c06356a)

## Overview

This document provides a comprehensive reference for all available fields and properties of Microsoft Teams Auto Attendants, extracted directly from the Teams API. Auto Attendants are key elements in the Office 365 Phone System that allow callers to reach specific people through directory lookup or route calls to operators, users, other Auto Attendants, or Call Queues.

---

## Main Auto Attendant Object Properties

### Core Properties

| Property | Type | Description | Required | Example |
|----------|------|-------------|----------|---------|
| `Id` | `string` | Unique identifier for the Auto Attendant | Yes | `0890b2cb-25d1-4bad-aa13-b0afb5fe1102` |
| `Identity` | `string` | Identity of the Auto Attendant (same as Id) | Yes | `0890b2cb-25d1-4bad-aa13-b0afb5fe1102` |
| `Name` | `string` | Friendly name for the Auto Attendant | Yes | `APITestAA-20250918-110625` |
| `TenantId` | `guid` | Tenant identifier | No | `e7b105b2-720e-4b5b-9310-1a414c06356a` |

### Language and Voice Settings

| Property | Type | Description | Required | Example |
|----------|------|-------------|----------|---------|
| `LanguageId` | `string` | Language for text-to-speech prompts | Yes | `en-US` |
| `VoiceId` | `string` | Voice for text-to-speech prompts | No | `Male`, `Female` |
| `VoiceResponseEnabled` | `System.Nullable[bool]` | Enable voice responses | No | `false` |

### Time and Location

| Property | Type | Description | Required | Example |
|----------|------|-------------|----------|---------|
| `TimeZoneId` | `string` | Time zone for schedule evaluation | Yes | `UTC` |

### User Access and Authorization

| Property | Type | Description | Required | Example |
|----------|------|-------------|----------|---------|
| `AuthorizedUsers` | `guid[]` | Users authorized to make changes | No | Array of GUIDs |
| `HideAuthorizedUsers` | `guid[]` | Users to hide from directory lookup | No | Array of GUIDs |
| `UserNameExtension` | `string` | How to extend usernames in dial search | No | `None`, `Office`, `Department` |

### Advanced Features

| Property | Type | Description | Required | Example |
|----------|------|-------------|----------|---------|
| `MainlineAttendantEnabled` | `System.Nullable[bool]` | Enable Mainline Attendant features | No | `false` |
| `IsInvokedByTenantAdmin` | `bool` | Indicates if invoked by tenant admin | No | `false` |

### Call Flow and Routing

| Property | Type | Description | Required | Example |
|----------|------|-------------|----------|---------|
| `DefaultCallFlow` | `CallFlow` | Primary call flow when no schedule is active | Yes | CallFlow object |
| `CallFlows` | `CallFlow[]` | Additional call flows for different schedules | No | Array of CallFlow objects |
| `Operator` | `CallableEntity` | Operator for call transfers | No | CallableEntity object |

### Directory and Lookup

| Property | Type | Description | Required | Example |
|----------|------|-------------|----------|---------|
| `DirectoryLookupScope` | `DirectoryLookupScope` | Directory lookup configuration | No | DirectoryLookupScope object |
| `DialByNameResourceId` | `string` | Resource ID for dial-by-name feature | No | Generated automatically |

### Scheduling and Associations

| Property | Type | Description | Required | Example |
|----------|------|-------------|----------|---------|
| `Schedules` | `Schedule[]` | Schedules for call handling | No | Array of Schedule objects |
| `CallHandlingAssociations` | `CallHandlingAssociation[]` | Associates schedules with call flows | No | Array of associations |

### System and Status

| Property | Type | Description | Required | Example |
|----------|------|-------------|----------|---------|
| `Status` | `StatusRecord[]` | Status information | No | Array of status records |
| `ApplicationInstances` | `string[]` | Associated application instances (resource accounts) | No | Array of instance IDs |

---

## Call Flow Object Properties

The `DefaultCallFlow` and `CallFlows` contain CallFlow objects with these properties:

| Property | Type | Description | Required | Example |
|----------|------|-------------|----------|---------|
| `Id` | `string` | Unique identifier for the call flow | Yes | `23e55761-6b06-4a74-83eb-76238ee47f9d` |
| `Name` | `string` | Name of the call flow | Yes | `DefaultFlow` |
| `Greetings` | `Prompt[]` | Welcome messages played to callers | No | Array of Prompt objects |
| `Menu` | `Menu` | Menu configuration for the call flow | Yes | Menu object |
| `IsInvokedByTenantAdmin` | `bool` | Admin invocation flag | No | `false` |
| `ForceListenMenuEnabled` | `bool` | Force callers to listen to menu | No | `false` |

---

## Menu Object Properties

The `Menu` object within CallFlow contains:

| Property | Type | Description | Required | Example |
|----------|------|-------------|----------|---------|
| `Name` | `string` | Name of the menu | Yes | `MainMenu` |
| `Prompts` | `Prompt[]` | Menu prompts played to callers | Yes | Array of Prompt objects |
| `MenuOptions` | `MenuOption[]` | Available menu options | Yes | Array of MenuOption objects |
| `DialByNameEnabled` | `bool` | Enable dial-by-name feature | No | `false` |
| `DirectorySearchMethod` | `DirectorySearchMethod` | Method for directory search | No | `None`, `ByName`, `ByExtension` |
| `IsInvokedByTenantAdmin` | `bool` | Admin invocation flag | No | `false` |

---

## Prompt Object Properties

Prompts are used for greetings and menu messages:

| Property | Type | Description | Required | Example |
|----------|------|-------------|----------|---------|
| `ActiveType` | `PromptType` | Type of prompt active | Yes | `TextToSpeech`, `AudioFile`, `None` |
| `TextToSpeechPrompt` | `string` | Text to be read aloud | Conditional | `"Welcome to our company"` |
| `AudioFilePrompt` | `AudioFile` | Audio file to play | Conditional | AudioFile object |

**Note:** Either `TextToSpeechPrompt` or `AudioFilePrompt` is required based on `ActiveType`.

---

## Menu Option Object Properties

Each menu option represents an action callers can take:

| Property | Type | Description | Required | Example |
|----------|------|-------------|----------|---------|
| `Action` | `ActionType` | Action to perform | Yes | See Action Types below |
| `DtmfResponse` | `DtmfTone` | Keypad response | Yes | `Tone0` to `Tone9`, `ToneStar`, `TonePound`, `Automatic` |
| `VoiceResponses` | `string[]` | Voice responses for the option | No | Array of voice commands |
| `CallTarget` | `CallableEntity` | Target for call transfer | Conditional | CallableEntity object |
| `Prompt` | `Prompt` | Prompt to play for this option | Conditional | Prompt object |
| `Description` | `string` | Description/keywords (Mainline only) | No | Up to 500 characters |
| `MainlineAttendantTarget` | `string` | Mainline Attendant target ID | No | Target identifier |

### Action Types

| Action | Description | Requires CallTarget | Requires Prompt |
|--------|-------------|-------------------|-----------------|
| `TransferCallToTarget` | Transfer call to specified target | Yes | No |
| `TransferCallToOperator` | Transfer call to operator | No | No |
| `DisconnectCall` | Disconnect the call | No | No |
| `Announcement` | Play announcement and return to menu | No | Yes |

---

## Callable Entity Object Properties

Used for call targets (users, queues, external numbers):

| Property | Type | Description | Required | Example |
|----------|------|-------------|----------|---------|
| `Identity` | `string` | ID or TEL URI of the target | Yes | Object ID or `tel:+1234567890` |
| `Type` | `CallableEntityType` | Type of callable entity | Yes | See Entity Types below |
| `CallPriority` | `Int16` | Call priority (1-5) | No | `3` (Normal) |
| `EnableTranscription` | `bool` | Enable voicemail transcription | No | `false` |
| `EnableSharedVoicemailSystemPromptSuppression` | `bool` | Suppress voicemail system prompt | No | `false` |

### Callable Entity Types

| Type | Description | Identity Format |
|------|-------------|-----------------|
| `User` | Individual user | User Object ID |
| `ApplicationEndpoint` | Resource Account | Resource Account Object ID |
| `ConfigurationEndpoint` | Auto Attendant or Call Queue | AA/CQ Object ID |
| `ExternalPstn` | External phone number | `tel:+1234567890` |
| `SharedVoicemail` | Shared voicemail | User/Group Object ID |

---

## Directory Lookup Scope Properties

Controls who can be reached through directory lookup:

| Property | Type | Description | Required | Example |
|----------|------|-------------|----------|---------|
| `InclusionScope` | `DialScope` | Users included in directory lookup | No | DialScope object |
| `ExclusionScope` | `DialScope` | Users excluded from directory lookup | No | DialScope object |
| `IsInvokedByTenantAdmin` | `bool` | Admin invocation flag | No | `false` |

**Note:** If a user is in both inclusion and exclusion scopes, exclusion takes priority.

---

## Supported Languages

Auto Attendants support 54 languages. Key examples include:

| Language Code | Display Name |
|---------------|--------------|
| `en-US` | English (United States) |
| `en-GB` | English (United Kingdom) |
| `es-ES` | Spanish (Spain) |
| `fr-FR` | French (France) |
| `de-DE` | German (Germany) |
| `it-IT` | Italian (Italy) |
| `ja-JP` | Japanese (Japan) |
| `zh-CN` | Chinese (Simplified, PRC) |

*For complete list, use: `Get-CsAutoAttendantSupportedLanguage`*

---

## Supported Time Zones

Auto Attendants support 108 time zones. Key examples include:

| Time Zone ID | Display Name |
|--------------|--------------|
| `UTC` | Coordinated Universal Time |
| `Eastern Standard Time` | Eastern Time (US & Canada) |
| `Pacific Standard Time` | Pacific Time (US & Canada) |
| `Central Standard Time` | Central Time (US & Canada) |
| `GMT Standard Time` | Dublin, Edinburgh, Lisbon, London |

*For complete list, use: `Get-CsAutoAttendantSupportedTimeZone`*

---

## DTMF Tone Options

| DTMF Tone | Description |
|-----------|-------------|
| `Tone0` - `Tone9` | Number keys 0-9 |
| `ToneStar` | Star (*) key |
| `TonePound` | Pound (#) key |
| `Automatic` | Action executes without user input |

---

## Voice Response Settings

| Voice ID | Description |
|----------|-------------|
| `Male` | Male voice for TTS |
| `Female` | Female voice for TTS |

**Note:** Available voices depend on the selected language. Use `Get-CsAutoAttendantSupportedLanguage` to see voice options for specific languages.

---

## PowerShell Creation Cmdlets

### Primary Cmdlet
- `New-CsAutoAttendant` - Creates the main Auto Attendant

### Supporting Cmdlets
- `New-CsAutoAttendantCallFlow` - Creates call flows
- `New-CsAutoAttendantMenu` - Creates menu structures
- `New-CsAutoAttendantMenuOption` - Creates menu options
- `New-CsAutoAttendantPrompt` - Creates prompts (greetings/announcements)
- `New-CsAutoAttendantCallableEntity` - Creates call targets
- `New-CsAutoAttendantDialScope` - Creates directory lookup scopes
- `New-CsAutoAttendantCallHandlingAssociation` - Associates schedules with call flows
- `New-CsOnlineSchedule` - Creates schedules
- `New-CsOnlineTimeRange` - Creates time ranges for schedules

---

## Important Notes

### Teams Admin Center Limitations
The following parameters are only available in PowerShell and will be removed if the Auto Attendant is saved through Teams Admin Center:
- `HideAuthorizedUsers`
- `UserNameExtension`
- `EnableMainlineAttendant`
- Menu option `Description`
- Menu option `MainlineAttendantTarget`
- Callable entity `CallPriority`

### Private Preview Features
Some features are only available to Voice Applications private preview customers:
- `EnableMainlineAttendant`
- `MainlineAttendantTarget`
- Enhanced `Description` fields

### Nesting Limitations
When using `ConfigurationEndpoint` type for nesting Auto Attendants or Call Queues:
- Not supported for Authorized users in Queues App
- Call priorities not supported for Authorized users
- Authorized users cannot edit nested configurations without resource accounts

---

## Example Implementation

```powershell
# Create a basic Auto Attendant
$greeting = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Welcome to Contoso!"
$menuOption = New-CsAutoAttendantMenuOption -Action TransferCallToOperator -DtmfResponse Tone0
$menu = New-CsAutoAttendantMenu -Name "Main Menu" -Prompts @($greeting) -MenuOptions @($menuOption)
$callFlow = New-CsAutoAttendantCallFlow -Name "Default Flow" -Greetings @($greeting) -Menu $menu

$autoAttendant = New-CsAutoAttendant -Name "Main Auto Attendant" -DefaultCallFlow $callFlow -LanguageId "en-US" -TimeZoneId "UTC" -EnableVoiceResponse
```

---

*This documentation was generated from live Microsoft Teams API data on September 25, 2025.*