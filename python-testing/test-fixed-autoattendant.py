#!/usr/bin/env python3
"""
Test the fixed Auto Attendant creation directly
"""
import subprocess
import json

def test_autoattendant_creation():
    """Test Auto Attendant creation with the corrected PowerShell syntax"""
    
    # This is the corrected PowerShell command with all fixes applied
    powershell_cmd = '''
    # Connect to Teams
    $TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
    $AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
    $PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
    $PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
    $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
    Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    
    try {
        Write-Host "Creating Auto Attendant: APITestAA"
        
        # Create greeting prompt
        $greetingPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Welcome to our company. Please listen to the following menu options."
        
        # Create menu option for call queue routing (using hardcoded working resource account)
        $menuTarget1 = New-CsAutoAttendantCallableEntity -Identity "aae57acd-8533-4ba0-9a0b-06895e4c6c47" -Type ApplicationEndpoint
        $menuOption1 = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone1 -CallTarget $menuTarget1
        
        # Create menu prompt (REQUIRED - this was the missing piece!)
        $menuPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Press 1 to connect to our support team, or stay on the line to speak with an operator."
        
        # Create menu (with required prompts parameter - no EnableDialByName issues)
        $menu = New-CsAutoAttendantMenu -Name "MainMenu" -MenuOptions @($menuOption1) -Prompts @($menuPrompt)
        
        # Create default call flow
        $defaultCallFlow = New-CsAutoAttendantCallFlow -Name "DefaultFlow" -Menu $menu -Greetings @($greetingPrompt)
        
        # Create Auto Attendant (removed problematic EnableVoiceResponse parameter)
        $autoAttendant = New-CsAutoAttendant -Name "APITestAA-$(Get-Date -Format 'yyyyMMdd-HHmmss')" -LanguageId "en-US" -TimeZoneId "UTC" -DefaultCallFlow $defaultCallFlow
        
        Write-Host "AUTOATTENDANT_CREATED_SUCCESS"
        Write-Host "Identity: $($autoAttendant.Identity)"
        Write-Host "Name: $($autoAttendant.Name)"
        Write-Host "LanguageId: $($autoAttendant.LanguageId)"
        Write-Host "Status: Created and ready for use"
        
    } catch {
        Write-Host "AUTOATTENDANT_CREATION_FAILED: $_"
        Write-Host "Error details: $($_.Exception.Message)"
    }
    '''
    
    print("🧪 Testing Fixed Auto Attendant Creation...")
    print("=" * 60)
    
    # Run the PowerShell command
    try:
        result = subprocess.run(
            ["pwsh", "-Command", powershell_cmd],
            capture_output=True,
            text=True,
            timeout=120,
            cwd="/root/code/teams-sdk"
        )
        
        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        print(f"\nReturn code: {result.returncode}")
        
        if "AUTOATTENDANT_CREATED_SUCCESS" in result.stdout:
            print("\n🎉 SUCCESS! Auto Attendant creation is now WORKING!")
            print("✅ Fixed the PowerShell parameter issues")
            print("✅ Added required menu prompts")
            print("✅ Removed problematic parameters")
            print("✅ Ready for API integration")
        else:
            print("\n❌ Still having issues - needs further debugging")
            
    except subprocess.TimeoutExpired:
        print("❌ Test timed out after 2 minutes")
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")

if __name__ == "__main__":
    test_autoattendant_creation()