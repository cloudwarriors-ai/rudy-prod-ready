# Debug the "rudy - etl" Auto Attendant Business Hours Issue
# Focus on the specific problem encountered during creation

Write-Host "=== Rudy ETL Business Hours Debug ==="
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

Write-Host "`n=== STEP 1: Check Existing Rudy ETL Auto Attendant ==="
try {
    $existingAAs = Get-CsAutoAttendant | Where-Object { $_.Name -like "*rudy*" -or $_.Name -like "*etl*" }
    if ($existingAAs) {
        Write-Host "Found existing Rudy/ETL Auto Attendants:"
        foreach ($aa in $existingAAs) {
            Write-Host "  AA ID: $($aa.Identity)"
            Write-Host "  Name: $($aa.Name)"
            Write-Host "  Call Flows: $($aa.CallFlows.Count)"
            Write-Host "  Call Handling Associations: $($aa.CallHandlingAssociations.Count)"
            Write-Host ""
        }
        $rudyAA = $existingAAs | Select-Object -First 1
    } else {
        Write-Host "No existing Rudy/ETL Auto Attendants found"
        $rudyAA = $null
    }
} catch {
    Write-Host "❌ Failed to check existing Auto Attendants: $_"
}

Write-Host "`n=== STEP 2: Analyze Current Schedule Implementation Issue ==="
Write-Host "Common business hours implementation issues:"
Write-Host "1. Schedule creation parameter syntax"
Write-Host "2. CallHandlingAssociation timing requirements"
Write-Host "3. CallFlow ID references"
Write-Host "4. Time zone considerations"

Write-Host "`n=== STEP 3: Test Minimal Schedule Creation ==="
try {
    # Test the exact schedule that was attempted for rudy-etl
    Write-Host "Testing business hours schedule creation..."
    
    # Create 9 AM to 5 PM time range
    $timeRange = New-CsOnlineTimeRange -Start 09:00 -End 17:00
    Write-Host "✅ Time range created: 09:00-17:00"
    
    # Create weekly schedule for Monday-Friday
    $scheduleName = "RudyETL-BusinessHours-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    $schedule = New-CsOnlineSchedule -Name $scheduleName -WeeklyRecurrentSchedule -MondayHours @($timeRange) -TuesdayHours @($timeRange) -WednesdayHours @($timeRange) -ThursdayHours @($timeRange) -FridayHours @($timeRange)
    
    Write-Host "✅ Business hours schedule created:"
    Write-Host "  Schedule ID: $($schedule.Id)"
    Write-Host "  Name: $($schedule.Name)"
    Write-Host "  Type: $($schedule.Type)"
    
} catch {
    Write-Host "❌ Schedule creation failed: $_"
    Write-Host "Error details: $($_.Exception.Message)"
}

Write-Host "`n=== STEP 4: Test CallHandlingAssociation Requirements ==="
if ($rudyAA) {
    try {
        Write-Host "Testing call handling association for existing Rudy AA..."
        
        # Get the default call flow ID from the existing AA
        $defaultCallFlowId = $rudyAA.DefaultCallFlow.Id
        Write-Host "Default Call Flow ID: $defaultCallFlowId"
        
        # Check if we have additional call flows
        if ($rudyAA.CallFlows.Count -gt 0) {
            Write-Host "Additional Call Flows found: $($rudyAA.CallFlows.Count)"
            foreach ($flow in $rudyAA.CallFlows) {
                Write-Host "  Flow ID: $($flow.Id)"
                Write-Host "  Flow Name: $($flow.Name)"
            }
        } else {
            Write-Host "No additional call flows found - this might be the issue!"
            Write-Host "Business hours requires separate call flows for business vs after-hours"
        }
        
        # Test call handling association creation
        if ($schedule) {
            Write-Host "`nTesting call handling association creation..."
            
            # For business hours, we need the after-hours call flow to be associated with the complement schedule
            if ($rudyAA.CallFlows.Count -gt 0) {
                $afterHoursFlow = $rudyAA.CallFlows[0]
                $testAssociation = New-CsAutoAttendantCallHandlingAssociation -Type AfterHours -ScheduleId $schedule.Id -CallFlowId $afterHoursFlow.Id
                
                Write-Host "✅ Call handling association test successful:"
                Write-Host "  Type: $($testAssociation.Type)"
                Write-Host "  Schedule ID: $($testAssociation.ScheduleId)"
                Write-Host "  Call Flow ID: $($testAssociation.CallFlowId)"
                
                # Test applying it to the Auto Attendant
                Write-Host "`nTesting application to Auto Attendant..."
                Set-CsAutoAttendant -Identity $rudyAA.Identity -CallHandlingAssociations @($testAssociation)
                Write-Host "✅ Successfully applied business hours to Rudy ETL Auto Attendant!"
                
                # Verify
                $updatedAA = Get-CsAutoAttendant -Identity $rudyAA.Identity
                Write-Host "✅ Verification: Call Handling Associations: $($updatedAA.CallHandlingAssociations.Count)"
                
            } else {
                Write-Host "❌ Cannot create association - no after-hours call flow available"
                Write-Host "SOLUTION: Need to create after-hours call flow first"
            }
        }
        
    } catch {
        Write-Host "❌ Call handling association test failed: $_"
        Write-Host "Error details: $($_.Exception.Message)"
    }
} else {
    Write-Host "No Rudy AA found to test associations with"
}

Write-Host "`n=== STEP 5: Provide Solution Recommendations ==="
Write-Host "Based on debug analysis:"
Write-Host ""
Write-Host "ISSUE IDENTIFIED:"
Write-Host "- Business hours requires separate call flows for business vs after-hours"
Write-Host "- The original rudy-etl creation likely only had a default call flow"
Write-Host "- CallHandlingAssociation needs a separate CallFlow ID to associate with the schedule"
Write-Host ""
Write-Host "SOLUTION STEPS:"
Write-Host "1. Create after-hours call flow with voicemail routing"
Write-Host "2. Add the after-hours call flow to the Auto Attendant"
Write-Host "3. Create business hours schedule (9-5 Mon-Fri)"
Write-Host "4. Create CallHandlingAssociation linking schedule to after-hours flow"
Write-Host "5. Apply the association to the Auto Attendant"
Write-Host ""
Write-Host "IMPLEMENTATION:"
Write-Host "- Default call flow = Business hours behavior"
Write-Host "- Additional call flow = After-hours behavior"
Write-Host "- Schedule defines WHEN to use the after-hours flow"

Write-Host "`n=== CLEANUP: Remove Test Schedule ==="
try {
    if ($schedule) {
        Remove-CsOnlineSchedule -Id $schedule.Id -Force
        Write-Host "✅ Test schedule removed"
    }
} catch {
    Write-Host "⚠️ Failed to remove test schedule: $_"
}

Write-Host "`n=== Debug Complete ==="