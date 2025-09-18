# Teams SDK API Endpoints

This FastAPI server provides endpoints for managing Microsoft Teams users and teams through PowerShell automation.

## Authentication

### POST /auth/connect
**Description:** Create an authenticated PowerShell session for Microsoft Graph/Teams operations.

**Response:**
```json
{
  "message": "Authenticated",
  "session_id": "uuid-string"
}
```

**Time:** ~1-2 seconds

### GET /auth/status?session_id={session_id}
**Description:** Check authentication status of a session.

**Response:**
```json
{
  "status": "authenticated", 
  "details": "Microsoft Graph connection active"
}
```

### POST /auth/disconnect?session_id={session_id}
**Description:** Disconnect and clean up a PowerShell session.

## User Management

### POST /users/direct (Create User - Direct)
**Description:** Create user using direct PowerShell execution (no session required).

**Request Body:**
- **accountEnabled**: bool (required)
- **displayName**: str (required) 
- **userPrincipalName**: str (required) - e.g., "user@domain.com"
- **mailNickname**: str (required) - e.g., "user"
- **password**: str (required) - Must meet complexity requirements
- **forceChangePassword**: bool (required)

**Example Request:**
```json
{
  "accountEnabled": true,
  "displayName": "Test User",
  "userPrincipalName": "testuser@cloudwarriors.onmicrosoft.com",
  "mailNickname": "testuser", 
  "password": "TempP@ssw0rd123!",
  "forceChangePassword": true
}
```

**Response:**
```json
{
  "message": "User created and verified successfully",
  "userPrincipalName": "testuser@cloudwarriors.onmicrosoft.com",
  "displayName": "Test User",
  "userId": "uuid-string",
  "status": "verified"
}
```

**Time:** ~8-9 seconds (includes authentication, creation, verification)

### POST /users/session?session_id={session_id} (Create User - Session)
**Description:** Create user using existing authenticated session (faster).

**Request Body:** Same as `/users/direct`

**Response:** Same as `/users/direct`

**Time:** ~3-4 seconds (reuses authenticated session)

### POST /users?session_id={session_id} (Legacy)
**Description:** Legacy endpoint, redirects to session-based approach.

## Team Management

### POST /teams/direct (Create Team - Direct)
**Description:** Create team using direct PowerShell execution with Microsoft Graph API (no session required).

**Request Body:**
- **displayName**: str (required) - Team display name
- **description**: str (required) - Team description
- **mailNickname**: str (required) - Unique mail nickname (no spaces/special chars)
- **visibility**: str (default "Private") - "Private" or "Public"

**Example Request:**
```json
{
  "displayName": "Support Team",
  "description": "Customer support team",
  "mailNickname": "supportteam",
  "visibility": "Private"
}
```

**Response:**
```json
{
  "message": "Team created successfully",
  "displayName": "Support Team",
  "mailNickname": "supportteam",
  "teamId": "uuid-string",
  "status": "created"
}
```

**Implementation Notes:**
- Uses Microsoft Graph API `/teams` endpoint
- Automatically includes standard template and team owner
- Creates fully functional Teams that appear in Microsoft Teams interface
- **Time:** ~3-4 seconds

### POST /teams?session_id={session_id} (Create Team - Session)
**Description:** Create team using existing authenticated session (recommended for multiple operations).

**Request Body:** Same as `/teams/direct`

**Response:** Same as `/teams/direct`

**Implementation Notes:** Same as direct endpoint but reuses authenticated PowerShell session
**Time:** ~2-3 seconds (faster due to session reuse)

## Team Membership

### POST /teams/{team_id}/members/direct (Add User to Team - Direct)
**Description:** Add user to team using direct PowerShell execution with Microsoft Graph API.

**Path Parameters:**
- **team_id**: str - Team/Group ID from team creation

**Request Body:**
- **user**: str (required) - User email or UPN (e.g., "user@domain.com")

**Example Request:**
```json
{
  "user": "testuser@cloudwarriors.onmicrosoft.com"
}
```

**Response:**
```json
{
  "message": "User added to team successfully",
  "user": "testuser@cloudwarriors.onmicrosoft.com",
  "teamId": "uuid-string",
  "status": "added"
}
```

