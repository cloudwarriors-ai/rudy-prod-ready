# Fix the existing "rudy - etl" Auto Attendant with proper business hours
# This script adds business hours configuration to the existing AA

Write-Host "=== Fixing Rudy ETL Auto Attendant Business Hours ==="
Write-Host "Timestamp: $(Get-Date)"

# Standard auth setup
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/Users/work/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

try {
    Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    Write-Host "✅ Teams connection successful"
} catch {
    Write-Host "❌ Teams connection failed: $_"
    exit 1
}

Write-Host "`n=== STEP 1: Find Rudy ETL Auto Attendant ==="
try {
    $allAAs = Get-CsAutoAttendant
    $rudyAA = $allAAs | Where-Object { $_.Name -like "*rudy*" -or $_.Name -like "*etl*" }
    
    if ($rudyAA) {
        Write-Host "✅ Found Rudy ETL Auto Attendant:"
        foreach ($aa in $rudyAA) {
            Write-Host "  Name: $($aa.Name)"
            Write-Host "  ID: $($aa.Identity)"
            Write-Host "  Call Flows: $($aa.CallFlows.Count)"
            Write-Host "  Call Handling Associations: $($aa.CallHandlingAssociations.Count)"
            Write-Host ""
        }
        
        # Use the first one found
        $targetAA = $rudyAA | Select-Object -First 1
        Write-Host "Using AA: $($targetAA.Name) (ID: $($targetAA.Identity))"
        
    } else {
        Write-Host "❌ No Rudy/ETL Auto Attendant found"
        Write-Host "Available Auto Attendants:"
        foreach ($aa in $allAAs) {
            Write-Host "  - $($aa.Name)"
        }
        exit 1
    }
} catch {
    Write-Host "❌ Failed to get Auto Attendants: $_"
    exit 1
}

Write-Host "`n=== STEP 2: Create Business Hours Schedule ==="
try {
    # Create 9 AM to 5 PM time range
    $timeRange = New-CsOnlineTimeRange -Start 09:00 -End 17:00
    Write-Host "✅ Time range created: 09:00-17:00"
    
    # Create business hours schedule for Monday-Friday
    $scheduleName = "RudyETL-BusinessHours-$(Get-Date -Format 'yyyyMMddHHmmss')"
    $schedule = New-CsOnlineSchedule -Name $scheduleName -WeeklyRecurrentSchedule -MondayHours @($timeRange) -TuesdayHours @($timeRange) -WednesdayHours @($timeRange) -ThursdayHours @($timeRange) -FridayHours @($timeRange)
    
    Write-Host "✅ Business hours schedule created:"
    Write-Host "  Schedule ID: $($schedule.Id)"
    Write-Host "  Name: $($schedule.Name)"
    
} catch {
    Write-Host "❌ Failed to create business hours schedule: $_"
    Write-Host "Error details: $($_.Exception.Message)"
    exit 1
}

Write-Host "`n=== STEP 3: Create After-Hours Call Flow ==="
try {
    # Create after-hours greeting
    $afterHoursGreeting = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Thank you for calling Rudy ETL. We are currently closed. Our business hours are 9 AM to 5 PM, Monday through Friday. Please call back during business hours."
    
    # Create after-hours call flow (announcement only)
    $afterHoursCallFlow = New-CsAutoAttendantCallFlow -Name "RudyETL-AfterHours" -Greetings @($afterHoursGreeting)
    
    Write-Host "✅ After-hours call flow created:"
    Write-Host "  Flow ID: $($afterHoursCallFlow.Id)"
    Write-Host "  Flow Name: $($afterHoursCallFlow.Name)"
    
} catch {
    Write-Host "❌ Failed to create after-hours call flow: $_"
    Write-Host "Error details: $($_.Exception.Message)"
    exit 1
}

