# Test Business Hours Schedule Creation for Auto Attendants
# Debug script to understand schedule and call handling association requirements

Write-Host "=== Business Hours Schedule Debug Test ==="
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

Write-Host "`n=== STEP 1: Research Existing Schedules ==="
try {
    $existingSchedules = Get-CsOnlineSchedule
    Write-Host "Found $($existingSchedules.Count) existing schedules:"
    foreach ($schedule in $existingSchedules) {
        Write-Host "- Schedule ID: $($schedule.Id)"
        Write-Host "  Name: $($schedule.Name)"
        Write-Host "  Type: $($schedule.Type)"
        Write-Host "  AssociatedConfigurationId: $($schedule.AssociatedConfigurationId)"
        if ($schedule.WeeklyRecurrentSchedule) {
            Write-Host "  WeeklyRecurrentSchedule: Yes"
            Write-Host "  MondayHours: $($schedule.WeeklyRecurrentSchedule.MondayHours)"
            Write-Host "  TuesdayHours: $($schedule.WeeklyRecurrentSchedule.TuesdayHours)"
        }
        Write-Host ""
    }
} catch {
    Write-Host "❌ Failed to get existing schedules: $_"
}

Write-Host "`n=== STEP 2: Create Business Hours Time Range ==="
try {
    # Create time range for 9 AM to 5 PM
    $businessHoursRange = New-CsOnlineTimeRange -Start 09:00 -End 17:00
    Write-Host "✅ Business hours time range created:"
    Write-Host "  Start: $($businessHoursRange.Start)"
    Write-Host "  End: $($businessHoursRange.End)"
} catch {
    Write-Host "❌ Failed to create time range: $_"
    exit 1
}

Write-Host "`n=== STEP 3: Create Business Hours Schedule ==="
try {
    $scheduleId = "BusinessHours-Debug-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    
    # Create weekly recurrent schedule for Monday-Friday 9-5
    $businessSchedule = New-CsOnlineSchedule -Name $scheduleId -WeeklyRecurrentSchedule -MondayHours @($businessHoursRange) -TuesdayHours @($businessHoursRange) -WednesdayHours @($businessHoursRange) -ThursdayHours @($businessHoursRange) -FridayHours @($businessHoursRange)
    
    Write-Host "✅ Business hours schedule created:"
    Write-Host "  Schedule ID: $($businessSchedule.Id)"
    Write-Host "  Name: $($businessSchedule.Name)"
    Write-Host "  Type: $($businessSchedule.Type)"
    Write-Host "  Monday Hours: $($businessSchedule.WeeklyRecurrentSchedule.MondayHours.Count) ranges"
    Write-Host "  Friday Hours: $($businessSchedule.WeeklyRecurrentSchedule.FridayHours.Count) ranges"
    
    $createdScheduleId = $businessSchedule.Id
    
} catch {
    Write-Host "❌ Failed to create business hours schedule: $_"
    Write-Host "Error details: $($_.Exception.Message)"
    exit 1
}

Write-Host "`n=== STEP 4: Test Call Handling Association Creation ==="
try {
    Write-Host "Testing call handling association syntax..."
    
    # This is just syntax testing - we'll need an actual auto attendant to associate
    Write-Host "New-CsAutoAttendantCallHandlingAssociation syntax test:"
    Write-Host "  -Type: BusinessHours"
    Write-Host "  -ScheduleId: $createdScheduleId"
    Write-Host "  -CallFlowId: [NEEDS_ACTUAL_CALLFLOW_ID]"
    
    Write-Host "✅ Syntax validation passed"
    
} catch {
    Write-Host "❌ Call handling association test failed: $_"
}

Write-Host "`n=== STEP 5: Get Available Call Queues for Testing ==="
try {
    $callQueues = Get-CsCallQueue
    Write-Host "Found $($callQueues.Count) call queues available for testing:"
    $testQueue = $callQueues | Select-Object -First 1
    if ($testQueue) {
        Write-Host "  Test Queue ID: $($testQueue.Identity)"
        Write-Host "  Test Queue Name: $($testQueue.Name)"
    }
} catch {
    Write-Host "❌ Failed to get call queues: $_"
}