**Implementation Notes:**
- Uses Microsoft Graph API to add user as team member
- User must exist before being added to team
- **Time:** ~2-3 seconds

### POST /teams/{team_id}/users?session_id={session_id} (Add User to Team - Session)
**Description:** Add user to team using existing authenticated session (recommended for bulk operations).

**Parameters:** Same as direct endpoint

**Response:** Same as direct endpoint

**Implementation Notes:** Same as direct endpoint but reuses authenticated PowerShell session
**Time:** ~1-2 seconds (faster due to session reuse)

## Call Queue Management

### POST /callqueues/direct (Create Call Queue - Direct)
**Description:** Create Microsoft Teams call queue using direct PowerShell execution (no session required). Compatible with Azure Communication Services calling.

**Request Body:**
- **name**: str (required) - Call queue display name
- **languageId**: str (default "en-US") - Language for prompts
- **routingMethod**: str (default "Attendant") - "Attendant", "Serial", "RoundRobin", "LongestIdle"  
- **agents**: list[str] (default []) - List of user email addresses to add as agents
- **welcomeTextToSpeechPrompt**: str (default "") - Welcome message for callers
- **overflowThreshold**: int (default 20) - Maximum calls in queue before overflow
- **overflowAction**: str (default "Disconnect") - "Disconnect", "Forward", "Voicemail", "SharedVoicemail"
- **timeoutThreshold**: int (default 1200) - Seconds before timeout (20 minutes)
- **timeoutAction**: str (default "Disconnect") - Same options as overflow
- **agentAlertTime**: int (default 30) - Seconds to alert agent before moving to next
- **conferenceMode**: bool (default true) - Enable modern call handling
- **useDefaultMusicOnHold**: bool (default true) - Use system default hold music

**Example Request:**
```json
{
  "name": "Support Call Queue",
  "languageId": "en-US",
  "routingMethod": "RoundRobin", 
  "agents": [],
  "welcomeTextToSpeechPrompt": "Welcome to our support line",
  "overflowThreshold": 25,
  "overflowAction": "Disconnect",
  "timeoutThreshold": 1800,
  "timeoutAction": "Disconnect",
  "agentAlertTime": 20,
  "conferenceMode": true,
  "useDefaultMusicOnHold": true
}
```

**Response:**
```json
{
  "message": "Call queue created successfully",
  "name": "Support Call Queue",
  "identity": "uuid-string",
  "routingMethod": "RoundRobin", 
  "resourceAccountId": "uuid-string",
  "objectId": "28:orgid:uuid-string",
  "status": "created"
}
```

**Time:** ~4-6 seconds
**Note:** The `objectId` field is formatted for Azure Communication Services calling (`28:orgid:{guid}`)

### POST /callqueues?session_id={session_id} (Create Call Queue - Session)
**Description:** Create call queue using existing authenticated session (faster for multiple operations).

**Request/Response:** Same as direct endpoint
**Time:** ~2-3 seconds (reuses session)

### POST /callqueues/{queue_identity}/agents?session_id={session_id} (Add Agent to Call Queue)
**Description:** Add a user as an agent to an existing call queue.

**Path Parameters:**
- **queue_identity**: str - Call queue identity/ID from creation

**Request Body:**
- **userPrincipalName**: str (required) - User email to add as agent

**Example Request:**
```json
{
  "userPrincipalName": "support@company.com"
}
```

**Response:**
```json
{
  "message": "User added to call queue successfully",
  "userPrincipalName": "support@company.com", 
  "callQueueIdentity": "uuid-string",
  "status": "added"
}
```

**Time:** ~2-3 seconds

### POST /callqueues/objectid?session_id={session_id} (Get Object ID for Calling)
**Description:** Get the Object ID needed for Azure Communication Services calling from a resource account email.

**Request Body:**
- **resourceAccountEmail**: str (required) - Resource account email associated with call queue

**Example Request:**
```json
{
  "resourceAccountEmail": "callqueue@company.onmicrosoft.com"
}
```

