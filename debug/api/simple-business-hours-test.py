#!/usr/bin/env python3

import subprocess
import sys
import os

def test_business_hours_powershell():
    """Test business hours implementation directly with PowerShell"""
    
    print("=== Direct PowerShell Business Hours Test ===")
    
    # Change to the teams-sdk directory
    os.chdir("/Users/work/teams-sdk")
    
    # PowerShell command with proper business hours implementation
    ps_script = '''
    # Auth setup
    $TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
    $AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
    $PfxPath = "/Users/work/teams-sdk/auth-keys/teamsfed.pfx"
    $PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
    $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
    
    Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    Write-Host "Connected to Teams"
    
    try {
        # Step 1: Create business hours time range
        $timeRange = New-CsOnlineTimeRange -Start 09:00 -End 17:00
        Write-Host "✅ Time range created"
        
        # Step 2: Create business hours schedule
        $scheduleName = "BH-Test-$(Get-Date -Format 'yyyyMMddHHmmss')"
        $schedule = New-CsOnlineSchedule -Name $scheduleName -WeeklyRecurrentSchedule -MondayHours @($timeRange) -TuesdayHours @($timeRange) -WednesdayHours @($timeRange) -ThursdayHours @($timeRange) -FridayHours @($timeRange)
        Write-Host "✅ Schedule created: $($schedule.Id)"
        
        # Step 3: Create prompts
        $businessGreeting = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Welcome. Our business hours are 9 AM to 5 PM, Monday through Friday."
        $afterHoursGreeting = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Thank you for calling. We are currently closed. Our business hours are 9 AM to 5 PM, Monday through Friday."
        Write-Host "✅ Prompts created"
        
        # Step 4: Create call flows
        $businessFlow = New-CsAutoAttendantCallFlow -Name "BusinessHoursFlow" -Greetings @($businessGreeting)
        $afterHoursFlow = New-CsAutoAttendantCallFlow -Name "AfterHoursFlow" -Greetings @($afterHoursGreeting)
        Write-Host "✅ Call flows created"
        
        # Step 5: Create Auto Attendant
        $aaName = "BusinessHours-Direct-Test-$(Get-Date -Format 'yyyyMMddHHmmss')"
        $aa = New-CsAutoAttendant -Name $aaName -LanguageId "en-US" -TimeZoneId "UTC" -DefaultCallFlow $businessFlow -CallFlows @($afterHoursFlow) -EnableVoiceResponse
        Write-Host "✅ Auto Attendant created: $($aa.Identity)"
        
        # Step 6: Create and apply call handling association
        $association = New-CsAutoAttendantCallHandlingAssociation -Type AfterHours -ScheduleId $schedule.Id -CallFlowId $afterHoursFlow.Id
        Set-CsAutoAttendant -Identity $aa.Identity -CallHandlingAssociations @($association)
        Write-Host "✅ Business hours applied successfully!"
        
        # Step 7: Verify
        $verifyAA = Get-CsAutoAttendant -Identity $aa.Identity
        Write-Host "VERIFICATION RESULTS:"
        Write-Host "  AA Name: $($verifyAA.Name)"
        Write-Host "  AA ID: $($verifyAA.Identity)"
        Write-Host "  Call Flows: $($verifyAA.CallFlows.Count)"
        Write-Host "  Call Handling Associations: $($verifyAA.CallHandlingAssociations.Count)"
        Write-Host "  Schedule ID: $($verifyAA.CallHandlingAssociations[0].ScheduleId)"
        Write-Host "  Association Type: $($verifyAA.CallHandlingAssociations[0].Type)"
        
        Write-Host "SUCCESS: Business hours Auto Attendant created and configured!"
        
        # Cleanup test schedule
        Remove-CsOnlineSchedule -Id $schedule.Id -Force
        Write-Host "✅ Test schedule cleaned up"
        
    } catch {
        Write-Host "❌ Error: $_"
        Write-Host "Details: $($_.Exception.Message)"
        Write-Host "Stack: $($_.ScriptStackTrace)"
    }
    '''
    
    try:
        # Run the PowerShell script
        result = subprocess.run(
            ["/Users/work/teams-sdk/powershell/pwsh", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print("PowerShell Output:")
        print(result.stdout)
        if result.stderr:
            print("PowerShell Errors:")
            print(result.stderr)
            
        print(f"Return code: {result.returncode}")
        
    except subprocess.TimeoutExpired:
        print("❌ PowerShell script timed out")
    except Exception as e:
        print(f"❌ Error running PowerShell: {e}")

if __name__ == "__main__":
    test_business_hours_powershell()