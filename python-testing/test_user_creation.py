import unittest
import time
import sys
import logging
from app import PowerShellSession

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("test_user_creation")

class TestUserCreation(unittest.TestCase):
    """Test the PowerShell session and user creation functionality."""
    
    def setUp(self):
        """Set up the test environment."""
        self.session = PowerShellSession()
        self.session.authenticate()
        logger.info("PowerShell session initialized and authenticated")
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, 'session'):
            self.session.close()
            logger.info("PowerShell session closed")
    
    def test_user_creation(self):
        """Test creating a user with the correct parameters."""
        # Generate unique identifier for the test user
        timestamp = int(time.time())
        
        # User details
        user_domain = "cloudwarriors.onmicrosoft.com"
        display_name = f"TestUser{timestamp}"
        user_principal_name = f"testuser{timestamp}@{user_domain}"
        mail_nickname = f"testuser{timestamp}"
        password = "Test@P@ssw0rd123!"
        
        logger.info(f"Testing user creation with UPN: {user_principal_name}")
        
        # First check if the Microsoft Graph module is loaded
        logger.info("Checking if Microsoft Graph module is loaded...")
        check_cmd = 'Get-Module -Name Microsoft.Graph -ListAvailable | Format-List'
        check_output, check_error = self.session.run_command(check_cmd, timeout=30)
        logger.info(f"Module check output: {check_output}")
        if check_error:
            logger.error(f"Module check error: {check_error}")
        
        # Import the Microsoft Graph module if needed
        import_cmd = 'Import-Module Microsoft.Graph.Users -ErrorAction SilentlyContinue'
        import_output, import_error = self.session.run_command(import_cmd, timeout=30)
        logger.info(f"Module import output: {import_output}")
        if import_error:
            logger.error(f"Module import error: {import_error}")

        # Construct PowerShell command for user creation
        cmd = (
            f'New-MgUser -AccountEnabled:$true '
            f'-DisplayName "{display_name}" '
            f'-UserPrincipalName "{user_principal_name}" '
            f'-MailNickname "{mail_nickname}" '
            f'-PasswordProfile @{{ '
            f'Password = "{password}"; '
            f'ForceChangePasswordNextSignIn = $true '
            f'}} | Format-List -Property Id,DisplayName,UserPrincipalName'
        )
        
        # Execute command with longer timeout
        output, error = self.session.run_command(cmd, timeout=120)
        
        # Log the output and error
        logger.info(f"Command output: {output}")
        if error:
            logger.error(f"Command error: {error}")
        
        # Verify the result
        self.assertFalse(error, f"Error occurred during user creation: {error}")
        self.assertTrue("DisplayName" in output, "Expected DisplayName in output")
        self.assertTrue(display_name in output, f"Expected {display_name} in output")
        self.assertTrue(user_principal_name in output, f"Expected {user_principal_name} in output")
        
        # Now try to get the user to verify creation
        verify_cmd = f'Get-MgUser -Filter "UserPrincipalName eq \'{user_principal_name}\'" | Format-List -Property Id,DisplayName,UserPrincipalName'
        verify_output, verify_error = self.session.run_command(verify_cmd, timeout=60)
        
        logger.info(f"Verification output: {verify_output}")
        if verify_error:
            logger.error(f"Verification error: {verify_error}")
        
        # Verify the user exists
        self.assertFalse(verify_error, f"Error occurred during user verification: {verify_error}")
        self.assertTrue(display_name in verify_output, f"User {display_name} not found")
        self.assertTrue(user_principal_name in verify_output, f"User with UPN {user_principal_name} not found")

if __name__ == "__main__":
    unittest.main()