**Response:**
```json
{
  "message": "Object ID found successfully",
  "resourceAccountEmail": "callqueue@company.onmicrosoft.com",
  "objectId": "uuid-string",
  "displayName": "Call Queue Display Name", 
  "callingObjectId": "28:orgid:uuid-string",
  "status": "found"
}
```

**Usage:** Use the `callingObjectId` value with Azure Communication Services calling SDK:
```javascript
const callQueueId = "28:orgid:uuid-from-response";
call = callAgent.startCall([{ teamsAppId: callQueueId, cloud: "public" }], options);
```

### GET /callqueues?session_id={session_id} (List Call Queues)
**Description:** List all call queues in the tenant with their configuration details.

**Response:**
```json
{
  "message": "Found 3 call queues",
  "queues": [
    {
      "identity": "uuid-string",
      "name": "Support Queue",
      "routingmethod": "RoundRobin",
      "agentalerttime": "20",
      "overflowthreshold": "25", 
      "timeoutthreshold": "1800"
    }
  ],
  "count": 3
}
```

## Auto Attendant Management (IVR)

### POST /autoattendants/direct (Create Auto Attendant - Direct)
**Description:** Create Microsoft Teams Auto Attendant (IVR system) using direct PowerShell execution (no session required). Includes automatic resource account verification for call queue targets.

**Request Body:**
- **name**: str (required) - Auto Attendant display name
- **languageId**: str (default "en-US") - Language for voice prompts
- **greetingPrompt**: str (required) - Welcome message for callers
- **menuOptions**: List[MenuOption] (required) - Array of menu options
- **enableVoiceResponse**: bool (default true) - Enable voice recognition
- **timeoutActionTargetType**: str (default "Disconnect") - Action when no input
- **timeoutActionTargetId**: str (default "") - Target ID for timeout action
- **timeoutPrompt**: str (default "") - Timeout message

**MenuOption Structure:**
- **dtmfResponse**: str (required) - DTMF key ("1", "2", etc.)
- **prompt**: str (required) - Spoken description of option
- **callTargetType**: str (required) - "CallQueue", "User", or "ExternalPstn"
- **callTargetId**: str (required) - Target identifier (queue ID, user ID, etc.)

**Example Request:**
```json
{
  "name": "Main Auto Attendant",
  "languageId": "en-US",
  "greetingPrompt": "Welcome to Acme Corporation",
  "menuOptions": [
    {
      "dtmfResponse": "1",
      "prompt": "Sales Department",
      "callTargetType": "CallQueue",
      "callTargetId": "sales-queue-identity-guid"
    },
    {
      "dtmfResponse": "2",
      "prompt": "Technical Support",
      "callTargetType": "CallQueue",
      "callTargetId": "support-queue-identity-guid"
    }
  ],
  "enableVoiceResponse": true,
  "timeoutPrompt": "We did not receive a response. Please try again."
}
```

**Response (Success):**
```json
{
  "message": "Auto Attendant created successfully",
  "name": "Main Auto Attendant",
  "identity": "uuid-string",
  "languageId": "en-US",
  "status": "created",
  "resource_check_results": [
    {
      "menu_option_index": 0,
      "call_target_id": "sales-queue-identity-guid",
      "call_target_type": "CallQueue",
      "resource_check": {
        "has_resource_account": true,
        "resource_account_id": "resource-guid",
        "resource_account_type": "ApplicationEndpoint",
        "method_used": "ApplicationInstances"
      }
    }
  ]
}
```

**Response (Skipped - Missing Resource Accounts):**
```json
{
  "message": "Auto Attendant creation skipped due to missing resource accounts",
  "status": "skipped",
  "reason": "One or more call queues in the menu options do not have associated resource accounts",
  "resource_check_results": [...],
  "available_queues_with_resources": [
    {
      "identity": "existing-queue-guid",
      "name": "Existing Queue with Resource",
      "resource_account_id": "resource-guid",
      "resource_account_name": "Existing Resource Account"
    }
  ],
  "suggestions": [
    "Create resource accounts for your call queues before creating Auto Attendants",
    "Use existing call queues that already have resource accounts",
    "Resource accounts can be created using: New-CsOnlineApplicationInstance"
  ]
}
```

