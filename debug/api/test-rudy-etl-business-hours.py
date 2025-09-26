#!/usr/bin/env python3

import subprocess
import os

def apply_business_hours_to_rudy_etl():
    """Apply business hours to the existing rudy-etl Auto Attendant"""
    
    print("=== Applying Business Hours to Rudy ETL Auto Attendant ===")
    
    # Change to the teams-sdk directory
    os.chdir("/Users/work/teams-sdk")
    
    # PowerShell script to apply business hours to specific AA
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
        # Target AA ID from your documentation
        $aaId = "7a76d78a-d7be-44c4-b653-22635a985bda"
        
        # Step 1: Verify the AA exists
        $existingAA = Get-CsAutoAttendant -Identity $aaId
        if (-not $existingAA) {
            Write-Host "❌ Auto Attendant not found: $aaId"
            
            # List all auto attendants to find the correct one
            Write-Host "Available Auto Attendants:"
            $allAAs = Get-CsAutoAttendant
            foreach ($aa in $allAAs) {
                Write-Host "  - Name: $($aa.Name)"
                Write-Host "    ID: $($aa.Identity)"
                if ($aa.Name -like "*rudy*" -or $aa.Name -like "*etl*") {
                    Write-Host "    *** This looks like the Rudy ETL AA ***"
                    $aaId = $aa.Identity
                    $existingAA = $aa
                }
                Write-Host ""
            }
        }
        
        if ($existingAA) {
            Write-Host "✅ Found Auto Attendant:"
            Write-Host "  Name: $($existingAA.Name)"
            Write-Host "  ID: $($existingAA.Identity)"
            Write-Host "  Current Call Flows: $($existingAA.CallFlows.Count)"
            Write-Host "  Current Associations: $($existingAA.CallHandlingAssociations.Count)"
            Write-Host ""
            
            # Step 2: Create business hours schedule
            $timeRange = New-CsOnlineTimeRange -Start 09:00 -End 17:00
            Write-Host "✅ Time range created"
            
            $scheduleName = "RudyETL-BH-$(Get-Date -Format 'yyyyMMddHHmmss')"
            $schedule = New-CsOnlineSchedule -Name $scheduleName -WeeklyRecurrentSchedule -MondayHours @($timeRange) -TuesdayHours @($timeRange) -WednesdayHours @($timeRange) -ThursdayHours @($timeRange) -FridayHours @($timeRange)
            Write-Host "✅ Schedule created: $($schedule.Id)"
            
            # Step 3: Create after-hours call flow
            $afterHoursGreeting = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Thank you for calling Rudy ETL. We are currently closed. Our business hours are 9 AM to 5 PM, Monday through Friday. Please call back during business hours or leave a message."
            $afterHoursFlow = New-CsAutoAttendantCallFlow -Name "RudyETL-AfterHours" -Greetings @($afterHoursGreeting)
            Write-Host "✅ After-hours call flow created: $($afterHoursFlow.Id)"
            
            # Step 4: Update Auto Attendant with after-hours flow
            $allFlows = @($existingAA.CallFlows) + @($afterHoursFlow)
            Set-CsAutoAttendant -Identity $existingAA.Identity -CallFlows $allFlows
            Write-Host "✅ Auto Attendant updated with after-hours flow"
            
            # Step 5: Create and apply call handling association
            $association = New-CsAutoAttendantCallHandlingAssociation -Type AfterHours -ScheduleId $schedule.Id -CallFlowId $afterHoursFlow.Id
            Set-CsAutoAttendant -Identity $existingAA.Identity -CallHandlingAssociations @($association)
            Write-Host "✅ Business hours association applied"
            
            # Step 6: Verify the result
            $updatedAA = Get-CsAutoAttendant -Identity $existingAA.Identity
            Write-Host ""
            Write-Host "🎉 SUCCESS: Business hours applied to Rudy ETL!"
            Write-Host "  Total Call Flows: $($updatedAA.CallFlows.Count)"
            Write-Host "  Call Handling Associations: $($updatedAA.CallHandlingAssociations.Count)"
            Write-Host "  Schedule ID: $($schedule.Id)"
            Write-Host ""
            Write-Host "CONFIGURATION:"
            Write-Host "  • Business Hours (9-5 Mon-Fri): Uses default call flow"
            Write-Host "  • After Hours: Uses new after-hours call flow"
            Write-Host "  • Schedule: Monday-Friday 9 AM to 5 PM"
            Write-Host ""
            Write-Host "Check Teams Admin Center under Auto attendants > Call flow for after hours"
            
        } else {
            Write-Host "❌ Could not find Rudy ETL Auto Attendant"
        }
        
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
    apply_business_hours_to_rudy_etl()