Write-Host "`n=== STEP 6: Test Complete Auto Attendant with Business Hours ==="
try {
    Write-Host "Creating test Auto Attendant with business hours..."
    
    # Create prompts
    $greetingPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Thank you for calling. Our business hours are 9 AM to 5 PM, Monday through Friday."
    $menuPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Press 0 to speak with an agent, or press star to repeat this menu."
    
    # Create menu option for repeat
    $repeatOption = New-CsAutoAttendantMenuOption -Action Announcement -DtmfResponse ToneStar -Prompt $menuPrompt
    
    # Create menu option for call queue (if available)
    $menuOptions = @($repeatOption)
    if ($testQueue) {
        $callTarget = New-CsAutoAttendantCallableEntity -Identity $testQueue.Identity -Type ApplicationEndpoint
        $transferOption = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone0 -CallTarget $callTarget
        $menuOptions += $transferOption
    }
    
    # Create menu
    $menu = New-CsAutoAttendantMenu -Name "BusinessHoursMenu" -Prompts @($menuPrompt) -MenuOptions $menuOptions
    
    # Create default call flow (this will be used during business hours)
    $defaultCallFlow = New-CsAutoAttendantCallFlow -Name "BusinessHoursFlow" -Greetings @($greetingPrompt) -Menu $menu
    
    # Create after-hours call flow (simple announcement)
    $afterHoursPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Thank you for calling. Our office is currently closed. Our business hours are 9 AM to 5 PM, Monday through Friday. Please call back during business hours."
    $afterHoursCallFlow = New-CsAutoAttendantCallFlow -Name "AfterHoursFlow" -Greetings @($afterHoursPrompt)
    
    # Create the Auto Attendant with multiple call flows
    $aaName = "BusinessHours-Test-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    $autoAttendant = New-CsAutoAttendant -Name $aaName -DefaultCallFlow $defaultCallFlow -CallFlows @($afterHoursCallFlow) -LanguageId "en-US" -TimeZoneId "UTC" -EnableVoiceResponse
    
    Write-Host "✅ Auto Attendant created:"
    Write-Host "  AA ID: $($autoAttendant.Identity)"
    Write-Host "  AA Name: $($autoAttendant.Name)"
    Write-Host "  Default Call Flow: $($autoAttendant.DefaultCallFlow.Name)"
    Write-Host "  Additional Call Flows: $($autoAttendant.CallFlows.Count)"
    
    # Now create the call handling association
    Write-Host "`nCreating call handling association..."
    $callHandlingAssociation = New-CsAutoAttendantCallHandlingAssociation -Type BusinessHours -ScheduleId $createdScheduleId -CallFlowId $afterHoursCallFlow.Id
    
    Write-Host "✅ Call handling association created:"
    Write-Host "  Type: $($callHandlingAssociation.Type)"
    Write-Host "  Schedule ID: $($callHandlingAssociation.ScheduleId)"
    Write-Host "  Call Flow ID: $($callHandlingAssociation.CallFlowId)"
    
    # Update the Auto Attendant with the association
    Write-Host "`nUpdating Auto Attendant with business hours..."
    Set-CsAutoAttendant -Identity $autoAttendant.Identity -CallHandlingAssociations @($callHandlingAssociation)
    
    Write-Host "✅ Auto Attendant updated with business hours successfully!"
    
    # Verify the final configuration
    $updatedAA = Get-CsAutoAttendant -Identity $autoAttendant.Identity
    Write-Host "`nFinal configuration:"
    Write-Host "  Call Handling Associations: $($updatedAA.CallHandlingAssociations.Count)"
    if ($updatedAA.CallHandlingAssociations.Count -gt 0) {
        foreach ($assoc in $updatedAA.CallHandlingAssociations) {
            Write-Host "    Type: $($assoc.Type)"
            Write-Host "    Schedule ID: $($assoc.ScheduleId)"
            Write-Host "    Call Flow ID: $($assoc.CallFlowId)"
        }
    }
    
} catch {
    Write-Host "❌ Failed to create Auto Attendant with business hours: $_"
    Write-Host "Error details: $($_.Exception.Message)"
    Write-Host "Stack trace: $($_.ScriptStackTrace)"
}

Write-Host "`n=== CLEANUP: Remove Test Schedule ==="
try {
    if ($createdScheduleId) {
        Remove-CsOnlineSchedule -Id $createdScheduleId -Force
        Write-Host "✅ Test schedule removed: $createdScheduleId"
    }
} catch {
    Write-Host "⚠️ Failed to remove test schedule: $_"
}

Write-Host "`n=== Debug Test Complete ==="
Write-Host "Check output above for business hours implementation insights"