**Time:** ~6-8 seconds
**Note:** Automatically verifies resource accounts for call queue targets and provides helpful guidance when they're missing

### POST /autoattendants?session_id={session_id} (Create Auto Attendant - Session)
**Description:** Create Auto Attendant using existing authenticated session (faster for multiple operations). Includes the same resource account verification as the direct endpoint.

**Request/Response:** Same as direct endpoint
**Time:** ~3-4 seconds (reuses session)

### GET /callqueues/{queue_identity}/resource-account?session_id={session_id}
**Description:** Check if a specific call queue has an associated resource account.

**Path Parameters:**
- **queue_identity**: str - Call queue identity to check

**Response:**
```json
{
  "queue_identity": "queue-guid",
  "queue_name": "Sales Queue",
  "has_resource_account": true,
  "resource_account_id": "resource-guid",
  "resource_account_type": "ApplicationEndpoint",
  "method_used": "ApplicationInstances",
  "status": "checked"
}
```

### GET /callqueues/resource-accounts?session_id={session_id}
**Description:** List all call queues that have associated resource accounts.

**Response:**
```json
{
  "message": "Found 2 call queues with resource accounts",
  "queues": [
    {
      "identity": "queue-guid-1",
      "name": "Sales Queue",
      "resource_account_id": "resource-guid-1",
      "resource_account_name": "Sales Resource Account"
    },
    {
      "identity": "queue-guid-2",
      "name": "Support Queue",
      "resource_account_id": "resource-guid-2",
      "resource_account_name": "Support Resource Account"
    }
  ],
  "count": 2,
  "status": "success"
}
```

### GET /autoattendants?session_id={session_id} (List Auto Attendants)
**Description:** List all Auto Attendants (IVR systems) in the tenant.

**Response:**
```json
{
  "message": "Found 2 auto attendants",
  "attendants": [
    {
      "identity": "uuid-string",
      "name": "Main Auto Attendant",
      "languageid": "en-US",
      "enablevoiceresponse": "True"
    }
  ],
  "count": 2
}
```

## ACS Federation

### GET /acs/federation?session_id={session_id}
**Description:** Get current ACS federation configuration.

**Response:**
```json
{
  "identity": "Global",
  "enableAcsUsers": true,
  "requireAcsFederationForMeeting": false,
  "labelForAllowedAcsUsers": "Unverified",
  "hideBannerForAllowedAcsUsers": false
}
```

### PUT /acs/federation?session_id={session_id}
**Description:** Update ACS federation configuration.

**Request Body:**
- **enableAcsUsers**: bool (required)
- **requireAcsFederationForMeeting**: bool (default false)
- **labelForAllowedAcsUsers**: str (default "Unverified") 
- **hideBannerForAllowedAcsUsers**: bool (default false)

## Performance Comparison

| Method | Authentication | User Creation | Team Creation | Add to Team | Call Queue Creation | Add Agent | Auto Attendant Creation |
|--------|----------------|---------------|---------------|-------------|---------------------|-----------|------------------------|
| **Direct** | Per request | ~8-9 seconds | ~3-4 seconds | ~2-3 seconds | ~4-6 seconds | N/A | ~6-8 seconds |
| **Session** | Once per session | ~3-4 seconds | ~2-3 seconds | ~1-2 seconds | ~2-3 seconds | ~2-3 seconds | ~3-4 seconds |

**Performance Notes:**
- **Direct endpoints** are simpler but slower due to authentication overhead
- **Session endpoints** are faster for multiple operations (authentication happens once)
- **Call queue operations** require Teams PowerShell module connection
- **Actual times** may vary based on network conditions and Azure AD replication

## Usage Patterns

### One-off Operations
Use direct endpoints when you need to create a single user/team without maintaining a session:
```bash
curl -X POST http://localhost:8001/users/direct -H "Content-Type: application/json" -d '{...}'
```

### Bulk Operations
Use session-based endpoints when creating multiple users/teams for better performance:
```bash
# 1. Create session
SESSION_ID=$(curl -X POST http://localhost:8001/auth/connect | jq -r '.session_id')

# 2. Create multiple users (much faster)
curl -X POST "http://localhost:8001/users/session?session_id=$SESSION_ID" -H "Content-Type: application/json" -d '{...}'
curl -X POST "http://localhost:8001/users/session?session_id=$SESSION_ID" -H "Content-Type: application/json" -d '{...}'

# 3. Clean up
curl -X POST "http://localhost:8001/auth/disconnect?session_id=$SESSION_ID"
```

