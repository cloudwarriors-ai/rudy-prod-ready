# Test Auto Attendant PowerShell Syntax
# This script tests the correct syntax for New-CsAutoAttendantMenu and New-CsAutoAttendantCallFlow

# Standard auth setup
$TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
$AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
$PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
$PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)

try {
    Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
    Write-Host "✅ Teams connection successful"
} catch {
    Write-Host "❌ Teams connection failed: $_"
    exit 1
}

Write-Host "=== TESTING AUTO ATTENDANT CMDLET SYNTAX ==="

# Test 1: Check what parameters are available for New-CsAutoAttendantMenu
Write-Host "`n1. Testing New-CsAutoAttendantMenu parameters..."
try {
    Get-Help New-CsAutoAttendantMenu -Parameter * | Select-Object Name, Type, Required | Format-Table
} catch {
    Write-Host "Help not available, trying Get-Command"
    (Get-Command New-CsAutoAttendantMenu).Parameters.Keys | Sort-Object
}

# Test 2: Check what parameters are available for New-CsAutoAttendantCallFlow
Write-Host "`n2. Testing New-CsAutoAttendantCallFlow parameters..."
try {
    Get-Help New-CsAutoAttendantCallFlow -Parameter * | Select-Object Name, Type, Required | Format-Table
} catch {
    Write-Host "Help not available, trying Get-Command"
    (Get-Command New-CsAutoAttendantCallFlow).Parameters.Keys | Sort-Object
}

# Test 3: Test creating a simple menu option
Write-Host "`n3. Testing menu option creation..."
try {
    # Use the hardcoded resource account that works
    $menuTarget1 = New-CsAutoAttendantCallableEntity -Identity "aae57acd-8533-4ba0-9a0b-06895e4c6c47" -Type ApplicationEndpoint
    Write-Host "✅ Menu target created successfully"
    
    $menuOption1 = New-CsAutoAttendantMenuOption -Action TransferCallToTarget -DtmfResponse Tone1 -CallTarget $menuTarget1
    Write-Host "✅ Menu option created successfully"
    
} catch {
    Write-Host "❌ Menu option creation failed: $_"
}

# Test 4: Test creating a menu (this might fail and show us the correct syntax)
Write-Host "`n4. Testing menu creation..."
try {
    $menu = New-CsAutoAttendantMenu -Name "TestMenu" -MenuOptions @($menuOption1) -EnableDialByName $false
    Write-Host "✅ Menu created successfully"
} catch {
    Write-Host "❌ Menu creation failed: $_"
    Write-Host "Error details: $($_.Exception.Message)"
    Write-Host "Full error: $($_.Exception)"
}

# Test 5: Test creating a greeting prompt
Write-Host "`n5. Testing greeting prompt creation..."
try {
    $greetingPrompt = New-CsAutoAttendantPrompt -TextToSpeechPrompt "Welcome to our test system"
    Write-Host "✅ Greeting prompt created successfully"
    Write-Host "Prompt type: $($greetingPrompt.GetType())"
} catch {
    Write-Host "❌ Greeting prompt creation failed: $_"
}

# Test 6: Test creating a call flow (this is likely where the -Prompts error occurs)
Write-Host "`n6. Testing call flow creation..."
try {
    # Try different parameter combinations
    Write-Host "Trying with -Greetings parameter..."
    $defaultCallFlow = New-CsAutoAttendantCallFlow -Name "TestFlow" -Menu $menu -Greetings @($greetingPrompt)
    Write-Host "✅ Call flow created with -Greetings parameter"
} catch {
    Write-Host "❌ Call flow with -Greetings failed: $_"
    
    Write-Host "Trying with -Prompts parameter..."
    try {
        $defaultCallFlow = New-CsAutoAttendantCallFlow -Name "TestFlow" -Menu $menu -Prompts @($greetingPrompt)
        Write-Host "✅ Call flow created with -Prompts parameter"
    } catch {
        Write-Host "❌ Call flow with -Prompts also failed: $_"
        
        Write-Host "Trying without greeting parameter..."
        try {
            $defaultCallFlow = New-CsAutoAttendantCallFlow -Name "TestFlow" -Menu $menu
            Write-Host "✅ Call flow created without greeting"
        } catch {
            Write-Host "❌ Call flow without greeting also failed: $_"
        }
    }
}

Write-Host "`n=== TEST COMPLETED ==="