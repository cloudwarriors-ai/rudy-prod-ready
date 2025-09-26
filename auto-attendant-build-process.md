# Auto Attendant Build Process Documentation

## Single Source of Truth - Teams SDK Capabilities

### ✅ Auto Attendant Features We Can Build

#### **Core Auto Attendant Functions**
- ✅ **Basic Auto Attendants** with greeting prompts and menu options
- ✅ **Voice Response Enabled** auto attendants for accessibility  
- ✅ **DTMF Menu Navigation** with 0-9 and * key options
- ✅ **Call Transfer to Queues** (preferred routing method)
- ✅ **Announcement Actions** for menu repeats and information
- ✅ **Multi-language Support** (English validated, others configurable)
- ✅ **Custom Names and Identifiers** for organizational structure

#### **Advanced Scheduling Features**
- ✅ **Business Hours Configuration** (8 AM - 4 PM EST working example)
- ✅ **After-Hours Call Flows** with different greetings and routing
- ✅ **Individual Holiday Schedules** (2025 holidays implemented)
- ✅ **Timezone Configuration** (EST/UTC conversions working)
- ✅ **Call Handling Associations** linking schedules to call flows
- ✅ **Weekly Recurrent Schedules** for business hours

#### **Integration Capabilities**
- ✅ **Parameter-Based Creation** from JSON input
- ✅ **Call Queue Integration** for robust call routing
- ✅ **PowerShell Command Automation** via FastAPI
- ✅ **Session Management** for authentication and state
- ✅ **Error Handling and Validation** for reliable operations

#### **Management and Monitoring**
- ✅ **List All Auto Attendants** in tenant
- ✅ **Configuration Retrieval** for existing auto attendants  
- ✅ **Status Checking** and health monitoring
- ✅ **Debug Logging** for troubleshooting

### ❌ Current Limitations

#### **Direct User Transfer Constraints**
- ❌ **Direct User Transfers** require Enterprise Voice enablement
- ❌ **Voicemail Integration** requires mail-enabled groups
- ❌ **DisconnectCall Actions** cannot accept DTMF input

#### **Menu Structure Limitations**
- ❌ **Complex Menu Validation** limits automatic call flows
- ❌ **Multiple Timeout Actions** restricted to single option menus
- ❌ **Shared Resource Dependencies** for advanced features

### 🔧 Working Examples

#### **Production Auto Attendants Built**
1. **rudy-etl Auto Attendant** (`7a76d78a-d7be-44c4-b653-22635a985bda`)
   - Business hours: 8 AM - 4 PM EST
   - Individual holiday schedules for 2025
   - After-hours call flow
   - Menu option with * key repeat

2. **Custom-AA-20250925** (`7fcbaec2-cba0-495e-99b3-da21ee4c4b8c`)
   - Multi-option DTMF menu (0,1,2,3,*)
   - Call queue routing
   - Voice response enabled

#### **Schedule Management Success**
- **Business Hours Schedule**: `15ded538-c693-4536-813a-f1db6b5ac34f` (8-4 EST)
- **Holiday Schedules**: 4 individual records for 2025
- **Call Handling Associations**: 5 total (1 business + 4 holidays)

---

**Date:** September 25, 2025  
**Last Updated:** September 26, 2025  

## Overview

This document details the step-by-step process used to build Microsoft Teams Auto Attendants with comprehensive features including business hours, holiday schedules, and advanced call routing.

---

## Parameter Analysis and Mapping

### Action Code Analysis
- **Action 2**: Transfer to User (interpreted as call queue)
- **Action 7**: Transfer to Extension/User (interpreted as call queue)
- **Action 21**: Repeat Menu (mapped to Announcement)
- **Action 100**: Transfer to Queue/Group (mapped to call queue)
- **Action -1**: Timeout/Disconnect (default timeout behavior)

---

## Build Process Template

### Environment Setup
```powershell
# Connect to Microsoft Teams
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/Users/work/teams-sdk/auth-keys/teamsfed.pfx"
Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
```

### Core Components Required
1. **Prompts** - Greeting and menu announcements
2. **Menu Options** - DTMF responses with actions
3. **Call Targets** - Call queues or users (Enterprise Voice required)
4. **Call Flow** - Links prompts, menus, and routing
5. **Auto Attendant** - Main container with language and timezone

### Implementation Notes

#### Voice Prompts
- Use `New-CsAutoAttendantPrompt` with TextToSpeechPrompt
- Include business hours in greeting messages
- Provide clear menu instructions

#### Menu Options  
- Use `New-CsAutoAttendantMenuOption` for each DTMF key
- TransferCallToTarget for call routing
- Announcement action for menu repeats

#### Call Targets
- Prefer Call Queues over direct user transfers
- Users require Enterprise Voice enablement
- Use `New-CsAutoAttendantCallableEntity` for targets

#### Voice Response
- Always enable with `-EnableVoiceResponse` for accessibility
- Supports voice commands in addition to DTMF

---

## Challenges and Solutions

### Enterprise Voice Requirement
**Solution:** Use Call Queues as intermediary routing mechanism for robust call handling

