# Call Queue Integration for FastAPI Teams SDK

## Overview

I've successfully integrated Microsoft Teams Call Queue creation and management into your FastAPI application based on the Microsoft documentation from research.md. This integration allows you to create call queues that can be used with Azure Communication Services.

## New Endpoints Added

### 1. Create Call Queue (Direct)
**POST** `/callqueues/direct`

Creates a call queue directly using PowerShell without requiring a session.

```json
{
  "name": "Support Call Queue",
  "languageId": "en-US", 
  "routingMethod": "Attendant",
  "agents": ["user1@domain.com", "user2@domain.com"],
  "welcomeTextToSpeechPrompt": "Welcome to our support queue",
  "overflowThreshold": 20,
  "overflowAction": "DisconnectWithBusy", 
  "timeoutThreshold": 1200,
  "timeoutAction": "DisconnectWithBusy",
  "agentAlertTime": 30,
  "conferenceMode": true,
  "useDefaultMusicOnHold": true
}
```

### 2. Create Call Queue (Session-based)
**POST** `/callqueues?session_id={session_id}`

Creates a call queue using an existing authenticated PowerShell session for better performance.

### 3. Get Call Queue Object ID
**POST** `/callqueues/objectid?session_id={session_id}`

Gets the Object ID needed for Azure Communication Services calling from a resource account email.

```json
{
  "resourceAccountEmail": "callqueue@yourtenant.onmicrosoft.com"
}
```

Returns:
```json
{
  "message": "Object ID found successfully",
  "resourceAccountEmail": "callqueue@yourtenant.onmicrosoft.com", 
  "objectId": "guid-here",
  "displayName": "Call Queue Display Name",
  "callingObjectId": "28:orgid:guid-here",
  "status": "found"
}
```

### 4. List Call Queues
**GET** `/callqueues?session_id={session_id}`

Lists all call queues in the tenant with their configuration details.

## Key Features

### Azure Communication Services Integration
- Automatically formats Object IDs for calling (`28:orgid:{id}`)
- Supports both public cloud (`28:orgid:`) and government cloud (`28:gcch:`) formats
- Compatible with the Azure Communication Services Calling SDK

### PowerShell Teams Module Integration  
- Uses `New-CsCallQueue` for creation
- Uses `Get-CsCallQueue` for listing
- Uses `Get-MgUser` for Object ID lookup
- Handles authentication automatically

### Flexible Agent Assignment
- Supports user email arrays for agents
- Configurable routing methods (Attendant, Serial, RoundRobin, LongestIdle)
- Optional overflow and timeout handling

## Usage Example

1. **Create a session:**
```bash
curl -X POST "http://localhost:8000/auth/connect"
```

2. **Create a call queue:**
```bash
curl -X POST "http://localhost:8000/callqueues/direct" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Support Queue",
    "agents": ["support1@company.com", "support2@company.com"],
    "routingMethod": "RoundRobin",
    "welcomeTextToSpeechPrompt": "Welcome to support"
  }'
```

3. **Get the Object ID for calling:**
```bash
curl -X POST "http://localhost:8000/callqueues/objectid?session_id={session_id}" \
  -H "Content-Type: application/json" \
  -d '{"resourceAccountEmail": "support-queue@company.onmicrosoft.com"}'
```

4. **Use in Azure Communication Services:**
```javascript
// Use the callingObjectId from step 3
const callQueueId = "28:orgid:your-object-id-here";
call = callAgent.startCall([{ teamsAppId: callQueueId, cloud: "public" }], options);
```

## Technical Implementation

### Authentication
- Uses your existing certificate-based authentication 
- Connects to both Microsoft Teams and Microsoft Graph
- Supports both session-based and direct execution

### Error Handling
- Comprehensive error parsing from PowerShell output
- Timeout handling (120s for creation, 60s for listing)
- Detailed error messages with troubleshooting information

### Performance Optimizations
- Session-based endpoints reuse PowerShell connections
- Direct endpoints for one-off operations
- Efficient PowerShell parameter building

## Microsoft Documentation Reference

This implementation follows the Microsoft Teams Call Queue documentation:
- [Teams Call Queue Quickstart](https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/voice-video-calling/get-started-teams-call-queue)
- Uses the exact workflow: Create queue → Get resource account → Get Object ID → Use in calling

## Next Steps

1. Test call queue creation with your Teams tenant
2. Verify agent assignment works correctly  
3. Test the Object ID lookup with real resource accounts
4. Integrate with your Azure Communication Services calling application