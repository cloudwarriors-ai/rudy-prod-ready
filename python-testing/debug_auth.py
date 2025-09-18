#!/usr/bin/env python3

import subprocess
import threading
import time
import select
import uuid

class TestPowerShellSession:
    def __init__(self):
        self.process = subprocess.Popen(
            ["pwsh", "-NoExit", "-Command", "Set-Location /root/code/teams-sdk"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self.authenticated = False
        print("PowerShell session started")

    def run_command(self, cmd, timeout=30):
        print(f"Running command: {cmd[:100]}...")
        
        # Clear any pending output
        while select.select([self.process.stdout, self.process.stderr], [], [], 0.1)[0]:
            if self.process.stdout in select.select([self.process.stdout], [], [], 0.1)[0]:
                self.process.stdout.readline()
            if self.process.stderr in select.select([self.process.stderr], [], [], 0.1)[0]:
                self.process.stderr.readline()
        
        # Add a unique marker to help identify command completion
        marker = f"CMD_COMPLETE_{int(time.time())}"
        full_cmd = f"{cmd}; Write-Host '{marker}'"
        
        # Send the command
        self.process.stdin.write(full_cmd + "\n")
        self.process.stdin.flush()
        
        output = ""
        error = ""
        marker_found = False
        
        # Read until marker or timeout
        start = time.time()
        marker_patterns = [marker, "PS /root/code/teams-sdk>", "PS>"]
        
        while time.time() - start < timeout and not marker_found:
            ready = select.select([self.process.stdout, self.process.stderr], [], [], 0.1)
            if ready[0]:
                if self.process.stdout in ready[0]:
                    line = self.process.stdout.readline()
                    print(f"STDOUT: {line.strip()}")
                    # Check for any completion pattern
                    if any(pattern in line for pattern in marker_patterns):
                        marker_found = True
                        break
                    # Skip the command echo line
                    if cmd in line and output == "":
                        continue
                    output += line
                if self.process.stderr in ready[0]:
                    stderr_line = self.process.stderr.readline()
                    print(f"STDERR: {stderr_line.strip()}")
                    error += stderr_line

        if not marker_found:
            print(f"Command timed out after {timeout} seconds")
        
        print(f"Command completed. Output length: {len(output)}, Error length: {len(error)}")
        return output, error

    def test_auth(self):
        print("Testing authentication...")
        
        # Test simple command first
        print("\n1. Testing simple command...")
        output, error = self.run_command("Get-Date", timeout=10)
        
        # Test Graph connection
        print("\n2. Testing Graph connection...")
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
        
        output, error = self.run_command(auth_cmd, timeout=60)
        
        # Check if we got the expected output
        if ("ClientId" in output and "TenantId" in output) or ("968fafbb-27b8-400a-b8c3-a90eb3c2de26" in output):
            print("✅ Authentication successful!")
            return True
        else:
            print("❌ Authentication failed")
            print(f"Output: {output}")
            print(f"Error: {error}")
            return False

    def close(self):
        self.process.terminate()

def main():
    session = TestPowerShellSession()
    
    try:
        success = session.test_auth()
        if success:
            print("\n3. Testing user creation...")
            # Test a quick user creation
            user_cmd = '''
            try {
                $PasswordProfile = @{
                    Password = "TestDebug@P@ssw0rd123!"
                    ForceChangePasswordNextSignIn = $true
                }
                
                Write-Host "Creating debug test user..."
                $newUser = New-MgUser -DisplayName "Debug Test User" -UserPrincipalName "debugtestuser@cloudwarriors.onmicrosoft.com" -MailNickname "debugtestuser" -PasswordProfile $PasswordProfile -AccountEnabled:$true
                
                Write-Host "USER_CREATED_SUCCESS"
                Write-Host "ID: $($newUser.Id)"
            } catch {
                Write-Host "USER_CREATION_FAILED: $_"
            }
            '''
            
            output, error = session.run_command(user_cmd, timeout=30)
            
            if "USER_CREATED_SUCCESS" in output:
                print("✅ User creation test successful!")
            else:
                print("❌ User creation test failed")
                
    finally:
        session.close()

if __name__ == "__main__":
    main()