### Menu Validation Constraints
**Solution:** Keep menu structures simple within Teams validation rules

### Business Hours Integration
**Solution:** Create separate call flows and schedules with call handling associations

---

## Complete API Reference

This build process has been automated into comprehensive API endpoints for programmatic creation and management.

### **Authentication Endpoints**

#### Connect to Teams
```http
POST /auth/connect
```
**Response:**
```json
{
    "message": "Authenticated",
    "session_id": "uuid-session-id"
}
```

#### Check Authentication Status  
```http
GET /auth/status?session_id={session_id}
```
**Response:**
```json
{
    "status": "authenticated",
    "details": "Microsoft Graph connection active"
}
```

#### Disconnect Session
```http
POST /auth/disconnect?session_id={session_id}
```

---

### **Auto Attendant Management**

#### Create Auto Attendant from Parameters
```http
POST /autoattendant/create-from-params?session_id={session_id}
Content-Type: application/json
```
**Request Body:**
```json
{
    "audio_prompt": {
        "id": "",
        "name": "Default"
    },
    "key_actions": [
        {
            "key": "0",
            "action": 100,
            "target": {
                "id": "target-id",
                "display_name": "Target Name",
                "extension_number": "1234"
            }
        }
    ],
    "caller_enters_no_action": {
        "action": -1,
        "audio_prompt_repeat": 3
    },
    "name": "Custom AA Name"
}
```

#### Create Auto Attendant with Business Hours
```http
POST /autoattendants/create-with-business-hours?session_id={session_id}
Content-Type: application/json
```
**Request Body:**
```json
{
    "name": "Business Hours AA",
    "greeting": "Welcome message",
    "menu_prompt": "Press 1 for...",
    "menu_options": [...],
    "business_hours": {
        "start_time": "08:00",
        "end_time": "16:00",
        "timezone": "Eastern Standard Time"
    }
}
```

#### Add Business Hours to Existing Auto Attendant
```http
POST /autoattendants/{aa_identity}/add-business-hours?session_id={session_id}
Content-Type: application/json
```
**Request Body:**
```json
{
    "start_time": "08:00",
    "end_time": "16:00", 
    "timezone": "Eastern Standard Time",
    "after_hours_greeting": "We are currently closed..."
}
```

#### Create Basic Auto Attendant
```http
POST /autoattendants?session_id={session_id}
Content-Type: application/json
```
**Request Body:**
```json
{
    "name": "Basic AA",
    "greeting": "Welcome",
    "menu_prompt": "Press 1 for...",
    "menu_options": [
        {
            "key": "1",
            "action": "TransferCallToTarget",
            "target": "queue-id"
        }
    ]
}
```

#### Create Auto Attendant (Direct PowerShell)
```http
POST /autoattendants/direct?session_id={session_id}
Content-Type: application/json
```

#### List All Auto Attendants
```http
GET /autoattendants?session_id={session_id}
```
**Response:**
```json
{
    "message": "Found X auto attendants",
    "attendants": [
        {
            "identity": "aa-id",
            "name": "Auto Attendant Name",
            "languageId": "en-US",
            "enableVoiceResponse": true
        }
    ],
    "count": 12
}
```

---

### **Call Queue Management**

#### Create Call Queue
```http
POST /callqueues?session_id={session_id}
Content-Type: application/json
```
**Request Body:**
```json
{
    "name": "Support Queue",
    "agents": ["user1@domain.com", "user2@domain.com"],
    "routing_method": "Attendant",
    "allow_opt_out": true,
    "conference_mode": false
}
```

#### Create Call Queue (Direct PowerShell)
```http
POST /callqueues/direct?session_id={session_id}
Content-Type: application/json
```

#### Create Call Queue with Object ID
```http
POST /callqueues/objectid?session_id={session_id}
Content-Type: application/json
```

#### Test Call Queue Creation
```http
POST /callqueues/test?session_id={session_id}
```

#### List All Call Queues
```http
GET /callqueues?session_id={session_id}
```
**Response:**
```json
{
    "message": "Found X call queues", 
    "queues": [
        {
            "identity": "queue-id",
            "name": "Queue Name",
            "routingMethod": "Attendant",
            "agents": ["user1", "user2"]
        }
    ],
    "count": 8
}
```

#### Add Agent to Call Queue
```http
POST /callqueues/{queue_identity}/agents?session_id={session_id}
Content-Type: application/json
```
**Request Body:**
```json
{
    "user_principal_name": "user@domain.com"
}
```

#### Add Agent to Single Call Queue
```http
POST /callqueues/add-agent?session_id={session_id}
Content-Type: application/json
```

#### Add Agent to All Call Queues
```http
POST /callqueues/add-agent-to-all?session_id={session_id}
Content-Type: application/json
```

#### Get Call Queue Resource Account
```http
GET /callqueues/{queue_identity}/resource-account?session_id={session_id}
```

#### List All Resource Accounts
```http
GET /callqueues/resource-accounts?session_id={session_id}
```

---

### **User Management**