## Authentication Requirements

- **Azure App Registration** with certificate-based authentication
- **Microsoft Graph permissions:**
  - `User.ReadWrite.All` - Required for user creation
  - `Group.ReadWrite.All` - Required for team creation and management
  - `Team.Create` - Required for creating teams
  - `TeamSettings.ReadWrite.All` - Required for team configuration
  - `Directory.ReadWrite.All` - Alternative broader permission
- **Microsoft Teams permissions:**
  - Teams administrator role required for call queue operations
  - ACS federation configuration permissions
- **Certificate files:** teamsfed.pfx, teamsfed.crt, teamsfed.key in project root
- **PowerShell modules:** MicrosoftTeams, Microsoft.Graph

## Complete Workflow Examples

### Teams Workflow: Create User, Team, and Add User to Team

#### 1. Create User
```bash
curl -X POST http://localhost:9000/users/direct \
  -H "Content-Type: application/json" \
  -d '{
    "accountEnabled": true,
    "displayName": "John Doe", 
    "userPrincipalName": "john.doe@yourdomain.com",
    "mailNickname": "johndoe",
    "password": "TempP@ssw0rd123!",
    "forceChangePassword": true
  }'
```

#### 2. Create Team
```bash
curl -X POST http://localhost:9000/teams/direct \
  -H "Content-Type: application/json" \
  -d '{
    "displayName": "Project Team",
    "description": "Team for project collaboration", 
    "mailNickname": "projectteam",
    "visibility": "Private"
  }'
```

#### 3. Add User to Team
```bash
curl -X POST "http://localhost:9000/teams/{team_id}/members/direct" \
  -H "Content-Type: application/json" \
  -d '{
    "user": "john.doe@yourdomain.com"
  }'
```

### Call Queue Workflow: Create User, Call Queue, and Add Agent

#### 1. Create User (Agent)
```bash
curl -X POST http://localhost:9000/users/direct \
  -H "Content-Type: application/json" \
  -d '{
    "accountEnabled": true,
    "displayName": "Support Agent",
    "userPrincipalName": "agent@company.com", 
    "mailNickname": "agent",
    "password": "TempP@ssw0rd123!",
    "forceChangePassword": true
  }'
```

#### 2. Create Call Queue
```bash
curl -X POST http://localhost:9000/callqueues/direct \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Support Queue",
    "routingMethod": "RoundRobin",
    "welcomeTextToSpeechPrompt": "Welcome to customer support",
    "overflowThreshold": 20,
    "timeoutThreshold": 1200,
    "agentAlertTime": 15
  }'
```

#### 3. Create Session and Add Agent
```bash
# Create session
SESSION_ID=$(curl -X POST http://localhost:9000/auth/connect | jq -r '.session_id')

# Add agent to queue
curl -X POST "http://localhost:9000/callqueues/{queue_identity}/agents?session_id=$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "userPrincipalName": "agent@company.com"
  }'
```

#### 4. Get Object ID for Azure Communication Services
```bash
# Find resource account email from Teams Admin Center first
curl -X POST "http://localhost:9000/callqueues/objectid?session_id=$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "resourceAccountEmail": "queue-resource@company.onmicrosoft.com"
  }'
```

#### 5. Use in Azure Communication Services
```javascript
// Use the callingObjectId from step 4
const callQueueId = "28:orgid:uuid-from-response";
call = callAgent.startCall([{ teamsAppId: callQueueId, cloud: "public" }], options);
```

### Auto Attendant (IVR) Workflow: Complete Call Center Setup

