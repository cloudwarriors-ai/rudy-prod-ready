#!/usr/bin/env python3
import subprocess
import logging
import time
import select

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_auth.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_auth")

class PowerShellTest:
    def __init__(self):
        logger.info("Initializing PowerShell session...")
        self.process = subprocess.Popen(
            ["pwsh", "-NoExit", "-Command", "Set-Location /root/code/teams-sdk"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        logger.info("PowerShell session initialized")
        
    def run_command(self, cmd, timeout=60, verbose=True):
        logger.info(f"Running command: {cmd}")
        self.process.stdin.write(cmd + "\n")
        self.process.stdin.flush()
        
        output = ""
        error = ""
        start = time.time()
        
        # Read until prompt or timeout
        while time.time() - start < timeout:
            ready = select.select([self.process.stdout, self.process.stderr], [], [], 0.1)
            if ready[0]:
                if self.process.stdout in ready[0]:
                    line = self.process.stdout.readline()
                    if verbose:
                        logger.info(f"STDOUT: {line.strip()}")
                    if "PS>" in line or line.strip() == "":
                        if verbose:
                            logger.info("Prompt detected, command completed")
                        break
                    output += line
                if self.process.stderr in ready[0]:
                    err_line = self.process.stderr.readline()
                    if verbose or err_line.strip():  # Always log non-empty stderr
                        logger.info(f"STDERR: {err_line.strip()}")
                    error += err_line
            
            if time.time() - start > timeout:
                logger.warning(f"Command timed out after {timeout} seconds")
                break
        
        logger.info(f"Command completed. Output length: {len(output)}, Error length: {len(error)}")
        return output, error
    
    def authenticate(self):
        logger.info("Authenticating with Microsoft Teams...")
        output, error = self.run_command(". ./connect.ps1")
        if error:
            logger.error(f"Authentication failed: {error}")
            return False
        logger.info(f"Authentication output: {output}")
        # Add a delay after authentication
        logger.info("Waiting 5 seconds after authentication...")
        time.sleep(5)
        return True
    
    def verify_connection(self):
        logger.info("Verifying connection...")
        # First run a simple command to ensure the session is responsive
        output, error = self.run_command("Get-Command -Name Get-CsTeamsAcsFederationConfiguration", verbose=True)
        if error:
            logger.error(f"Command verification failed: {error}")
            return False
        
        # Now run the actual command we want to verify
        output, error = self.run_command("Get-CsTeamsAcsFederationConfiguration", verbose=True)
        if error:
            logger.error(f"Connection verification failed: {error}")
            return False
        
        logger.info(f"Connection verification output: {output}")
        return len(output) > 0
    
    def create_test_user(self):
        timestamp = int(time.time())
        username = f"testuser{timestamp}"
        email = f"{username}@e7b105b2-720e-4b5b-9310-1a414c06356a.onmicrosoft.com"
        
        logger.info(f"Creating test user: {username} with email {email}")
        
        # Run a simple command first to check if PowerShell is working
        self.run_command("Write-Host 'PowerShell is ready'", timeout=10)
        
        # Run the New-MgUser command with a unique ID
        cmd = f'New-MgUser -AccountEnabled $true -DisplayName "Test User {timestamp}" -UserPrincipalName "{email}" -MailNickname "{username}" -PasswordProfile @{{ Password = "Test@P@ssw0rd123!"; ForceChangePasswordNextSignIn = $true }} | Format-List -Property Id,DisplayName,UserPrincipalName'
        
        output, error = self.run_command(cmd, timeout=120)
        
        if error:
            logger.error(f"User creation failed: {error}")
            return False, None
        
        logger.info(f"User creation output: {output}")
        
        # Verify user was created by trying to get the user
        verify_cmd = f'Get-MgUser -UserPrincipalName "{email}" | Format-List -Property Id,DisplayName,UserPrincipalName'
        verify_output, verify_error = self.run_command(verify_cmd, timeout=30)
        
        if verify_error:
            logger.error(f"User verification failed: {verify_error}")
            return False, None
            
        logger.info(f"User verification output: {verify_output}")
        
        if "UserPrincipalName" in verify_output and email in verify_output:
            return True, email
        else:
            logger.error("User verification failed: User not found")
            return False, None
    
    def close(self):
        logger.info("Closing PowerShell session")
        self.process.terminate()

def main():
    logger.info("Starting authentication test")
    ps = PowerShellTest()
    
    try:
        # Authenticate
        if not ps.authenticate():
            logger.error("Authentication failed")
            return
        
        logger.info("Authentication successful")
        
        # Verify connection
        if not ps.verify_connection():
            logger.error("Connection verification failed")
            return
        
        logger.info("Connection verification successful")
        
        # Create test user
        success, email = ps.create_test_user()
        if not success:
            logger.error("User creation failed")
            return
        
        logger.info(f"User created successfully: {email}")
        
    finally:
        ps.close()

if __name__ == "__main__":
    main()