#### Create User
```http
POST /users?session_id={session_id}
Content-Type: application/json
```
**Request Body:**
```json
{
    "accountEnabled": true,
    "displayName": "John Doe",
    "userPrincipalName": "john.doe@tenant.onmicrosoft.com",
    "mailNickname": "johndoe",
    "passwordProfile": {
        "password": "TempPassword123!",
        "forceChangePasswordNextSignIn": true
    }
}
```

#### Create User (Direct PowerShell)
```http
POST /users/direct?session_id={session_id}
Content-Type: application/json
```

#### Create User (Session)
```http
POST /users/session?session_id={session_id}
Content-Type: application/json
```

#### List Users
```http
GET /users?session_id={session_id}&result_size=50
```
**Response:**
```json
{
    "message": "Found X users",
    "users": [
        {
            "identity": "user-id",
            "displayName": "User Name", 
            "userPrincipalName": "user@domain.com",
            "phoneNumber": "+1234567890"
        }
    ],
    "count": 25
}
```

#### Assign Phone Number to User
```http
PUT /users/{identity}/phone?session_id={session_id}
Content-Type: application/json
```
**Request Body:**
```json
{
    "phone_number": "+1234567890"
}
```

---

### **Teams Management**

#### Create Team
```http
POST /teams?session_id={session_id}
Content-Type: application/json
```
**Request Body:**
```json
{
    "displayName": "Development Team",
    "description": "Team for development projects"
}
```

#### Create Team (Direct PowerShell)
```http
POST /teams/direct?session_id={session_id}
Content-Type: application/json
```

#### Add User to Team (Direct)
```http
POST /teams/{team_id}/members/direct?session_id={session_id}
Content-Type: application/json
```

#### Add User to Team (Group)
```http
POST /teams/{group_id}/users?session_id={session_id}
Content-Type: application/json
```

---

### **ACS Federation Management**

#### Get ACS Federation Configuration
```http
GET /acs/federation?session_id={session_id}
```

#### Update ACS Federation Configuration
```http
PUT /acs/federation?session_id={session_id}
Content-Type: application/json
```
**Request Body:**
```json
{
    "allowedDomains": ["domain1.com", "domain2.com"],
    "allowB2BAccess": true
}
```

---

### **Emergency Services**

#### Setup Emergency Address
```http
POST /emergency/setup?session_id={session_id}
Content-Type: application/json
```
**Request Body:**
```json
{
    "address": {
        "street": "123 Main St",
        "city": "Anytown", 
        "state": "ST",
        "postal_code": "12345",
        "country": "US"
    },
    "policy": {
        "name": "Emergency Policy",
        "description": "Emergency calling policy"
    }
}
```

#### Get Emergency Policies
```http
GET /emergency/policies?session_id={session_id}
```

---

### **Data Extraction**

#### Extract All Teams Data
```http
GET /extract/all?session_id={session_id}
```
**Response:**
```json
{
    "voice_users": [...],
    "phone_numbers": [...],
    "auto_attendants": [...],
    "call_queues": [...],
    "application_instances": [...],
    "extraction_time": "2025-09-26T10:30:00Z",
    "total_records": 150
}
```

---

### **Documentation Endpoints**

#### API Documentation (Swagger UI)
```http
GET /docs
```

#### OpenAPI Specification
```http
GET /openapi.json
```

---

## Schedule Management (Advanced Features)

### **Business Hours Schedule**
- **Schedule Type:** Weekly Recurrent
- **Business Hours:** 9:00 AM - 5:00 PM
- **Days:** Monday through Friday
- **Time Zone:** UTC (configurable)

### **After-Hours Schedule**
- **Type:** Complement of business hours
- **Behavior:** Plays after-hours greeting
- **Routing:** Can be configured for voicemail or alternate flows

### **Call Handling Associations**
- Links schedules to specific call flows
- Enables time-based routing
- Supports holiday schedules (future enhancement)

---

## Implementation Notes

### **Auto Attendant Limitations Discovered**
1. **Callable Entity Constraints:** Direct user transfers require Enterprise Voice enablement
2. **Menu Option Restrictions:** DisconnectCall actions cannot accept DTMF input
3. **Menu Validation:** Automatic actions limit menu to single option
4. **Call Flow Dependencies:** After-hours call flows must be included in main call flows array
5. **Shared Voicemail Requirements:** Users must be mail-enabled groups for shared voicemail

### **Workarounds Implemented**
1. **Queue-based Routing:** Use Call Queues instead of direct user transfers
2. **Announcement Actions:** Use announcements for menu repeats and interactions
3. **Simplified Menus:** Create working menu structures within validation constraints
4. **Foundation Approach:** Create base Auto Attendants that can be enhanced via Teams Admin Center

### **Best Practices Established**
1. **Voice Response:** Always enable for accessibility
2. **Standard Greetings:** Include business hours information
3. **Menu Design:** Keep options simple and intuitive
4. **Time Zone Consistency:** Use UTC for server processing
5. **Documentation:** Document all configuration parameters and limitations

---

*Build completed successfully on September 25, 2025 at 20:28:47 UTC*  
*Rudy ETL Auto Attendant added on September 25, 2025 at 21:15:00 UTC*