#### 1. Create Users (Agents)
```bash
curl -X POST http://localhost:9000/users/direct \
  -H "Content-Type: application/json" \
  -d '{
    "accountEnabled": true,
    "displayName": "Sales Agent",
    "userPrincipalName": "sales@company.com",
    "mailNickname": "sales",
    "password": "TempP@ssw0rd123!",
    "forceChangePassword": true
  }'

curl -X POST http://localhost:9000/users/direct \
  -H "Content-Type: application/json" \
  -d '{
    "accountEnabled": true,
    "displayName": "Support Agent", 
    "userPrincipalName": "support@company.com",
    "mailNickname": "support",
    "password": "TempP@ssw0rd123!",
    "forceChangePassword": true
  }'
```

#### 2. Create Call Queues
```bash
# Sales Queue
curl -X POST http://localhost:9000/callqueues/direct \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sales Queue",
    "routingMethod": "RoundRobin",
    "welcomeTextToSpeechPrompt": "Welcome to sales",
    "agents": []
  }'

# Support Queue  
curl -X POST http://localhost:9000/callqueues/direct \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Support Queue", 
    "routingMethod": "Serial",
    "welcomeTextToSpeechPrompt": "Welcome to support",
    "agents": []
  }'
```

#### 3. Create Auto Attendant (IVR System)
```bash
curl -X POST http://localhost:9000/autoattendants/direct \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main IVR System",
    "greetingPrompt": "Welcome to Acme Corporation! Thank you for calling.",
    "menuOptions": [
      {
        "dtmfResponse": "1",
        "prompt": "Sales Department", 
        "callTargetType": "CallQueue",
        "callTargetId": "sales-queue-identity"
      },
      {
        "dtmfResponse": "2",
        "prompt": "Technical Support",
        "callTargetType": "CallQueue", 
        "callTargetId": "support-queue-identity"
      }
    ],
    "timeoutPrompt": "We did not receive a response. Please try again."
  }'
```

#### 4. Add Agents to Queues
```bash
# Create session for multiple operations
SESSION_ID=$(curl -X POST http://localhost:9000/auth/connect | jq -r '.session_id')

# Add sales agent to sales queue
curl -X POST "http://localhost:9000/callqueues/sales-queue-id/agents?session_id=$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"userPrincipalName": "sales@company.com"}'

# Add support agent to support queue
curl -X POST "http://localhost:9000/callqueues/support-queue-id/agents?session_id=$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"userPrincipalName": "support@company.com"}'
```

#### 5. Complete Call Center Flow
```
Caller → Auto Attendant (IVR) → Menu Selection → Call Queue → Available Agent
       ↓
   "Welcome to Acme Corporation!"
       ↓
   "Press 1 for Sales, Press 2 for Support" 
       ↓
   [Caller presses 1] → Sales Queue → Sales Agent
   [Caller presses 2] → Support Queue → Support Agent
```

## Implementation Details

### Team Creation Requirements
- **Template**: Uses Microsoft Teams standard template
- **Owner**: Automatically assigns the first available admin user as team owner
- **Permissions**: Requires `Team.Create` and `Group.ReadWrite.All` permissions
- **Visibility**: Supports Private and Public teams

### Call Queue Requirements
- **Teams PowerShell Module**: Uses `New-CsCallQueue`, `Set-CsCallQueue`, `Get-CsCallQueue` cmdlets
- **Resource Accounts**: Automatically created and associated with call queues
- **Agent Assignment**: Users must exist before adding as agents (use user GUID, not email)
- **Azure Communication Services**: Object IDs formatted as `28:orgid:{guid}` for calling
- **Routing Methods**: Attendant, Serial, RoundRobin, LongestIdle
- **Actions**: Disconnect, Forward, Voicemail, SharedVoicemail for overflow/timeout

### Auto Attendant (IVR) Requirements
- **Teams PowerShell Module**: Uses `New-CsAutoAttendant`, `New-CsAutoAttendantMenu`, `New-CsAutoAttendantMenuOption`, `New-CsAutoAttendantPrompt` cmdlets
- **Resource Accounts**: Must be associated with call queues before routing to them
- **Menu Options**: Support DTMF responses (Tone1, Tone2, etc.) with routing targets
- **Prompts**: Text-to-speech for greetings and menu options
- **Call Targets**: Can route to CallQueues, Users, or External phone numbers
- **Timezone**: Required parameter for business hours handling
- **Voice Recognition**: Optional voice response capability alongside DTMF

