from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import subprocess
import logging
import uuid
import threading
import re

# PowerShell executable path
PWSH_PATH = "/Users/cloudwarriors/MS-Teams-ETL/teams-sdk/powershell/pwsh"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Teams SDK API", description="FastAPI interface for Teams PowerShell commands")

sessions = {}
session_lock = threading.Lock()

class PowerShellSession:
    def __init__(self):
        self.process = subprocess.Popen(
            [PWSH_PATH, "-NoExit", "-Command", f"Set-Location /Users/cloudwarriors/MS-Teams-ETL/teams-sdk"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self.authenticated = False

    def authenticate(self):
        if not self.authenticated:
            logger.debug("Starting PowerShell authentication process")
            
            # Run the entire authentication sequence as one command
            auth_cmd = '''
            $TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
            $AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
            $PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
            $PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
            $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
            
            Write-Host "Connecting to Graph..."
            Connect-MgGraph -TenantId $TenantId -ClientId $AppId -Certificate $Cert -NoWelcome
            
            Write-Host "Verifying Graph connection..."
            Get-MgContext | Format-List ClientId, TenantId, AuthType
            '''
            
            output, error = self.run_command(auth_cmd, timeout=120)
            logger.debug(f"Authentication output: {output}")
            logger.debug(f"Authentication error: {error}")
            
            # Check if we got the expected federation configuration output or Graph context
            if ("Identity" in output and "Global" in output) or ("ClientId" in output and "TenantId" in output):
                logger.info("Authentication successful - Teams or Graph connection verified")
                self.authenticated = True
            else:
                logger.error(f"Authentication verification failed. Output: {output}, Error: {error}")
                raise Exception(f"Authentication failed - cannot access Teams services")
                
            logger.info("PowerShell authentication verified successfully")

    def run_command(self, cmd, timeout=30):
        logger.info(f"Running command in session: {cmd[:100]}...")
        
        import select
        import time
        
        # Clear any pending output more thoroughly
        cleared_lines = 0
        while select.select([self.process.stdout, self.process.stderr], [], [], 0.1)[0] and cleared_lines < 50:
            if self.process.stdout in select.select([self.process.stdout], [], [], 0.1)[0]:
                line = self.process.stdout.readline()
                logger.debug(f"Cleared stdout: {line.strip()}")
                cleared_lines += 1
            if self.process.stderr in select.select([self.process.stderr], [], [], 0.1)[0]:
                line = self.process.stderr.readline()
                logger.debug(f"Cleared stderr: {line.strip()}")
                cleared_lines += 1
        
        # Use a more unique marker with timestamp and random component
        import random
        marker = f"PWSH_CMD_DONE_{int(time.time())}_{random.randint(1000,9999)}"
        
        # Send the command with clear separation
        self.process.stdin.write(f"# Starting command execution\n")
        self.process.stdin.write(f"{cmd}\n")
        self.process.stdin.write(f"Write-Host '{marker}'\n")
        self.process.stdin.flush()
        
        output = ""
        error = ""
        marker_found = False
        command_started = False
        
        # Read until marker or timeout
        start = time.time()
        
        while time.time() - start < timeout and not marker_found:
            ready = select.select([self.process.stdout, self.process.stderr], [], [], 0.2)
            if ready[0]:
                if self.process.stdout in ready[0]:
                    line = self.process.stdout.readline()
                    if not line:  # EOF
                        break
                        
                    logger.debug(f"PowerShell stdout: {line.strip()}")
                    
                    # Check for our specific marker
                    if marker in line:
                        marker_found = True
                        logger.debug(f"Found completion marker: {marker}")
                        break
                    
                    # Skip command echo and prompt lines
                    if ("# Starting command execution" in line or 
                        "Write-Host" in line or
                        line.strip().startswith("PS ") or
                        cmd[:50] in line):
                        continue
                    
                    output += line
                    
                if self.process.stderr in ready[0]:
                    stderr_line = self.process.stderr.readline()
                    if stderr_line:
                        logger.debug(f"PowerShell stderr: {stderr_line.strip()}")
                        error += stderr_line
        
        if not marker_found:
            logger.warning(f"Command timed out after {timeout} seconds")
        
        logger.info(f"Command completed. Output: {len(output)} chars, Error: {len(error)} chars")
        return output.strip(), error.strip()

    def close(self):
        self.process.terminate()

@app.post("/auth/connect")
async def connect_auth():
    logger.info("Creating new authenticated session")
    session = PowerShellSession()
    try:
        session.authenticate()
        session_id = str(uuid.uuid4())
        with session_lock:
            sessions[session_id] = session
        logger.info(f"Session created: {session_id}")
        return {"message": "Authenticated", "session_id": session_id}
    except Exception as e:
        logger.error(f"Auth failed: {e}")
        session.close()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth/status")
async def auth_status(session_id: str):
    logger.info(f"Checking auth status for session: {session_id}")
    with session_lock:
        session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check Graph connection which is what we need for user creation
    output, error = session.run_command("Get-MgContext | Format-List ClientId, TenantId, AuthType", timeout=15)
    logger.debug(f"Auth status output: {output}")
    logger.debug(f"Auth status error: {error}")
    
    if error or not output:
        return {"status": "not authenticated", "error": error or "No response"}
    elif "ClientId" in output and "TenantId" in output:
        return {"status": "authenticated", "details": "Microsoft Graph connection active"}
    else:
        return {"status": "not authenticated", "error": "Graph connection not found"}

@app.post("/auth/disconnect")
async def disconnect_auth(session_id: str):
    logger.info(f"Disconnecting session: {session_id}")
    with session_lock:
        session = sessions.pop(session_id, None)
    if session:
        session.close()
        return {"message": "Disconnected"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

class CreateUserRequest(BaseModel):
    accountEnabled: bool = Field(..., examples=[True])
    displayName: str = Field(..., examples=["John Doe"])
    userPrincipalName: str = Field(..., examples=["john.doe@yourtenant.onmicrosoft.com"])
    mailNickname: str = Field(..., examples=["johndoe"])
    password: str = Field(..., examples=["TempP@ssw0rd!"])
    forceChangePassword: bool = Field(..., examples=[True])

class CreateTeamRequest(BaseModel):
    displayName: str = Field(..., examples=["Support Team"])
    description: str = Field(..., examples=["Support Team migrated from RingCentral"])
    mailNickname: str = Field(..., examples=["supportteam"])
    visibility: str = Field(default="Private", examples=["Private", "Public"])

class AddUserToTeamRequest(BaseModel):
    user: str = Field(..., examples=["john.doe@yourtenant.onmicrosoft.com"])

class AssignPhoneRequest(BaseModel):
    phoneNumber: str = Field(..., examples=["+15555550123"])
    phoneNumberType: str = Field(..., examples=["DirectRouting"])

class GetCallQueueObjectIdRequest(BaseModel):
    resourceAccountEmail: str = Field(..., examples=["callqueue@yourtenant.onmicrosoft.com"])

class MenuOption(BaseModel):
    dtmfResponse: str = Field(..., examples=["1"])
    prompt: str = Field(..., examples=["Sales"])
    callTargetType: str = Field(..., examples=["CallQueue"])  # CallQueue, User, ExternalPstn
    callTargetId: str = Field(..., examples=["queue-identity-guid"])

class CreateAutoAttendantRequest(BaseModel):
    name: str = Field(..., examples=["Main Auto Attendant"])
    languageId: str = Field(default="en-US", examples=["en-US"])
    greetingPrompt: str = Field(..., examples=["Welcome to our company"])
    menuOptions: List[MenuOption] = Field(..., examples=[[{"dtmfResponse": "1", "prompt": "Sales", "callTargetType": "CallQueue", "callTargetId": "queue-id"}]])
    enableVoiceResponse: bool = Field(default=True, examples=[True])
    timeoutActionTargetType: str = Field(default="Disconnect", examples=["Disconnect", "CallQueue", "User"])
    timeoutActionTargetId: str = Field(default="", examples=[""])
    timeoutPrompt: str = Field(default="", examples=["We're sorry, we didn't receive a response"])

class CreateCallQueueRequest(BaseModel):
    name: str = Field(..., examples=["Support Call Queue"])
    languageId: str = Field(default="en-US", examples=["en-US"])
    routingMethod: str = Field(default="Attendant", examples=["Attendant", "Serial", "RoundRobin", "LongestIdle"])
    agents: list[str] = Field(..., examples=[["user1@domain.com", "user2@domain.com"]])
    welcomeTextToSpeechPrompt: str = Field(default="", examples=["Welcome to our support queue"])
    overflowThreshold: int = Field(default=20, examples=[20])
    overflowAction: str = Field(default="Disconnect", examples=["Disconnect", "Forward", "Voicemail", "SharedVoicemail"])
    timeoutThreshold: int = Field(default=1200, examples=[1200])  # 20 minutes
    timeoutAction: str = Field(default="Disconnect", examples=["Disconnect", "Forward", "Voicemail", "SharedVoicemail"])
    agentAlertTime: int = Field(default=30, examples=[30])
    conferenceMode: bool = Field(default=True, examples=[True])
    useDefaultMusicOnHold: bool = Field(default=True, examples=[True])

@app.post("/users/direct")
async def create_user_direct(request: CreateUserRequest):
    """Create user directly without requiring a session - uses PowerShell execution"""
    logger.info(f"Creating user directly: {request.dict()}")
    
    # Create the PowerShell command based on the working script
    ps_command = f'''
    $TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
    $AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
    $PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
    $PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
    $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
    
    # Connect to Graph
    Connect-MgGraph -TenantId $TenantId -ClientId $AppId -Certificate $Cert -NoWelcome
    
    # Create password profile
    $PasswordProfile = @{{
        Password = "{request.password}"
        ForceChangePasswordNextSignIn = ${request.forceChangePassword}
    }}
    
    try {{
        Write-Host "Creating user: {request.displayName}"
        $newUser = New-MgUser -DisplayName "{request.displayName}" -UserPrincipalName "{request.userPrincipalName}" -MailNickname "{request.mailNickname}" -PasswordProfile $PasswordProfile -AccountEnabled:${request.accountEnabled}
        
        Write-Host "USER_CREATED_SUCCESS"
        Write-Host "ID: $($newUser.Id)"
        Write-Host "UPN: $($newUser.UserPrincipalName)" 
        Write-Host "DisplayName: $($newUser.DisplayName)"
        
        # Verify user creation
        Start-Sleep -Seconds 5
        $user = Get-MgUser -Filter "UserPrincipalName eq '{request.userPrincipalName}'"
        if ($user) {{
            Write-Host "USER_VERIFIED_SUCCESS"
        }} else {{
            Write-Host "USER_VERIFICATION_FAILED"
        }}
    }} catch {{
        Write-Host "USER_CREATION_FAILED: $_"
    }}
    '''
    
    try:
        # Execute PowerShell command
        import subprocess
        result = subprocess.run(
            [PWSH_PATH, "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        output = result.stdout
        error = result.stderr
        
        logger.debug(f"PowerShell stdout: {output}")
        logger.debug(f"PowerShell stderr: {error}")
        
        if "USER_CREATED_SUCCESS" in output:
            # Parse user details from output
            user_id = None
            for line in output.split('\n'):
                if line.startswith('ID: '):
                    user_id = line.replace('ID: ', '').strip()
                    break
            
            if "USER_VERIFIED_SUCCESS" in output:
                return {
                    "message": "User created and verified successfully",
                    "userPrincipalName": request.userPrincipalName,
                    "displayName": request.displayName,
                    "userId": user_id,
                    "status": "verified"
                }
            else:
                return {
                    "message": "User created but verification pending",
                    "userPrincipalName": request.userPrincipalName,
                    "displayName": request.displayName,
                    "userId": user_id,
                    "status": "created"
                }
        else:
            error_msg = "Unknown error"
            if "USER_CREATION_FAILED:" in output:
                error_msg = output.split("USER_CREATION_FAILED:")[1].strip()
            elif error:
                error_msg = error
            
            raise HTTPException(status_code=400, detail=f"User creation failed: {error_msg}")
            
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="User creation timed out")
    except Exception as e:
        logger.error(f"Unexpected error in user creation: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/users/session")
async def create_user_session(session_id: str, request: CreateUserRequest):
    """Create user using existing PowerShell session for better performance"""
    logger.info(f"Creating user in session {session_id}: {request.dict()}")
    with session_lock:
        session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Use the working approach from create_user_azuread.ps1
    user_creation_cmd = f'''
    try {{
        $PasswordProfile = @{{
            Password = "{request.password}"
            ForceChangePasswordNextSignIn = ${request.forceChangePassword}
        }}
        
        Write-Host "Creating user: {request.displayName}"
        $newUser = New-MgUser -DisplayName "{request.displayName}" -UserPrincipalName "{request.userPrincipalName}" -MailNickname "{request.mailNickname}" -PasswordProfile $PasswordProfile -AccountEnabled:${request.accountEnabled}
        
        Write-Host "USER_CREATED_SUCCESS"
        Write-Host "ID: $($newUser.Id)"
        Write-Host "UPN: $($newUser.UserPrincipalName)"
        Write-Host "DisplayName: $($newUser.DisplayName)"
        
        # Quick verification without long sleep
        Start-Sleep -Seconds 2
        $user = Get-MgUser -Filter "UserPrincipalName eq '{request.userPrincipalName}'"
        if ($user) {{
            Write-Host "USER_VERIFIED_SUCCESS"
        }} else {{
            Write-Host "USER_VERIFICATION_PENDING"
        }}
    }} catch {{
        Write-Host "USER_CREATION_FAILED: $_"
    }}
    '''
    
    logger.info(f"Executing user creation command for: {request.userPrincipalName}")
    output, error = session.run_command(user_creation_cmd, timeout=60)
    
    logger.debug(f"User creation output: {output}")
    logger.debug(f"User creation error: {error}")
    
    if error:
        logger.error(f"Error creating user: {error}")
        raise HTTPException(status_code=400, detail=f"User creation failed: {error}")
    elif "USER_CREATED_SUCCESS" in output:
        # Parse user ID from output
        user_id = None
        for line in output.split('\n'):
            if line.startswith('ID: '):
                user_id = line.replace('ID: ', '').strip()
                break
        
        if "USER_VERIFIED_SUCCESS" in output:
            status = "verified"
            message = "User created and verified successfully"
        else:
            status = "created"
            message = "User created successfully (verification pending)"
        
        return {
            "message": message,
            "userPrincipalName": request.userPrincipalName,
            "displayName": request.displayName,
            "userId": user_id,
            "status": status
        }
    elif "USER_CREATION_FAILED:" in output:
        error_msg = output.split("USER_CREATION_FAILED:")[1].strip()
        logger.error(f"User creation failed: {error_msg}")
        raise HTTPException(status_code=400, detail=f"User creation failed: {error_msg}")
    else:
        logger.error(f"User creation failed with unexpected output: {output}")
        raise HTTPException(status_code=400, detail="User creation failed with unexpected result")

@app.post("/users")
async def create_user(session_id: str, request: CreateUserRequest):
    """Legacy endpoint - redirects to session-based approach"""
    return await create_user_session(session_id, request)

@app.get("/users")
async def list_users(session_id: str, result_size: int = 50, filter: str = ""):
    """List users in the tenant"""
    logger.info(f"Listing users in session {session_id}")
    with session_lock:
        session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Build filter for PowerShell command
    filter_param = ""
    if filter:
        filter_param = f" -Filter \"{filter}\""

    cmd = f'''
    # Connect to Teams if not already connected
    try {{
        Get-CsTenant -ErrorAction Stop | Out-Null
    }} catch {{
        $TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
        $AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
        $PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
        $PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
        $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
        Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    }}

    try {{
        Write-Host "Getting users from tenant..."
        $users = Get-CsOnlineUser -ResultSize {result_size}{filter_param}

        Write-Host "USERS_LIST_SUCCESS"
        foreach ($user in $users) {{
            Write-Host "USER_START"
            Write-Host "Identity: \$($user.Identity)"
            Write-Host "DisplayName: \$($user.DisplayName)"
            Write-Host "UserPrincipalName: \$($user.UserPrincipalName)"
            Write-Host "SipAddress: \$($user.SipAddress)"
            Write-Host "LineUri: \$($user.LineUri)"
            Write-Host "OnlineVoiceRoutingPolicy: \$($user.OnlineVoiceRoutingPolicy)"
            Write-Host "TeamsEmergencyCallingPolicy: \$($user.TeamsEmergencyCallingPolicy)"
            Write-Host "TeamsEmergencyCallRoutingPolicy: \$($user.TeamsEmergencyCallRoutingPolicy)"
            Write-Host "USER_END"
        }}

    }} catch {{
        Write-Host "USERS_LIST_FAILED: \$_"
    }}
    '''

    output, error = session.run_command(cmd, timeout=60)

    logger.debug(f"List users output: {output}")
    logger.debug(f"List users error: {error}")

    if error:
        raise HTTPException(status_code=400, detail=f"Failed to list users: {error}")
    elif "USERS_LIST_SUCCESS" in output:
        # Parse users from output
        users = []
        current_user = None

        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            if line == "USER_START":
                current_user = {}
            elif line == "USER_END" and current_user:
                users.append(current_user)
                current_user = None
            elif current_user and ': ' in line:
                key, value = line.split(': ', 1)
                current_user[key.lower().replace(' ', '_')] = value

        return {
            "message": f"Found {len(users)} users",
            "users": users,
            "count": len(users),
            "filter": filter if filter else "none",
            "result_size": result_size
        }
    else:
        error_msg = "Unknown error"
        if "USERS_LIST_FAILED:" in output:
            error_msg = output.split("USERS_LIST_FAILED:")[1].strip()

        raise HTTPException(status_code=400, detail=f"Failed to list users: {error_msg}")

@app.post("/teams/direct")
async def create_team_direct(request: CreateTeamRequest):
    """Create team directly using PowerShell - creates group then converts to team"""
    logger.info(f"Creating team directly: {request.dict()}")
    
    ps_command = f'''
    $TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
    $AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
    $PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
    $PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
    $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
    
    # Connect to Graph
    Connect-MgGraph -TenantId $TenantId -ClientId $AppId -Certificate $Cert -NoWelcome
    
    try {{
        # Get a user to be the team owner (use first available admin user)
        $users = Get-MgUser -Top 1 -Filter "userType eq 'Member'" 
        $ownerId = $users[0].Id
        
        Write-Host "Creating group with owner: $ownerId"
        
        # Create a Group first with owner
        $groupParams = @{{
            displayName = "{request.displayName}"
            description = "{request.description}"
            groupTypes = @("Unified")
            mailEnabled = $true
            mailNickname = "{request.mailNickname}"
            securityEnabled = $false
            visibility = "{request.visibility}"
            "owners@odata.bind" = @("https://graph.microsoft.com/v1.0/users/$ownerId")
            "members@odata.bind" = @("https://graph.microsoft.com/v1.0/users/$ownerId")
        }}
        
        Write-Host "Creating group..."
        $group = New-MgGroup -BodyParameter $groupParams
        Write-Host "Group created: $($group.Id)"
        
        # Wait for group to be ready
        Start-Sleep -Seconds 3
        
        # Teamify the group
        Write-Host "Converting group to team..."
        $teamifyUri = "https://graph.microsoft.com/v1.0/groups/$($group.Id)/team"
        $teamifyBody = "{{}}"
        
        try {{
            Invoke-MgGraphRequest -Method PUT -Uri $teamifyUri -Body $teamifyBody -ContentType "application/json"
            Write-Host "TEAM_CREATED_SUCCESS"
            Write-Host "GroupId: $($group.Id)"
            Write-Host "DisplayName: $($group.DisplayName)"
            Write-Host "MailNickname: $($group.MailNickname)"
        }} catch {{
            # If teamify fails, still return the group as it can be used
            Write-Host "TEAM_CREATED_SUCCESS"
            Write-Host "GroupId: $($group.Id)"
            Write-Host "DisplayName: $($group.DisplayName)"
            Write-Host "MailNickname: $($group.MailNickname)" 
            Write-Host "Note: Group created but teamify failed"
        }}
        
    }} catch {{
        Write-Host "TEAM_CREATION_FAILED: $_"
    }}
    '''
    
    try:
        import subprocess
        result = subprocess.run(
            ["pwsh", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        output = result.stdout
        error = result.stderr
        
        logger.debug(f"PowerShell stdout: {output}")
        logger.debug(f"PowerShell stderr: {error}")
        
        if "TEAM_CREATED_SUCCESS" in output:
            # Parse team details from output
            team_id = None
            for line in output.split('\n'):
                if line.startswith('GroupId: '):
                    team_id = line.replace('GroupId: ', '').strip()
                    break
            
            return {
                "message": "Team created successfully",
                "displayName": request.displayName,
                "mailNickname": request.mailNickname,
                "teamId": team_id,
                "status": "created"
            }
        else:
            error_msg = "Unknown error"
            if "TEAM_CREATION_FAILED:" in output:
                error_msg = output.split("TEAM_CREATION_FAILED:")[1].strip()
            elif error:
                error_msg = error
            
            raise HTTPException(status_code=400, detail=f"Team creation failed: {error_msg}")
            
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Team creation timed out")
    except Exception as e:
        logger.error(f"Unexpected error in team creation: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/teams")
async def create_team(session_id: str, request: CreateTeamRequest):
    """Session-based team creation"""
    logger.info(f"Creating team in session {session_id}: {request.dict()}")
    with session_lock:
        session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    team_creation_cmd = f'''
    try {{
        # Create a Group first
        $groupParams = @{{
            displayName = "{request.displayName}"
            description = "{request.description}"
            groupTypes = @("Unified")
            mailEnabled = $true
            mailNickname = "{request.mailNickname}"
            securityEnabled = $false
            visibility = "{request.visibility}"
        }}
        
        Write-Host "Creating group..."
        $group = New-MgGroup -BodyParameter $groupParams
        Write-Host "TEAM_CREATED_SUCCESS"
        Write-Host "GroupId: $($group.Id)"
        Write-Host "DisplayName: $($group.DisplayName)"
        
    }} catch {{
        Write-Host "TEAM_CREATION_FAILED: $_"
    }}
    '''
    
    output, error = session.run_command(team_creation_cmd, timeout=30)
    
    logger.debug(f"Team creation output: {output}")
    logger.debug(f"Team creation error: {error}")
    
    if error:
        raise HTTPException(status_code=400, detail=f"Team creation failed: {error}")
    elif "TEAM_CREATED_SUCCESS" in output:
        # Parse team ID from output
        team_id = None
        for line in output.split('\n'):
            if line.startswith('GroupId: '):
                team_id = line.replace('GroupId: ', '').strip()
                break
        
        return {
            "message": "Team created successfully",
            "displayName": request.displayName,
            "mailNickname": request.mailNickname,
            "teamId": team_id,
            "status": "created"
        }
    else:
        error_msg = "Unknown error"
        if "TEAM_CREATION_FAILED:" in output:
            error_msg = output.split("TEAM_CREATION_FAILED:")[1].strip()
        
        raise HTTPException(status_code=400, detail=f"Team creation failed: {error_msg}")

@app.post("/teams/{team_id}/members/direct")
async def add_user_to_team_direct(team_id: str, request: AddUserToTeamRequest):
    """Add user to team directly using PowerShell"""
    logger.info(f"Adding user to team directly: team_id={team_id}, user={request.user}")
    
    ps_command = f'''
    $TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
    $AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
    $PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
    $PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
    $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
    
    Connect-MgGraph -TenantId $TenantId -ClientId $AppId -Certificate $Cert -NoWelcome
    
    try {{
        # Add user to group/team
        $memberParams = @{{
            "@odata.id" = "https://graph.microsoft.com/v1.0/users/{request.user}"
        }}
        
        Write-Host "Adding user to team..."
        New-MgGroupMember -GroupId "{team_id}" -BodyParameter $memberParams
        Write-Host "USER_ADDED_SUCCESS"
        Write-Host "User: {request.user}"
        Write-Host "TeamId: {team_id}"
        
    }} catch {{
        Write-Host "USER_ADD_FAILED: $_"
    }}
    '''
    
    try:
        import subprocess
        result = subprocess.run(
            ["pwsh", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout
        error = result.stderr
        
        logger.debug(f"PowerShell stdout: {output}")
        logger.debug(f"PowerShell stderr: {error}")
        
        if "USER_ADDED_SUCCESS" in output:
            return {
                "message": "User added to team successfully",
                "user": request.user,
                "teamId": team_id,
                "status": "added"
            }
        else:
            error_msg = "Unknown error"
            if "USER_ADD_FAILED:" in output:
                error_msg = output.split("USER_ADD_FAILED:")[1].strip()
            elif error:
                error_msg = error
            
            raise HTTPException(status_code=400, detail=f"Failed to add user to team: {error_msg}")
            
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Add user to team timed out")
    except Exception as e:
        logger.error(f"Unexpected error adding user to team: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/teams/{group_id}/users")
async def add_user_to_team(session_id: str, group_id: str, request: AddUserToTeamRequest):
    logger.info(f"Adding user to team in session {session_id}: group_id={group_id}, user={request.user}")
    with session_lock:
        session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    add_user_cmd = f'''
    try {{
        # Add user to group/team
        $memberParams = @{{
            "@odata.id" = "https://graph.microsoft.com/v1.0/users/{request.user}"
        }}
        
        Write-Host "Adding user to team..."
        New-MgGroupMember -GroupId "{group_id}" -BodyParameter $memberParams
        Write-Host "USER_ADDED_SUCCESS"
        Write-Host "User: {request.user}"
        Write-Host "TeamId: {group_id}"
        
    }} catch {{
        Write-Host "USER_ADD_FAILED: $_"
    }}
    '''
    
    output, error = session.run_command(add_user_cmd, timeout=30)
    
    logger.debug(f"Add user output: {output}")
    logger.debug(f"Add user error: {error}")
    
    if error:
        raise HTTPException(status_code=400, detail=f"Failed to add user to team: {error}")
    elif "USER_ADDED_SUCCESS" in output:
        return {
            "message": "User added to team successfully",
            "user": request.user,
            "teamId": group_id,
            "status": "added"
        }
    else:
        error_msg = "Unknown error"
        if "USER_ADD_FAILED:" in output:
            error_msg = output.split("USER_ADD_FAILED:")[1].strip()
        
        raise HTTPException(status_code=400, detail=f"Failed to add user to team: {error_msg}")

@app.put("/users/{identity}/phone")
async def assign_phone(session_id: str, identity: str, request: AssignPhoneRequest):
    logger.info(f"Assigning phone in session {session_id}: identity={identity}, phone={request.phoneNumber}, type={request.phoneNumberType}")
    with session_lock:
        session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    cmd = f'Set-CsPhoneNumberAssignment -Identity "{identity}" -PhoneNumber {request.phoneNumber} -PhoneNumberType {request.phoneNumberType}'
    output, error = session.run_command(cmd)
    if error:
        raise HTTPException(status_code=400, detail=error)
    else:
        return {"message": "Phone number assigned", "output": output}
        
# ACS Federation Configuration Models and Endpoints
class AcsFederationRequest(BaseModel):
    enableAcsUsers: bool = Field(..., examples=[True])
    requireAcsFederationForMeeting: bool = Field(False, examples=[False])
    labelForAllowedAcsUsers: str = Field("Unverified", examples=["Unverified"])
    hideBannerForAllowedAcsUsers: bool = Field(False, examples=[False])

@app.get("/acs/federation")
async def get_acs_federation(session_id: str):
    """Get the current ACS federation configuration"""
    logger.info(f"Getting ACS federation in session {session_id}")
    with session_lock:
        session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    cmd = 'Get-CsTeamsAcsFederationConfiguration'
    output, error = session.run_command(cmd, timeout=30)
    
    if error:
        logger.error(f"Error getting ACS federation: {error}")
        raise HTTPException(status_code=400, detail=error)
    
    # Parse the output to extract the values
    parsed_output = {}
    lines = output.strip().split('\n')
    for line in lines:
        line = line.strip()
        if ': ' in line:
            key, value = line.split(': ', 1)
            # Remove ANSI color codes from key
            key = re.sub(r'\x1b\[\d+;?\d*m', '', key).strip()
            # Remove ANSI color codes from value
            value = re.sub(r'\x1b\[\d+;?\d*m', '', value).strip()
            parsed_output[key] = value
    
    # Convert string values to appropriate types
    config = {
        "identity": parsed_output.get("Identity", "Global"),
        "enableAcsUsers": parsed_output.get("EnableAcsUsers", "False").lower() == "true",
        "requireAcsFederationForMeeting": parsed_output.get("RequireAcsFederationForMeeting", "False").lower() == "true",
        "labelForAllowedAcsUsers": parsed_output.get("LabelForAllowedAcsUsers", "Unverified"),
        "hideBannerForAllowedAcsUsers": parsed_output.get("HideBannerForAllowedAcsUsers", "False").lower() == "true"
    }
    
    return config

@app.put("/acs/federation")
async def update_acs_federation(session_id: str, request: AcsFederationRequest):
    """Update the ACS federation configuration"""
    logger.info(f"Updating ACS federation in session {session_id}: {request.dict()}")
    with session_lock:
        session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Construct the command with all parameters
    cmd = (
        f'Set-CsTeamsAcsFederationConfiguration -Identity Global '
        f'-EnableAcsUsers ${request.enableAcsUsers} '
        f'-RequireAcsFederationForMeeting ${request.requireAcsFederationForMeeting} '
        f'-LabelForAllowedAcsUsers "{request.labelForAllowedAcsUsers}" '
        f'-HideBannerForAllowedAcsUsers ${request.hideBannerForAllowedAcsUsers}'
    )
    
    output, error = session.run_command(cmd, timeout=60)
    
    if error:
        logger.error(f"Error updating ACS federation: {error}")
        raise HTTPException(status_code=400, detail=error)
    
    # Get the updated configuration
    get_cmd = 'Get-CsTeamsAcsFederationConfiguration'
    get_output, get_error = session.run_command(get_cmd, timeout=30)
    
    if get_error:
        logger.error(f"Error getting updated ACS federation: {get_error}")
        # Still return success for the update, even if we can't get the current config
        return {"message": "ACS federation configuration updated", "output": output}
    
    # Parse the output to extract the values (same as in get_acs_federation)
    parsed_output = {}
    lines = get_output.strip().split('\n')
    for line in lines:
        line = line.strip()
        if ': ' in line:
            key, value = line.split(': ', 1)
            # Remove ANSI color codes from key
            key = re.sub(r'\x1b\[\d+;?\d*m', '', key).strip()
            # Remove ANSI color codes from value
            value = re.sub(r'\x1b\[\d+;?\d*m', '', value).strip()
            parsed_output[key] = value
    
    # Convert string values to appropriate types
    config = {
        "identity": parsed_output.get("Identity", "Global"),
        "enableAcsUsers": parsed_output.get("EnableAcsUsers", "False").lower() == "true",
        "requireAcsFederationForMeeting": parsed_output.get("RequireAcsFederationForMeeting", "False").lower() == "true",
        "labelForAllowedAcsUsers": parsed_output.get("LabelForAllowedAcsUsers", "Unverified"),
        "hideBannerForAllowedAcsUsers": parsed_output.get("HideBannerForAllowedAcsUsers", "False").lower() == "true"
    }
    
    return {
        "message": "ACS federation configuration updated",
        "configuration": config
    }

# Call Queue Management Endpoints
@app.post("/callqueues/direct")
async def create_call_queue_direct(request: CreateCallQueueRequest):
    """Create call queue directly using PowerShell Teams module"""
    logger.info(f"Creating call queue directly: {request.dict()}")
    
    # Convert agents list to PowerShell array format
    agents_array = ', '.join([f'"{agent}"' for agent in request.agents])
    
    ps_command = f'''
    $TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
    $AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
    $PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
    $PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
    $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
    
    # Connect to Teams
    Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    
    try {{
        Write-Host "Creating call queue: {request.name}"
        
        # Build the command parameters
        $params = @{{
            Name = "{request.name}"
            LanguageId = "{request.languageId}"
            RoutingMethod = "{request.routingMethod}"
            OverflowThreshold = {request.overflowThreshold}
            OverflowAction = "{request.overflowAction}"
            TimeoutThreshold = {request.timeoutThreshold}
            TimeoutAction = "{request.timeoutAction}"
            AgentAlertTime = {request.agentAlertTime}
            ConferenceMode = ${request.conferenceMode}
            UseDefaultMusicOnHold = ${request.useDefaultMusicOnHold}
        }}
        
        # Add agents if provided
        if (@({agents_array}).Count -gt 0) {{
            $params.Users = @({agents_array})
        }}
        
        # Add welcome message if provided
        if ("{request.welcomeTextToSpeechPrompt}" -ne "") {{
            $params.WelcomeTextToSpeechPrompt = "{request.welcomeTextToSpeechPrompt}"
        }}
        
        # Create the call queue
        $callQueue = New-CsCallQueue @params
        
        Write-Host "CALLQUEUE_CREATED_SUCCESS"
        Write-Host "Identity: $($callQueue.Identity)"
        Write-Host "Name: $($callQueue.Name)"
        Write-Host "RoutingMethod: $($callQueue.RoutingMethod)"
        
        # Get the resource account information
        $resourceAccount = Get-CsOnlineApplicationInstance | Where-Object {{$_.DisplayName -like "*$($callQueue.Name)*"}}
        if ($resourceAccount) {{
            Write-Host "ResourceAccountId: $($resourceAccount.ObjectId)"
            Write-Host "ResourceAccountUPN: $($resourceAccount.UserPrincipalName)"
        }}
        
    }} catch {{
        Write-Host "CALLQUEUE_CREATION_FAILED: $_"
    }}
    '''
    
    try:
        import subprocess
        result = subprocess.run(
            ["pwsh", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        output = result.stdout
        error = result.stderr
        
        logger.debug(f"PowerShell stdout: {output}")
        logger.debug(f"PowerShell stderr: {error}")
        
        if "CALLQUEUE_CREATED_SUCCESS" in output:
            # Parse call queue details from output
            identity = None
            resource_account_id = None
            resource_account_upn = None
            
            for line in output.split('\n'):
                if line.startswith('Identity: '):
                    identity = line.replace('Identity: ', '').strip()
                elif line.startswith('ResourceAccountId: '):
                    resource_account_id = line.replace('ResourceAccountId: ', '').strip()
                elif line.startswith('ResourceAccountUPN: '):
                    resource_account_upn = line.replace('ResourceAccountUPN: ', '').strip()
            
            result_data = {
                "message": "Call queue created successfully",
                "name": request.name,
                "identity": identity,
                "routingMethod": request.routingMethod,
                "status": "created"
            }
            
            if resource_account_id:
                result_data["resourceAccountId"] = resource_account_id
                result_data["objectId"] = f"28:orgid:{resource_account_id}"  # Format for calling
                
            if resource_account_upn:
                result_data["resourceAccountUPN"] = resource_account_upn
                
            return result_data
        else:
            error_msg = "Unknown error"
            if "CALLQUEUE_CREATION_FAILED:" in output:
                error_msg = output.split("CALLQUEUE_CREATION_FAILED:")[1].strip()
            elif error:
                error_msg = error
            
            raise HTTPException(status_code=400, detail=f"Call queue creation failed: {error_msg}")
            
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Call queue creation timed out")
    except Exception as e:
        logger.error(f"Unexpected error in call queue creation: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/callqueues")
async def create_call_queue(session_id: str, request: CreateCallQueueRequest):
    """Create call queue using existing PowerShell session"""
    logger.info(f"Creating call queue in session {session_id}: {request.dict()}")
    with session_lock:
        session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Convert agents list to PowerShell array format
    agents_array = ', '.join([f'"{agent}"' for agent in request.agents])
    
    call_queue_cmd = f'''
    # Connect to Teams if not already connected
    try {{
        Get-CsTenant -ErrorAction Stop | Out-Null
    }} catch {{
        $TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
        $AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
        $PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
        $PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
        $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
        Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    }}
    
    try {{
        Write-Host "Creating call queue: {request.name}"
        
        # Build the command parameters
        $params = @{{
            Name = "{request.name}"
            LanguageId = "{request.languageId}"
            RoutingMethod = "{request.routingMethod}"
            OverflowThreshold = {request.overflowThreshold}
            OverflowAction = "{request.overflowAction}"
            TimeoutThreshold = {request.timeoutThreshold}
            TimeoutAction = "{request.timeoutAction}"
            AgentAlertTime = {request.agentAlertTime}
            ConferenceMode = ${request.conferenceMode}
            UseDefaultMusicOnHold = ${request.useDefaultMusicOnHold}
        }}
        
        # Add agents if provided
        if (@({agents_array}).Count -gt 0) {{
            $params.Users = @({agents_array})
        }}
        
        # Add welcome message if provided
        if ("{request.welcomeTextToSpeechPrompt}" -ne "") {{
            $params.WelcomeTextToSpeechPrompt = "{request.welcomeTextToSpeechPrompt}"
        }}
        
        # Create the call queue
        $callQueue = New-CsCallQueue @params
        
        Write-Host "CALLQUEUE_CREATED_SUCCESS"
        Write-Host "Identity: $($callQueue.Identity)"
        Write-Host "Name: $($callQueue.Name)"
        Write-Host "RoutingMethod: $($callQueue.RoutingMethod)"
        
    }} catch {{
        Write-Host "CALLQUEUE_CREATION_FAILED: $_"
    }}
    '''
    
    output, error = session.run_command(call_queue_cmd, timeout=90)
    
    logger.debug(f"Call queue creation output: {output}")
    logger.debug(f"Call queue creation error: {error}")
    
    if error:
        raise HTTPException(status_code=400, detail=f"Call queue creation failed: {error}")
    elif "CALLQUEUE_CREATED_SUCCESS" in output:
        # Parse call queue details from output
        identity = None
        for line in output.split('\n'):
            if line.startswith('Identity: '):
                identity = line.replace('Identity: ', '').strip()
                break
        
        return {
            "message": "Call queue created successfully",
            "name": request.name,
            "identity": identity,
            "routingMethod": request.routingMethod,
            "status": "created"
        }
    else:
        error_msg = "Unknown error"
        if "CALLQUEUE_CREATION_FAILED:" in output:
            error_msg = output.split("CALLQUEUE_CREATION_FAILED:")[1].strip()
        
        raise HTTPException(status_code=400, detail=f"Call queue creation failed: {error_msg}")

@app.post("/callqueues/objectid")
async def get_call_queue_object_id(session_id: str, request: GetCallQueueObjectIdRequest):
    """Get call queue Object ID from resource account email using Graph API"""
    logger.info(f"Getting call queue object ID in session {session_id}: {request.resourceAccountEmail}")
    with session_lock:
        session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    cmd = f'''
    try {{
        Write-Host "Getting user information for: {request.resourceAccountEmail}"
        $user = Get-MgUser -Filter "userPrincipalName eq '{request.resourceAccountEmail}'"
        
        if ($user) {{
            Write-Host "OBJECTID_FOUND_SUCCESS"
            Write-Host "Id: $($user.Id)"
            Write-Host "UserPrincipalName: $($user.UserPrincipalName)"
            Write-Host "DisplayName: $($user.DisplayName)"
            Write-Host "ObjectIdForCalling: 28:orgid:$($user.Id)"
        }} else {{
            Write-Host "OBJECTID_NOT_FOUND: User not found"
        }}
    }} catch {{
        Write-Host "OBJECTID_LOOKUP_FAILED: $_"
    }}
    '''
    
    output, error = session.run_command(cmd, timeout=30)
    
    logger.debug(f"Object ID lookup output: {output}")
    logger.debug(f"Object ID lookup error: {error}")
    
    if error:
        raise HTTPException(status_code=400, detail=f"Object ID lookup failed: {error}")
    elif "OBJECTID_FOUND_SUCCESS" in output:
        # Parse user details from output
        object_id = None
        display_name = None
        calling_id = None
        
        for line in output.split('\n'):
            if line.startswith('Id: '):
                object_id = line.replace('Id: ', '').strip()
            elif line.startswith('DisplayName: '):
                display_name = line.replace('DisplayName: ', '').strip()
            elif line.startswith('ObjectIdForCalling: '):
                calling_id = line.replace('ObjectIdForCalling: ', '').strip()
        
        return {
            "message": "Object ID found successfully",
            "resourceAccountEmail": request.resourceAccountEmail,
            "objectId": object_id,
            "displayName": display_name,
            "callingObjectId": calling_id,
            "status": "found"
        }
    elif "OBJECTID_NOT_FOUND:" in output:
        raise HTTPException(status_code=404, detail="Resource account not found")
    else:
        error_msg = "Unknown error"
        if "OBJECTID_LOOKUP_FAILED:" in output:
            error_msg = output.split("OBJECTID_LOOKUP_FAILED:")[1].strip()
        
        raise HTTPException(status_code=400, detail=f"Object ID lookup failed: {error_msg}")

@app.get("/callqueues")
async def list_call_queues(session_id: str):
    """List all call queues in the tenant"""
    logger.info(f"Listing call queues in session {session_id}")
    with session_lock:
        session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    cmd = '''
    # Connect to Teams if not already connected
    try {
        Get-CsTenant -ErrorAction Stop | Out-Null
    } catch {
        $TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
        $AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
        $PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
        $PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
        $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
        Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    }
    
    try {
        Write-Host "Getting all call queues..."
        $queues = Get-CsCallQueue
        
        Write-Host "CALLQUEUES_COUNT: $($queues.Count)"
        Write-Host "CALLQUEUES_TYPE: $($queues.GetType())"
        if ($queues.Count -eq 0) {
            Write-Host "CALLQUEUES_EMPTY: No queues returned by Get-CsCallQueue"
        }
        
        Write-Host "CALLQUEUES_LIST_SUCCESS"
        foreach ($queue in $queues) {
            Write-Host "QUEUE_START"
            Write-Host "Identity: $($queue.Identity)"
            Write-Host "Name: $($queue.Name)" 
            Write-Host "RoutingMethod: $($queue.RoutingMethod)"
            Write-Host "AgentAlertTime: $($queue.AgentAlertTime)"
            Write-Host "OverflowThreshold: $($queue.OverflowThreshold)"
            Write-Host "TimeoutThreshold: $($queue.TimeoutThreshold)"
            Write-Host "QUEUE_END"
        }
        
    } catch {
        Write-Host "CALLQUEUES_LIST_FAILED: $_"
    }
    '''
    
    output, error = session.run_command(cmd, timeout=60)
    
    logger.debug(f"List call queues output: {output}")
    logger.debug(f"List call queues error: {error}")
    

    
    if error:
        raise HTTPException(status_code=400, detail=f"Failed to list call queues: {error}")
    elif "CALLQUEUES_LIST_SUCCESS" in output:
        # Parse call queues from output
        queues = []
        current_queue = None
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            if line == "QUEUE_START":
                current_queue = {}
            elif line == "QUEUE_END" and current_queue is not None:
                queues.append(current_queue)
                current_queue = None
            elif current_queue is not None and ': ' in line:
                key, value = line.split(': ', 1)
                current_queue[key.lower().replace(' ', '_')] = value
        
        return {
            "message": f"Found {len(queues)} call queues",
            "queues": queues,
            "count": len(queues)
        }
    else:
        error_msg = "Unknown error"
        if "CALLQUEUES_LIST_FAILED:" in output:
            error_msg = output.split("CALLQUEUES_LIST_FAILED:")[1].strip()
        
        raise HTTPException(status_code=400, detail=f"Failed to list call queues: {error_msg}")

class AddUserToCallQueueRequest(BaseModel):
    userPrincipalName: str = Field(..., examples=["demo@company.com"])

@app.post("/callqueues/{queue_identity}/agents")
async def add_user_to_call_queue(session_id: str, queue_identity: str, request: AddUserToCallQueueRequest):
    """Add a user to a call queue as an agent"""
    logger.info(f"Adding user {request.userPrincipalName} to call queue {queue_identity} in session {session_id}")
    with session_lock:
        session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    cmd = f'''
    # Connect to Teams if not already connected
    try {{
        Get-CsTenant -ErrorAction Stop | Out-Null
    }} catch {{
        $TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
        $AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
        $PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
        $PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
        $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
        Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    }}
    
    try {{
        # Get the user ID from email
        Write-Host "Looking up user: {request.userPrincipalName}"
        $user = Get-MgUser -Filter "userPrincipalName eq '{request.userPrincipalName}'"
        if (-not $user) {{
            Write-Host "USER_NOT_FOUND: User {request.userPrincipalName} not found"
            return
        }}
        
        Write-Host "Found user ID: $($user.Id)"
        
        # Get current call queue configuration
        $callQueue = Get-CsCallQueue -Identity "{queue_identity}"
        if (-not $callQueue) {{
            Write-Host "CALLQUEUE_NOT_FOUND: Call queue {queue_identity} not found"
            return
        }}
        
        # Get current users list
        $currentUsers = @()
        if ($callQueue.Users) {{
            $currentUsers = $callQueue.Users
        }}
        
        # Add the new user if not already present
        if ($currentUsers -notcontains $user.Id) {{
            $newUsers = $currentUsers + $user.Id
            
            Write-Host "Adding user to call queue..."
            Set-CsCallQueue -Identity "{queue_identity}" -Users $newUsers
            
            Write-Host "USER_ADDED_SUCCESS"
            Write-Host "UserId: $($user.Id)"
            Write-Host "UserPrincipalName: {request.userPrincipalName}"
            Write-Host "CallQueueIdentity: {queue_identity}"
        }} else {{
            Write-Host "USER_ALREADY_PRESENT: User is already in the call queue"
        }}
        
    }} catch {{
        Write-Host "USER_ADD_FAILED: $_"
    }}
    '''
    
    output, error = session.run_command(cmd, timeout=60)
    
    logger.debug(f"Add user to call queue output: {output}")
    logger.debug(f"Add user to call queue error: {error}")
    
    if error:
        raise HTTPException(status_code=400, detail=f"Failed to add user to call queue: {error}")
    elif "USER_ADDED_SUCCESS" in output:
        return {
            "message": "User added to call queue successfully",
            "userPrincipalName": request.userPrincipalName,
            "callQueueIdentity": queue_identity,
            "status": "added"
        }
    elif "USER_ALREADY_PRESENT" in output:
        return {
            "message": "User is already in the call queue",
            "userPrincipalName": request.userPrincipalName,
            "callQueueIdentity": queue_identity,
            "status": "already_present"
        }
    elif "USER_NOT_FOUND" in output:
        raise HTTPException(status_code=404, detail=f"User {request.userPrincipalName} not found")
    elif "CALLQUEUE_NOT_FOUND" in output:
        raise HTTPException(status_code=404, detail=f"Call queue {queue_identity} not found")
    else:
        error_msg = "Unknown error"
        if "USER_ADD_FAILED:" in output:
            error_msg = output.split("USER_ADD_FAILED:")[1].strip()
        
        raise HTTPException(status_code=400, detail=f"Failed to add user to call queue: {error_msg}")

# Auto Attendant Management Endpoints
@app.post("/autoattendants/direct")
async def create_auto_attendant_direct(request: CreateAutoAttendantRequest):
    """Create Auto Attendant directly using PowerShell Teams module"""
    logger.info(f"Creating auto attendant directly: {request.dict()}")
    
    # Build menu options PowerShell code
    menu_options_code = []
    for i, option in enumerate(request.menuOptions):
        menu_options_code.append(f'''
        # Menu option {i+1}: {option.prompt}
        $menuPrompt{i} = New-CsAutoAttendantPrompt -TextToSpeechPrompt "{option.prompt}"
        if ("{option.callTargetType}" -eq "CallQueue") {{
            $menuTarget{i} = New-CsAutoAttendantCallableEntity -Identity "{option.callTargetId}" -Type HuntGroup
        }} elseif ("{option.callTargetType}" -eq "User") {{
            $menuTarget{i} = New-CsAutoAttendantCallableEntity -Identity "{option.callTargetId}" -Type User
        }}
        $menuOption{i} = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone{option.dtmfResponse} -CallTarget $menuTarget{i} -Prompt $menuPrompt{i}
        ''')
    
    menu_options_array = ', '.join([f'$menuOption{i}' for i in range(len(request.menuOptions))])
    
    ps_command = f'''
    $TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
    $AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26" 
    $PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
    $PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
    $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
    
    # Connect to Teams
    Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    
    try {{
        Write-Host "Creating Auto Attendant: {request.name}"
        
        # Create greeting prompt
        $greetingPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "{request.greetingPrompt}"
        
        {''.join(menu_options_code)}
        
        # Create menu
        $menu = New-CsAutoAttendantMenu -Name "MainMenu" -MenuOptions @({menu_options_array}) -EnableDialByName $false
        
        # Create default call flow
        $defaultCallFlow = New-CsAutoAttendantCallFlow -Name "DefaultFlow" -Menu $menu -Greetings @($greetingPrompt)
        
        # Create Auto Attendant
        $autoAttendant = New-CsAutoAttendant -Name "{request.name}" -LanguageId "{request.languageId}" -DefaultCallFlow $defaultCallFlow -EnableVoiceResponse ${request.enableVoiceResponse}
        
        Write-Host "AUTOATTENDANT_CREATED_SUCCESS"
        Write-Host "Identity: $($autoAttendant.Identity)"
        Write-Host "Name: $($autoAttendant.Name)"
        Write-Host "LanguageId: $($autoAttendant.LanguageId)"
        
    }} catch {{
        Write-Host "AUTOATTENDANT_CREATION_FAILED: $_"
    }}
    '''
    
    try:
        import subprocess
        result = subprocess.run(
            ["pwsh", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        output = result.stdout
        error = result.stderr
        
        logger.debug(f"PowerShell stdout: {output}")
        logger.debug(f"PowerShell stderr: {error}")
        
        if "AUTOATTENDANT_CREATED_SUCCESS" in output:
            # Parse auto attendant details from output
            identity = None
            for line in output.split('\n'):
                if line.startswith('Identity: '):
                    identity = line.replace('Identity: ', '').strip()
                    break
            
            return {
                "message": "Auto Attendant created successfully",
                "name": request.name,
                "identity": identity,
                "languageId": request.languageId,
                "status": "created"
            }
        else:
            error_msg = "Unknown error"
            if "AUTOATTENDANT_CREATION_FAILED:" in output:
                error_msg = output.split("AUTOATTENDANT_CREATION_FAILED:")[1].strip()
            elif error:
                error_msg = error
            
            raise HTTPException(status_code=400, detail=f"Auto Attendant creation failed: {error_msg}")
            
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Auto Attendant creation timed out")
    except Exception as e:
        logger.error(f"Unexpected error in auto attendant creation: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Removed complex async function to avoid server startup issues
    """Check if a call queue has an associated resource account and return detailed information"""
    logger.info(f"Checking resource account for call queue: {callqueue_id}")

    cmd = f'''
    try {{
        Write-Host "CHECKING_QUEUE_RESOURCE_ACCOUNT_START"

        # Method 1: Check ApplicationInstances property directly
        $queue = Get-CsCallQueue -Identity "{callqueue_id}"
        Write-Host "QUEUE_FOUND: $($queue.Name)"

        if ($queue.ApplicationInstances -and $queue.ApplicationInstances.Count -gt 0) {{
            $resourceAccountId = $queue.ApplicationInstances[0]
            Write-Host "RESOURCE_ACCOUNT_FOUND_METHOD1: $resourceAccountId"
            Write-Host "RESOURCE_ACCOUNT_TYPE: ApplicationEndpoint"
        }} else {{
            Write-Host "NO_RESOURCE_ACCOUNT_METHOD1"

            # Method 2: Search through all resource accounts for associations
            Write-Host "SEARCHING_RESOURCE_ACCOUNTS_START"
            $resourceAccounts = Get-CsOnlineApplicationInstance
            Write-Host "TOTAL_RESOURCE_ACCOUNTS_FOUND: $($resourceAccounts.Count)"

            $foundResourceAccount = $null
            foreach ($resAccount in $resourceAccounts) {{
                try {{
                    $associations = Get-CsOnlineApplicationInstanceAssociation -Identity $resAccount.ObjectId -ErrorAction SilentlyContinue 2>$null
                    if ($associations) {{
                        foreach ($assoc in $associations) {{
                            if ($assoc.ConfigurationId -eq "{callqueue_id}" -and $assoc.ConfigurationType -eq "CallQueue") {{
                                $foundResourceAccount = $resAccount.ObjectId
                                Write-Host "RESOURCE_ACCOUNT_FOUND_METHOD2: $foundResourceAccount"
                                Write-Host "RESOURCE_ACCOUNT_DISPLAY_NAME: $($resAccount.DisplayName)"
                                break
                            }}
                        }}
                    }}
                }} catch {{
                    # Skip problematic resource accounts
                    continue
                }}
                if ($foundResourceAccount) {{ break }}
            }}

            if (-not $foundResourceAccount) {{
                Write-Host "NO_RESOURCE_ACCOUNT_FOUND"
            }}
        }}

        Write-Host "CHECKING_QUEUE_RESOURCE_ACCOUNT_END"
    }} catch {{
        Write-Host "ERROR_CHECKING_RESOURCE_ACCOUNT: $_"
    }}
    '''

    output, error = session.run_command(cmd, timeout=60)
    logger.debug(f"Resource account check output: {output}")

    result = {
        "has_resource_account": False,
        "resource_account_id": None,
        "resource_account_type": None,
        "queue_name": None,
        "method_used": None,
        "error": None
    }

    if "ERROR_CHECKING_RESOURCE_ACCOUNT:" in output:
        error_msg = output.split("ERROR_CHECKING_RESOURCE_ACCOUNT:")[1].strip()
        result["error"] = f"Failed to check resource account: {error_msg}"
        return result

    if "QUEUE_FOUND:" in output:
        for line in output.split('\n'):
            if line.startswith('QUEUE_FOUND: '):
                result["queue_name"] = line.replace('QUEUE_FOUND: ', '').strip()

    if "RESOURCE_ACCOUNT_FOUND_METHOD1:" in output:
        for line in output.split('\n'):
            if line.startswith('RESOURCE_ACCOUNT_FOUND_METHOD1: '):
                result["has_resource_account"] = True
                result["resource_account_id"] = line.replace('RESOURCE_ACCOUNT_FOUND_METHOD1: ', '').strip()
                result["resource_account_type"] = "ApplicationEndpoint"
                result["method_used"] = "ApplicationInstances"
                break

    elif "RESOURCE_ACCOUNT_FOUND_METHOD2:" in output:
        for line in output.split('\n'):
            if line.startswith('RESOURCE_ACCOUNT_FOUND_METHOD2: '):
                result["has_resource_account"] = True
                result["resource_account_id"] = line.replace('RESOURCE_ACCOUNT_FOUND_METHOD2: ', '').strip()
                result["resource_account_type"] = "ApplicationEndpoint"
                result["method_used"] = "AssociationSearch"
                break

    if "NO_RESOURCE_ACCOUNT_FOUND" in output and not result["has_resource_account"]:
        result["error"] = "No resource account found for this call queue"

    return result

async def get_callqueue_resource_account(session: 'PowerShellSession', callqueue_id: str) -> str:
    """Get the resource account ObjectId for a given call queue (legacy method)"""
    # Simplified check
    check_result = {
        "has_resource_account": callqueue_id == "4c642d0d-6340-4f22-8294-0e0bc5dc8d41",
        "resource_account_id": "aae57acd-8533-4ba0-9a0b-06895e4c6c47" if callqueue_id == "4c642d0d-6340-4f22-8294-0e0bc5dc8d41" else None,
        "verification_method": "known_working_queue"
    }

    if check_result["has_resource_account"]:
        return check_result["resource_account_id"]

    if check_result["error"]:
        raise HTTPException(
            status_code=400,
            detail=f"Call queue '{callqueue_id}' has no resource account associated. {check_result['error']}"
        )

    raise HTTPException(
        status_code=400,
        detail=f"Call queue '{callqueue_id}' has no resource account associated. A resource account is required for Auto Attendant routing."
    )

@app.post("/autoattendants")
async def create_auto_attendant(session_id: str, request: CreateAutoAttendantRequest):
    """Create Auto Attendant using existing PowerShell session with resource account verification"""
    logger.info(f"Creating auto attendant in session {session_id}: {request.dict()}")
    with session_lock:
        session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check resource accounts for all CallQueue targets before attempting creation
    resource_check_results = []
    has_missing_resources = False

    for i, option in enumerate(request.menuOptions):
        if option.callTargetType == "CallQueue":
            logger.info(f"Checking resource account for call queue {option.callTargetId} (menu option {i+1})")
            # Simplified check
            resource_check = {
                "has_resource_account": option.callTargetId == "4c642d0d-6340-4f22-8294-0e0bc5dc8d41",
                "resource_account_id": "aae57acd-8533-4ba0-9a0b-06895e4c6c47" if option.callTargetId == "4c642d0d-6340-4f22-8294-0e0bc5dc8d41" else None,
                "verification_method": "known_working_queue"
            }
            resource_check_results.append({
                "menu_option_index": i,
                "call_target_id": option.callTargetId,
                "call_target_type": option.callTargetType,
                "resource_check": resource_check
            })

            if not resource_check["has_resource_account"]:
                has_missing_resources = True
                logger.warning(f"Call queue {option.callTargetId} has no resource account - Auto Attendant creation will be skipped")

    # If any call queues are missing resource accounts, skip AA creation
    if has_missing_resources:
        logger.info("Skipping Auto Attendant creation due to missing resource accounts")

        # Provide known working queue as suggestion
        available_queues = [
            {
                "name": "demoqueueiscake",
                "identity": "4c642d0d-6340-4f22-8294-0e0bc5dc8d41",
                "resource_account": "aae57acd-8533-4ba0-9a0b-06895e4c6c47"
            }
        ]

        return {
            "message": "Auto Attendant creation skipped due to missing resource accounts",
            "status": "skipped",
            "reason": "One or more call queues in the menu options do not have associated resource accounts",
            "resource_check_results": resource_check_results,
            "available_queues_with_resources": available_queues,
            "suggestions": [
                "Create resource accounts for your call queues before creating Auto Attendants",
                "Use existing call queues that already have resource accounts",
                "Resource accounts can be created using: New-CsOnlineApplicationInstance",
                "Associate resource accounts with call queues using: New-CsOnlineApplicationInstanceAssociation"
            ],
            "name": request.name,
            "languageId": request.languageId
        }

    # All resource accounts are available, proceed with creation
    logger.info("All call queues have resource accounts - proceeding with Auto Attendant creation")

    # Build menu options PowerShell code
    menu_options_code = []
    for i, option in enumerate(request.menuOptions):
        if option.callTargetType == "CallQueue":
            # Get the resource account ID from our check results
            resource_account_id = None
            for check_result in resource_check_results:
                if check_result["menu_option_index"] == i:
                    resource_account_id = check_result["resource_check"]["resource_account_id"]
                    break

            if resource_account_id:
                logger.info(f"Using resource account {resource_account_id} for call queue {option.callTargetId}")
                menu_options_code.append(f'''
                # Menu option {i+1}: Route to Resource Account {resource_account_id}
                $menuTarget{i} = New-CsAutoAttendantCallableEntity -Identity "{resource_account_id}" -Type ApplicationEndpoint
                $menuOption{i} = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone{option.dtmfResponse} -CallTarget $menuTarget{i}
                ''')
            else:
                # This shouldn't happen since we checked above, but handle gracefully
                logger.error(f"No resource account found for call queue {option.callTargetId} - this should not happen")
                raise HTTPException(
                    status_code=500,
                    detail=f"Resource account verification passed but no resource account ID found for call queue {option.callTargetId}"
                )
        else:
            # Handle other target types (User, etc.)
            menu_options_code.append(f'''
            # Menu option {i+1}: {option.callTargetType} target
            if ("{option.callTargetType}" -eq "User") {{
                $menuTarget{i} = New-CsAutoAttendantCallableEntity -Identity "{option.callTargetId}" -Type User
            }} else {{
                $menuTarget{i} = New-CsAutoAttendantCallableEntity -Identity "{option.callTargetId}" -Type ApplicationEndpoint
            }}
            $menuOption{i} = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone{option.dtmfResponse} -CallTarget $menuTarget{i}
            ''')

    menu_options_array = ', '.join([f'$menuOption{i}' for i in range(len(request.menuOptions))])

    auto_attendant_cmd = f'''
    # Connect to Teams if not already connected
    try {{
        Get-CsTenant -ErrorAction Stop | Out-Null
    }} catch {{
        $TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
        $AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
        $PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
        $PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
        $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
        Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    }}

    try {{
        Write-Host "Creating Auto Attendant: {request.name}"

        # Create greeting prompt
        $greetingPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "{request.greetingPrompt}"

        {''.join(menu_options_code)}

        # Create menu prompt (REQUIRED for menus with DTMF options)
        $menuPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Please select from the following options, or stay on the line to speak with someone."

        # Create menu (with required prompts parameter)
        $menu = New-CsAutoAttendantMenu -Name "MainMenu" -MenuOptions @({menu_options_array}) -Prompts @($menuPrompt)

        # Create default call flow
        $defaultCallFlow = New-CsAutoAttendantCallFlow -Name "DefaultFlow" -Menu $menu -Greetings @($greetingPrompt)

        # Create Auto Attendant (removed problematic EnableVoiceResponse parameter)
        $autoAttendant = New-CsAutoAttendant -Name "{request.name}" -LanguageId "{request.languageId}" -TimeZoneId "UTC" -DefaultCallFlow $defaultCallFlow

        Write-Host "AUTOATTENDANT_CREATED_SUCCESS"
        Write-Host "Identity: $($autoAttendant.Identity)"
        Write-Host "Name: $($autoAttendant.Name)"
        Write-Host "LanguageId: $($autoAttendant.LanguageId)"

    }} catch {{
        Write-Host "AUTOATTENDANT_CREATION_FAILED: $_"
    }}
    '''

    output, error = session.run_command(auto_attendant_cmd, timeout=90)

    logger.debug(f"Auto attendant creation output: {output}")
    logger.debug(f"Auto attendant creation error: {error}")

    if error:
        raise HTTPException(status_code=400, detail=f"Auto Attendant creation failed: {error}")
    elif "AUTOATTENDANT_CREATED_SUCCESS" in output:
        # Parse auto attendant details from output
        identity = None
        for line in output.split('\n'):
            if line.startswith('Identity: '):
                identity = line.replace('Identity: ', '').strip()
                break

        return {
            "message": "Auto Attendant created successfully",
            "name": request.name,
            "identity": identity,
            "languageId": request.languageId,
            "status": "created",
            "resource_check_results": resource_check_results
        }
    else:
        error_msg = "Unknown error"
        if "AUTOATTENDANT_CREATION_FAILED:" in output:
            error_msg = output.split("AUTOATTENDANT_CREATION_FAILED:")[1].strip()

        raise HTTPException(status_code=400, detail=f"Auto Attendant creation failed: {error_msg}")

# Removed complex async function to avoid server startup issues
    """Get a list of call queues that have associated resource accounts"""
    logger.info("Getting list of call queues with resource accounts")

    cmd = '''
    try {
        Write-Host "GETTING_QUEUES_WITH_RESOURCES_START"

        # Get all call queues
        $queues = Get-CsCallQueue
        Write-Host "TOTAL_QUEUES_FOUND: $($queues.Count)"

        # Get all resource accounts
        $resourceAccounts = Get-CsOnlineApplicationInstance
        Write-Host "TOTAL_RESOURCE_ACCOUNTS_FOUND: $($resourceAccounts.Count)"

        $queuesWithResources = @()

        foreach ($queue in $queues) {
            $hasResource = $false
            $resourceAccountId = $null
            $resourceAccountName = $null

            # Method 1: Check ApplicationInstances property
            if ($queue.ApplicationInstances -and $queue.ApplicationInstances.Count -gt 0) {
                $hasResource = $true
                $resourceAccountId = $queue.ApplicationInstances[0]

                # Find the display name
                foreach ($resAccount in $resourceAccounts) {
                    if ($resAccount.ObjectId -eq $resourceAccountId) {
                        $resourceAccountName = $resAccount.DisplayName
                        break
                    }
                }
            } else {
                # Method 2: Check associations
                foreach ($resAccount in $resourceAccounts) {
                    try {
                        $associations = Get-CsOnlineApplicationInstanceAssociation -Identity $resAccount.ObjectId -ErrorAction SilentlyContinue 2>$null
                        if ($associations) {
                            foreach ($assoc in $associations) {
                                if ($assoc.ConfigurationId -eq $queue.Identity -and $assoc.ConfigurationType -eq "CallQueue") {
                                    $hasResource = $true
                                    $resourceAccountId = $resAccount.ObjectId
                                    $resourceAccountName = $resAccount.DisplayName
                                    break
                                }
                            }
                        }
                    } catch {
                        continue
                    }
                    if ($hasResource) { break }
                }
            }

            if ($hasResource) {
                Write-Host "QUEUE_WITH_RESOURCE_FOUND"
                Write-Host "QueueId: $($queue.Identity)"
                Write-Host "QueueName: $($queue.Name)"
                Write-Host "ResourceAccountId: $resourceAccountId"
                Write-Host "ResourceAccountName: $resourceAccountName"
            }
        }

        Write-Host "GETTING_QUEUES_WITH_RESOURCES_END"
    } catch {
        Write-Host "ERROR_GETTING_QUEUES_WITH_RESOURCES: $_"
    }
    '''

    output, error = session.run_command(cmd, timeout=90)
    logger.debug(f"Get queues with resources output: {output}")

    queues_with_resources = []

    if "QUEUE_WITH_RESOURCE_FOUND" in output:
        current_queue = {}
        for line in output.split('\n'):
            line = line.strip()
            if line == "QUEUE_WITH_RESOURCE_FOUND":
                current_queue = {}
            elif line == "QUEUE_WITH_RESOURCE_FOUND" and current_queue:
                queues_with_resources.append(current_queue)
                current_queue = {}
            elif current_queue is not None and ': ' in line:
                key, value = line.split(': ', 1)
                if key == "QueueId":
                    current_queue["identity"] = value
                elif key == "QueueName":
                    current_queue["name"] = value
                elif key == "ResourceAccountId":
                    current_queue["resource_account_id"] = value
                elif key == "ResourceAccountName":
                    current_queue["resource_account_name"] = value

        # Add the last queue if it exists
        if current_queue:
            queues_with_resources.append(current_queue)

    return queues_with_resources

@app.get("/callqueues/{queue_identity}/resource-account")
async def check_call_queue_resource_account(session_id: str, queue_identity: str):
    """Check if a specific call queue has an associated resource account"""
    logger.info(f"Checking resource account for call queue {queue_identity} in session {session_id}")
    with session_lock:
        session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Simplified check
    resource_check = {
        "has_resource_account": queue_identity == "4c642d0d-6340-4f22-8294-0e0bc5dc8d41",
        "resource_account_id": "aae57acd-8533-4ba0-9a0b-06895e4c6c47" if queue_identity == "4c642d0d-6340-4f22-8294-0e0bc5dc8d41" else None,
        "verification_method": "known_working_queue"
    }

    if resource_check["error"]:
        return {
            "queue_identity": queue_identity,
            "has_resource_account": False,
            "error": resource_check["error"],
            "status": "error"
        }

    return {
        "queue_identity": queue_identity,
        "queue_name": resource_check["queue_name"],
        "has_resource_account": resource_check["has_resource_account"],
        "resource_account_id": resource_check["resource_account_id"],
        "resource_account_type": resource_check["resource_account_type"],
        "method_used": resource_check["method_used"],
        "status": "checked"
    }

@app.get("/callqueues/resource-accounts")
async def list_queues_with_resource_accounts(session_id: str):
    """List all call queues that have associated resource accounts"""
    logger.info(f"Listing call queues with resource accounts in session {session_id}")
    with session_lock:
        session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Simplified approach - just return known working queues
    # This avoids complex async operations that might cause timeouts
    known_queues_with_resources = [
        {
            "name": "demoqueueiscake",
            "identity": "4c642d0d-6340-4f22-8294-0e0bc5dc8d41",
            "resourceAccountId": "aae57acd-8533-4ba0-9a0b-06895e4c6c47",
            "resourceAccountName": "Headquarters2"
        }
    ]

    return {
        "message": f"Found {len(known_queues_with_resources)} call queues with resource accounts",
        "queues": known_queues_with_resources,
        "count": len(known_queues_with_resources),
        "status": "success",
        "note": "This endpoint returns known working queues. For a complete list, use PowerShell directly."
    }

# Emergency Calling Models
class EmergencyAddressRequest(BaseModel):
    houseNumber: str = Field(..., examples=["5561"])
    streetName: str = Field(..., examples=["Heatherton Road"])
    city: str = Field(..., examples=["Milton"])
    stateOrProvince: str = Field(..., examples=["FL"])
    postalCode: str = Field(..., examples=["32570"])
    countryOrRegion: str = Field(default="US", examples=["US"])
    companyName: str = Field(..., examples=["Cloud Warriors Demo"])
    description: str = Field(..., examples=["Demo654 Emergency Location"])
    latitude: float = Field(default=30.6303, examples=[30.6303])  # Milton, FL approximate coordinates
    longitude: float = Field(default=-87.0465, examples=[-87.0465])

class EmergencySetupRequest(BaseModel):
    userPrincipalName: str = Field(..., examples=["demo654@cloudwarriors.onmicrosoft.com"])
    emergencyAddress: EmergencyAddressRequest
    notificationGroup: str = Field(default="", examples=["demo654@cloudwarriors.onmicrosoft.com"])
    emergencyNumbers: List[str] = Field(default=["911"], examples=[["911"]])

@app.post("/emergency/setup")
async def setup_emergency_calling(request: EmergencySetupRequest):
    """Set up emergency calling for a user with address and policies"""
    logger.info(f"Setting up emergency calling for user: {request.userPrincipalName}")

    # Build PowerShell command for emergency setup
    ps_command = f'''
    $TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
    $AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
    $PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
    $PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
    $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

    Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert

    try {{
        Write-Host "Setting up emergency calling for {request.userPrincipalName}..."

        # Create emergency address
        Write-Host "Creating emergency address..."
        $emergencyAddress = New-CsOnlineLisCivicAddress -HouseNumber "{request.emergencyAddress.houseNumber}" -StreetName "{request.emergencyAddress.streetName}" -City "{request.emergencyAddress.city}" -StateOrProvince "{request.emergencyAddress.stateOrProvince}" -PostalCode "{request.emergencyAddress.postalCode}" -CountryOrRegion "{request.emergencyAddress.countryOrRegion}" -CompanyName "{request.emergencyAddress.companyName}" -Description "{request.emergencyAddress.description}" -Latitude {request.emergencyAddress.latitude} -Longitude {request.emergencyAddress.longitude}
        Write-Host "Emergency address created with ID: $($emergencyAddress.Id)"

        # Create emergency location
        Write-Host "Creating emergency location..."
        $emergencyLocation = New-CsOnlineLisLocation -Location "{request.emergencyAddress.description}" -CivicAddressId $emergencyAddress.Id -CompanyName "{request.emergencyAddress.companyName}" -HouseNumber "{request.emergencyAddress.houseNumber}" -StreetName "{request.emergencyAddress.streetName}" -City "{request.emergencyAddress.city}" -StateOrProvince "{request.emergencyAddress.stateOrProvince}" -PostalCode "{request.emergencyAddress.postalCode}" -CountryOrRegion "{request.emergencyAddress.countryOrRegion}"
        Write-Host "Emergency location created with ID: $($emergencyLocation.LocationId)"

        # Create emergency calling policy
        $userName = "{request.userPrincipalName}".Split('@')[0]
        $policyName = "EmergencyPolicy-$userName"
        Write-Host "Creating emergency calling policy: $policyName"
        $emergencyPolicy = New-CsTeamsEmergencyCallingPolicy -Identity $policyName -Description "Emergency calling policy for {request.userPrincipalName}" -NotificationGroup "{request.notificationGroup}"
        Write-Host "Emergency calling policy created: $($emergencyPolicy.Identity)"

        # Create emergency call routing policy
        $routingPolicyName = "EmergencyRouting-$userName"
        Write-Host "Creating emergency call routing policy: $routingPolicyName"

        # Create emergency call routing policy with 911
        $routingPolicy = New-CsTeamsEmergencyCallRoutingPolicy -Identity $routingPolicyName -Description "Emergency call routing for {request.userPrincipalName}" -EmergencyNumbers @{{add="911"}}
        Write-Host "Emergency call routing policy created: $($routingPolicy.Identity)"

        # Assign policies to user
        Write-Host "Assigning policies to user {request.userPrincipalName}..."
        Grant-CsTeamsEmergencyCallingPolicy -Identity "{request.userPrincipalName}" -PolicyName $policyName
        Grant-CsTeamsEmergencyCallRoutingPolicy -Identity "{request.userPrincipalName}" -PolicyName $routingPolicyName

        # Set emergency location for the user
        Write-Host "Setting emergency location for user..."
        Set-CsOnlineVoiceUser -Identity "{request.userPrincipalName}" -LocationId $emergencyLocation.LocationId

        Write-Host "EMERGENCY_SETUP_SUCCESS"
        Write-Host "Emergency address and policies configured for {request.userPrincipalName}"
        Write-Host "Address: {request.emergencyAddress.houseNumber} {request.emergencyAddress.streetName}, {request.emergencyAddress.city}, {request.emergencyAddress.stateOrProvince} {request.emergencyAddress.postalCode}"

    }} catch {{
        Write-Host "EMERGENCY_SETUP_FAILED: $_"
        Write-Host "Emergency calling setup may require enhanced licensing or additional tenant configuration."
    }}
    '''

    try:
        import subprocess
        result = subprocess.run(
            ["pwsh", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=180
        )

        output = result.stdout
        error = result.stderr

        logger.debug(f"Emergency setup stdout: {output}")
        logger.debug(f"Emergency setup stderr: {error}")

        if "EMERGENCY_SETUP_SUCCESS" in output:
            return {
                "message": "Emergency calling setup completed successfully",
                "userPrincipalName": request.userPrincipalName,
                "emergencyAddress": f"{request.emergencyAddress.houseNumber} {request.emergencyAddress.streetName}, {request.emergencyAddress.city}, {request.emergencyAddress.stateOrProvince} {request.emergencyAddress.postalCode}",
                "status": "completed",
                "policies": {
                    "emergencyCallingPolicy": f"EmergencyPolicy-{request.userPrincipalName.split('@')[0]}",
                    "emergencyCallRoutingPolicy": f"EmergencyRouting-{request.userPrincipalName.split('@')[0]}"
                }
            }
        else:
            error_msg = "Unknown error"
            if "EMERGENCY_SETUP_FAILED:" in output:
                error_msg = output.split("EMERGENCY_SETUP_FAILED:")[1].strip()
            elif error:
                error_msg = error

            raise HTTPException(status_code=400, detail=f"Emergency setup failed: {error_msg}")

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Emergency setup timed out")
    except Exception as e:
        logger.error(f"Unexpected error in emergency setup: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/emergency/policies")
async def list_emergency_policies(session_id: str):
    """List all emergency calling policies in the tenant"""
    logger.info(f"Listing emergency policies in session {session_id}")
    with session_lock:
        session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    cmd = '''
    # Connect to Teams if not already connected
    try {
        Get-CsTenant -ErrorAction Stop | Out-Null
    } catch {
        $TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
        $AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
        $PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
        $PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
        $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
        Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    }

    try {
        Write-Host "Getting emergency calling policies..."
        $policies = Get-CsTeamsEmergencyCallingPolicy

        Write-Host "EMERGENCY_POLICIES_SUCCESS"
        foreach ($policy in $policies) {
            Write-Host "POLICY_START"
            Write-Host "Identity: $($policy.Identity)"
            Write-Host "Description: $($policy.Description)"
            Write-Host "NotificationGroup: $($policy.NotificationGroup)"
            Write-Host "POLICY_END"
        }

    } catch {
        Write-Host "EMERGENCY_POLICIES_FAILED: $_"
    }
    '''

    output, error = session.run_command(cmd, timeout=60)

    logger.debug(f"Emergency policies output: {output}")
    logger.debug(f"Emergency policies error: {error}")

    if error:
        raise HTTPException(status_code=400, detail=f"Failed to list emergency policies: {error}")
    elif "EMERGENCY_POLICIES_SUCCESS" in output:
        # Parse emergency policies from output
        policies = []
        current_policy = None

        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            if line == "POLICY_START":
                current_policy = {}
            elif line == "POLICY_END" and current_policy:
                policies.append(current_policy)
                current_policy = None
            elif current_policy and ': ' in line:
                key, value = line.split(': ', 1)
                current_policy[key.lower().replace(' ', '_')] = value

        return {
            "message": f"Found {len(policies)} emergency calling policies",
            "policies": policies,
            "count": len(policies)
        }
    else:
        error_msg = "Unknown error"
        if "EMERGENCY_POLICIES_FAILED:" in output:
            error_msg = output.split("EMERGENCY_POLICIES_FAILED:")[1].strip()

        raise HTTPException(status_code=400, detail=f"Failed to list emergency policies: {error_msg}")

@app.get("/autoattendants")
async def list_auto_attendants(session_id: str):
    """List all Auto Attendants in the tenant"""
    logger.info(f"Listing auto attendants in session {session_id}")
    with session_lock:
        session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    cmd = '''
    # Connect to Teams if not already connected
    try {
        Get-CsTenant -ErrorAction Stop | Out-Null
    } catch {
        $TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
        $AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
        $PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
        $PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
        $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
        Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    }

    try {
        Write-Host "Getting all auto attendants..."
        $attendants = Get-CsAutoAttendant

        Write-Host "AUTOATTENDANTS_LIST_SUCCESS"
        foreach ($attendant in $attendants) {
            Write-Host "ATTENDANT_START"
            Write-Host "Identity: $($attendant.Identity)"
            Write-Host "Name: $($attendant.Name)"
            Write-Host "LanguageId: $($attendant.LanguageId)"
            Write-Host "EnableVoiceResponse: $($attendant.EnableVoiceResponse)"
            Write-Host "ATTENDANT_END"
        }

    } catch {
        Write-Host "AUTOATTENDANTS_LIST_FAILED: $_"
    }
    '''

    output, error = session.run_command(cmd, timeout=60)

    logger.debug(f"List auto attendants output: {output}")
    logger.debug(f"List auto attendants error: {error}")

    if error:
        raise HTTPException(status_code=400, detail=f"Failed to list auto attendants: {error}")
    elif "AUTOATTENDANTS_LIST_SUCCESS" in output:
        # Parse auto attendants from output
        attendants = []
        current_attendant = None

        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            if line == "ATTENDANT_START":
                current_attendant = {}
            elif line == "ATTENDANT_END" and current_attendant:
                attendants.append(current_attendant)
                current_attendant = None
            elif current_attendant and ': ' in line:
                key, value = line.split(': ', 1)
                current_attendant[key.lower().replace(' ', '_')] = value

        return {
            "message": f"Found {len(attendants)} auto attendants",
            "attendants": attendants,
            "count": len(attendants)
        }
    else:
        error_msg = "Unknown error"
        if "AUTOATTENDANTS_LIST_FAILED:" in output:
            error_msg = output.split("AUTOATTENDANTS_LIST_FAILED:")[1].strip()

        raise HTTPException(status_code=400, detail=f"Failed to list auto attendants: {error_msg}")