Write-Host "`n=== STEP 4: Update Auto Attendant with After-Hours Flow ==="
try {
    # Get current call flows and add the new after-hours flow
    $currentCallFlows = $targetAA.CallFlows
    $updatedCallFlows = @()
    
    # Add existing call flows (if any)
    foreach ($flow in $currentCallFlows) {
        $updatedCallFlows += $flow
    }
    
    # Add the new after-hours flow
    $updatedCallFlows += $afterHoursCallFlow
    
    # Update the Auto Attendant with the new call flow
    Set-CsAutoAttendant -Identity $targetAA.Identity -CallFlows $updatedCallFlows
    
    Write-Host "✅ Auto Attendant updated with after-hours call flow"
    Write-Host "  Total call flows: $($updatedCallFlows.Count)"
    
} catch {
    Write-Host "❌ Failed to update Auto Attendant with call flow: $_"
    Write-Host "Error details: $($_.Exception.Message)"
    exit 1
}

Write-Host "`n=== STEP 5: Create and Apply Call Handling Association ==="
try {
    # Create call handling association for after-hours
    $callHandlingAssociation = New-CsAutoAttendantCallHandlingAssociation -Type AfterHours -ScheduleId $schedule.Id -CallFlowId $afterHoursCallFlow.Id
    
    Write-Host "✅ Call handling association created:"
    Write-Host "  Type: $($callHandlingAssociation.Type)"
    Write-Host "  Schedule ID: $($callHandlingAssociation.ScheduleId)"
    Write-Host "  Call Flow ID: $($callHandlingAssociation.CallFlowId)"
    
    # Apply the association to the Auto Attendant
    Set-CsAutoAttendant -Identity $targetAA.Identity -CallHandlingAssociations @($callHandlingAssociation)
    
    Write-Host "✅ Business hours configuration applied to Auto Attendant!"
    
} catch {
    Write-Host "❌ Failed to create or apply call handling association: $_"
    Write-Host "Error details: $($_.Exception.Message)"
    exit 1
}

Write-Host "`n=== STEP 6: Verify Business Hours Configuration ==="
try {
    # Get the updated Auto Attendant to verify
    $updatedAA = Get-CsAutoAttendant -Identity $targetAA.Identity
    
    Write-Host "✅ VERIFICATION RESULTS:"
    Write-Host "  AA Name: $($updatedAA.Name)"
    Write-Host "  AA ID: $($updatedAA.Identity)"
    Write-Host "  Total Call Flows: $($updatedAA.CallFlows.Count)"
    Write-Host "  Call Handling Associations: $($updatedAA.CallHandlingAssociations.Count)"
    
    if ($updatedAA.CallHandlingAssociations.Count -gt 0) {
        foreach ($assoc in $updatedAA.CallHandlingAssociations) {
            Write-Host "    Association Type: $($assoc.Type)"
            Write-Host "    Schedule ID: $($assoc.ScheduleId)"
            Write-Host "    Call Flow ID: $($assoc.CallFlowId)"
        }
        
        Write-Host ""
        Write-Host "🎉 SUCCESS: Rudy ETL Auto Attendant now has proper business hours!"
        Write-Host ""
        Write-Host "BUSINESS HOURS CONFIGURATION:"
        Write-Host "  ⏰ Business Hours: 9 AM - 5 PM, Monday - Friday"
        Write-Host "  📞 Business Hours: Uses existing default call flow"
        Write-Host "  🌙 After Hours: Uses new after-hours call flow with closed message"
        Write-Host "  📅 Schedule ID: $($schedule.Id)"
        Write-Host ""
        Write-Host "The Auto Attendant will now:"
        Write-Host "  • During business hours (9-5 Mon-Fri): Use default greeting and menu"
        Write-Host "  • During after hours: Play closed message with business hours info"
        
    } else {
        Write-Host "⚠️ WARNING: Call handling associations not found - verification failed"
    }
    
} catch {
    Write-Host "❌ Failed to verify configuration: $_"
    Write-Host "Error details: $($_.Exception.Message)"
}

Write-Host "`n=== Fix Complete ==="
Write-Host "Check the Teams Admin Center to verify the business hours configuration"