### User Requirements
- **UPN Format**: Must be valid email format (user@domain.com)
- **Password Complexity**: Must meet Azure AD password requirements
- **Domain**: Must be a verified domain in your Azure AD tenant

### Error Handling
- **User exists**: Returns appropriate error if user already exists
- **Team exists**: Returns appropriate error if team name/mailNickname conflicts
- **Call queue exists**: Returns appropriate error if call queue name conflicts
- **Permission issues**: Clear error messages for missing permissions
- **Network timeouts**: Automatic retry logic for transient failures
- **PowerShell errors**: Detailed parsing of Teams PowerShell command errors

## Server Configuration

**Start server:**
```bash
uvicorn app:app --host 0.0.0.0 --port 9000
```

**API Documentation:** Available at `http://localhost:9000/docs` (FastAPI auto-generated)

## Microsoft Teams Call Center Integration

The API provides complete integration with Microsoft Teams calling infrastructure, supporting both Call Queues and Auto Attendants (IVR) with Azure Communication Services:

### Key Features
- **Complete Call Center Setup**: Auto Attendants (IVR) + Call Queues + Agents
- **Full Call Queue Management**: Create, configure, and manage call queues via API
- **IVR System Creation**: Auto Attendants with multi-level menu systems
- **Agent Management**: Add/remove users as call queue agents dynamically  
- **Azure Communication Services Ready**: Provides correctly formatted Object IDs for calling
- **Enterprise Features**: Supports overflow handling, timeout actions, welcome messages, hold music
- **Multiple Routing Methods**: Attendant, Serial, RoundRobin, LongestIdle distribution
- **Voice & DTMF Support**: Text-to-speech prompts and keypad navigation
- **Real-time Configuration**: Changes take effect immediately in Microsoft Teams

### Complete Call Center Architecture
```
Azure Communication Services → Auto Attendant (IVR) → Call Queues → Agents
                             ↓
                        "Press 1 for Sales"
                        "Press 2 for Support"  
                             ↓
                    Routes to appropriate queue
                             ↓
                    Distributes to available agents
```

### Integration Workflow
1. **Create Users** → Add users who will be agents
2. **Create Call Queues** → Configure routing and thresholds for different departments
3. **Create Auto Attendant** → Set up IVR menu system routing to queues
4. **Add Agents** → Assign users to handle calls in each queue
5. **Get Object ID** → Retrieve ID for Azure Communication Services calling
6. **Implement Calling** → Use Object ID in your calling application

### Azure Communication Services Usage
```javascript
// After getting Object ID from API
const autoAttendantId = "28:orgid:your-object-id-here";

// Start call to Teams Auto Attendant (IVR)
const call = callAgent.startCall([
  { teamsAppId: autoAttendantId, cloud: "public" }
], { videoOptions: videoOptions });

// Caller hears: "Welcome to Acme Corporation! Press 1 for Sales, Press 2 for Support"
// Based on selection, routes to appropriate call queue and agents
```

### Real-World Example: "democakeaa"
The example Auto Attendant created demonstrates a complete setup:
- **Auto Attendant**: "Welcome to Demo Cake Company! Press 1 to buy some cake"
- **Routes to**: "demoqueueiscake" call queue  
- **Agent**: demogod@cloudwarriors.onmicrosoft.com handles calls
- **Complete Flow**: Caller → IVR Menu → Call Queue → Agent

This creates enterprise-grade call center functionality using Microsoft Teams infrastructure with API-driven configuration.

## Emergency Calling Setup

### POST /emergency/setup (Emergency Calling Setup)
**Description:** Set up complete emergency calling configuration for a user including address, policies, and routing.

**Request Body:**
- **userPrincipalName**: str (required) - User to configure emergency calling for
- **emergencyAddress**: object (required)
  - **houseNumber**: str (required)
  - **streetName**: str (required)
  - **city**: str (required)
  - **stateOrProvince**: str (required)
  - **postalCode**: str (required)
  - **countryOrRegion**: str (default "US")
  - **companyName**: str (required)
  - **description**: str (required)
  - **latitude**: float (default approximate coordinates)
  - **longitude**: float (default approximate coordinates)
