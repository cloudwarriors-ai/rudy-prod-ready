import requests
import json
import time
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("test_acs_api")

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_acs_federation():
    """Test the ACS federation endpoints"""
    logger.info("Testing ACS federation endpoints")
    
    # Step 1: Connect to the API and get a session ID
    logger.info("Step 1: Creating authenticated session")
    response = requests.post(f"{BASE_URL}/auth/connect")
    if response.status_code != 200:
        logger.error(f"Failed to connect: {response.text}")
        return False
    
    session_data = response.json()
    session_id = session_data.get("session_id")
    logger.info(f"Session created: {session_id}")
    
    # Step 2: Get the current ACS federation configuration
    logger.info("Step 2: Getting current ACS federation configuration")
    response = requests.get(f"{BASE_URL}/acs/federation?session_id={session_id}")
    if response.status_code != 200:
        logger.error(f"Failed to get ACS federation: {response.text}")
        return False
    
    current_config = response.json()
    logger.info(f"Current configuration: {json.dumps(current_config, indent=2)}")
    
    # Step 3: Update the ACS federation configuration
    logger.info("Step 3: Updating ACS federation configuration")
    
    # Toggle the enableAcsUsers value
    enable_acs_users = not current_config.get("enableAcsUsers", True)
    
    update_data = {
        "enableAcsUsers": enable_acs_users,
        "requireAcsFederationForMeeting": False,
        "labelForAllowedAcsUsers": "TestLabel",
        "hideBannerForAllowedAcsUsers": False
    }
    
    response = requests.put(
        f"{BASE_URL}/acs/federation?session_id={session_id}",
        json=update_data
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to update ACS federation: {response.text}")
        return False
    
    updated_config = response.json()
    logger.info(f"Updated configuration: {json.dumps(updated_config, indent=2)}")
    
    # Step 4: Verify the change
    logger.info("Step 4: Verifying the change")
    response = requests.get(f"{BASE_URL}/acs/federation?session_id={session_id}")
    if response.status_code != 200:
        logger.error(f"Failed to get updated ACS federation: {response.text}")
        return False
    
    verify_config = response.json()
    logger.info(f"Verification configuration: {json.dumps(verify_config, indent=2)}")
    
    # Check if the update was successful
    if verify_config.get("enableAcsUsers") != enable_acs_users:
        logger.error("Update verification failed - enableAcsUsers didn't change")
        return False
    
    if verify_config.get("labelForAllowedAcsUsers") != "TestLabel":
        logger.error("Update verification failed - labelForAllowedAcsUsers didn't change")
        return False
    
    # Step 5: Restore the original configuration
    logger.info("Step 5: Restoring original configuration")
    restore_data = {
        "enableAcsUsers": current_config.get("enableAcsUsers", True),
        "requireAcsFederationForMeeting": current_config.get("requireAcsFederationForMeeting", False),
        "labelForAllowedAcsUsers": current_config.get("labelForAllowedAcsUsers", "Unverified"),
        "hideBannerForAllowedAcsUsers": current_config.get("hideBannerForAllowedAcsUsers", False)
    }
    
    response = requests.put(
        f"{BASE_URL}/acs/federation?session_id={session_id}",
        json=restore_data
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to restore ACS federation: {response.text}")
        return False
    
    restore_config = response.json()
    logger.info(f"Restored configuration: {json.dumps(restore_config, indent=2)}")
    
    # Step 6: Disconnect the session
    logger.info("Step 6: Disconnecting session")
    response = requests.post(f"{BASE_URL}/auth/disconnect?session_id={session_id}")
    if response.status_code != 200:
        logger.error(f"Failed to disconnect: {response.text}")
        return False
    
    logger.info("Session disconnected successfully")
    
    logger.info("ACS federation test completed successfully!")
    return True

if __name__ == "__main__":
    logger.info("Starting ACS federation API test")
    
    # Make sure the server is running
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code != 200:
            logger.error("Server is not running or not accessible")
            sys.exit(1)
        logger.info("Server is running")
    except Exception as e:
        logger.error(f"Error connecting to server: {e}")
        sys.exit(1)
    
    # Run the test
    success = test_acs_federation()
    
    if success:
        logger.info("Test passed!")
        sys.exit(0)
    else:
        logger.error("Test failed!")
        sys.exit(1)