- **notificationGroup**: str (optional) - Users to notify of emergency calls
- **emergencyNumbers**: array (default ["911"]) - Emergency numbers to route

**Example Request:**
```json
{
  "userPrincipalName": "demo654@cloudwarriors.onmicrosoft.com",
  "emergencyAddress": {
    "houseNumber": "5561",
    "streetName": "Heatherton Road",
    "city": "Milton",
    "stateOrProvince": "FL",
    "postalCode": "32570",
    "countryOrRegion": "US",
    "companyName": "Cloud Warriors Demo",
    "description": "Demo654 Emergency Location",
    "latitude": 30.6303,
    "longitude": -87.0465
  },
  "notificationGroup": "demo654@cloudwarriors.onmicrosoft.com",
  "emergencyNumbers": ["911"]
}
```

**Response:**
```json
{
  "message": "Emergency calling setup completed successfully",
  "userPrincipalName": "demo654@cloudwarriors.onmicrosoft.com",
  "emergencyAddress": "5561 Heatherton Road, Milton, FL 32570",
  "status": "completed",
  "policies": {
    "emergencyCallingPolicy": "EmergencyPolicy-demo654",
    "emergencyCallRoutingPolicy": "EmergencyRouting-demo654"
  }
}
```

**Time:** ~10-15 seconds
**Requirements:** Enhanced emergency services licensing, valid geographic coordinates

### GET /emergency/policies?session_id={session_id} (List Emergency Policies)
**Description:** List all emergency calling policies in the tenant.

**Response:**
```json
{
  "message": "Found 2 emergency calling policies",
  "policies": [
    {
      "identity": "EmergencyPolicy-demo654",
      "description": "Emergency calling policy for demo654@cloudwarriors.onmicrosoft.com",
      "notification_group": "demo654@cloudwarriors.onmicrosoft.com"
    }
  ],
  "count": 2
}
```

**Time:** ~3-5 seconds

## Emergency Calling Requirements

### Licensing Requirements
- **Phone System** license or equivalent
- **Calling Plan** or **Direct Routing** for emergency calling
- **Enhanced Emergency Services** for physical address validation
- **Teams Phone** license for advanced emergency features

### Geographic Requirements
- **Valid coordinates**: Latitude and longitude for address validation
- **Supported regions**: Emergency calling features vary by country/region
- **Address validation**: Physical addresses must be validated by emergency services

### Permission Requirements
- **Teams Administrator** role
- **Emergency Calling Policy** permissions
- **Location Information Service (LIS)** permissions
- **Enhanced Emergency Services** permissions

### Implementation Notes
- **Address validation**: Requires exact latitude/longitude coordinates
- **Policy assignment**: Policies are automatically assigned to users
- **Notification groups**: Specify users to be notified of emergency calls
- **Emergency numbers**: Default is 911, configurable per region
- **Location services**: LIS integration for automatic location detection

### Emergency Calling Workflow
1. **Create emergency address** with valid geographic coordinates
2. **Configure emergency policies** for calling and routing
3. **Assign policies to users** who need emergency calling capabilities
4. **Set up notification groups** for emergency call alerts
5. **Test emergency calling** to ensure proper routing and notifications

### Error Handling
- **Invalid coordinates**: Returns error if latitude/longitude are invalid
- **Licensing issues**: Clear error messages for missing licenses
- **Permission errors**: Detailed messages for missing permissions
- **Address validation**: Errors if address cannot be validated
- **Policy conflicts**: Warnings if policies already exist

### Testing Emergency Calling
```bash
# Test emergency calling setup
curl -X POST http://localhost:9000/emergency/setup \
  -H "Content-Type: application/json" \
  -d '{
    "userPrincipalName": "test@domain.com",
    "emergencyAddress": {
      "houseNumber": "123",
      "streetName": "Main St",
      "city": "Anytown",
      "stateOrProvince": "ST",
      "postalCode": "12345",
      "companyName": "Test Company",
      "description": "Test Emergency Location"
    }
  }'
```

**Note:** Emergency calling setup requires appropriate licensing and may not be available in all tenant configurations. Contact your Microsoft administrator for licensing requirements.