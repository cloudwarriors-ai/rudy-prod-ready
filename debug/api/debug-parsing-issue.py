#!/usr/bin/env python3
"""
Debug Call Queue Parsing Issue
Purpose: Test the parsing logic with actual API output
Date: September 18, 2025
"""

# Simulate the actual output from the API logs
api_output = """PS /root/code/teams-sdk> [?1h# Starting command execution
[?1lPS /root/code/teams-sdk> [?1h
[?1lPS /root/code/teams-sdk> [?1h    # Connect to Teams if not already connected
[?1lPS /root/code/teams-sdk> [?1h    try {
[?1l>> [?1h        Get-CsTenant -ErrorAction Stop | Out-Null
>> [?1h    } catch {
>> [?1h        $TenantId = "e7b105b2-720e-4b5b-9310-1a414c06356a"
>> [?1h        $AppId = "968fafbb-27b8-400a-b8c3-a90eb3c2de26"
>> [?1h        $PfxPath = "/root/code/teams-sdk/auth-keys/teamsfed.pfx"
>> [?1h        $PfxPass = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
>> [?1h        $Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($PfxPath, $PfxPass)
>> [?1h        Connect-MicrosoftTeams -TenantId $TenantId -ApplicationId $AppId -Certificate $Cert
>> [?1h    }
>> [?1h
[?1l

Account                             Environment Tenant
-------                              ----------- ------
968fafbb-27b8-400a-b8c3-a90eb3c2de26 AzureCloud  e7b105b2-720e-4b5b-9310-1a414…

PS /root/code/teams-sdk> [?1h    try {
[?1l>> [?1h        Write-Host "Getting all call queues..."
>> [?1h        $queues = Get-CsCallQueue
>> [?1h
[?1l>> [?1h        Write-Host "CALLQUEUES_COUNT: $($queues.Count)"
>> [?1h        Write-Host "CALLQUEUES_TYPE: $($queues.GetType())"
>> [?1h        if ($queues.Count -eq 0) {
>> [?1h            Write-Host "CALLQUEUES_EMPTY: No queues returned by Get-CsCallQueue"
>> [?1h        }
>> [?1h
[?1l>> [?1h        Write-Host "CALLQUEUES_LIST_SUCCESS"
>> [?1h        foreach ($queue in $queues) {
>> [?1h            Write-Host "QUEUE_START"
>> [?1h            Write-Host "Identity: $($queue.Identity)"
>> [?1h            Write-Host "Name: $($queue.Name)"
>> [?1h            Write-Host "RoutingMethod: $($queue.RoutingMethod)"
>> [?1h            Write-Host "AgentAlertTime: $($queue.AgentAlertTime)"
>> [?1h            Write-Host "OverflowThreshold: $($queue.OverflowThreshold)"
>> [?1h            Write-Host "TimeoutThreshold: $($queue.TimeoutThreshold)"
>> [?1h            Write-Host "QUEUE_END"
>> [?1h        }
>> [?1h
[?1lGetting all call queues...
WARNING: No Distribution Lists or Users added to callqueue. There will be no agents to call.
WARNING: ConferenceMode is turned on for this callqueue. The call will be established using the traditional transfer mode or the new conference mode, based on the supportability of caller/agent. Please refer to the documentation for more information on the supportability matrix.
CALLQUEUES_COUNT: 13
CALLQUEUES_TYPE: System.Object[]
CALLQUEUES_LIST_SUCCESS
QUEUE_START
Identity: ca6cf9b4-55d6-4123-8321-9114a09985dd
Name: Alpha Test Queue
RoutingMethod: RoundRobin
AgentAlertTime: 30
OverflowThreshold: 20
TimeoutThreshold: 1200
QUEUE_END
QUEUE_START
Identity: f7f37bee-ef88-430d-9d30-d162f1edbf36
Name: Debug Test Queue
RoutingMethod: Attendant
AgentAlertTime: 30
OverflowThreshold: 20
TimeoutThreshold: 1200
QUEUE_END"""

def test_parsing_logic():
    """Test the current parsing logic from app.py"""
    print("🔍 Testing Call Queue Parsing Logic")
    print("=" * 50)
    
    # Current parsing logic from app.py
    if "CALLQUEUES_LIST_SUCCESS" in api_output:
        print("✅ Found CALLQUEUES_LIST_SUCCESS marker")
        
        # Parse call queues from output
        queues = []
        current_queue = None
        
        lines = api_output.split('\n')
        print(f"📄 Total lines to parse: {len(lines)}")
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line == "QUEUE_START":
                print(f"🟢 Line {i}: Found QUEUE_START")
                current_queue = {}
            elif line == "QUEUE_END" and current_queue:
                print(f"🔴 Line {i}: Found QUEUE_END, adding queue: {current_queue}")
                queues.append(current_queue)
                current_queue = None
            elif current_queue and ': ' in line:
                key, value = line.split(': ', 1)
                key_formatted = key.lower().replace(' ', '_')
                current_queue[key_formatted] = value
                print(f"📝 Line {i}: Added {key_formatted} = {value}")
        
        print(f"\n🎯 PARSING RESULTS:")
        print(f"   - Total queues parsed: {len(queues)}")
        print(f"   - Queue names: {[q.get('name', 'NO NAME') for q in queues]}")
        
        return {
            "message": f"Found {len(queues)} call queues",
            "queues": queues,
            "count": len(queues)
        }
    else:
        print("❌ CALLQUEUES_LIST_SUCCESS marker not found")
        return None

def analyze_output_issues():
    """Analyze potential issues with the output format"""
    print("\n🔬 ANALYZING OUTPUT ISSUES")
    print("=" * 50)
    
    lines = api_output.split('\n')
    
    # Look for ANSI escape sequences
    ansi_lines = [i for i, line in enumerate(lines) if '[' in line and '?1' in line]
    print(f"📺 Lines with ANSI escape sequences: {len(ansi_lines)}")
    if ansi_lines:
        print(f"   First few: {ansi_lines[:5]}")
    
    # Find queue start/end markers
    start_lines = [i for i, line in enumerate(lines) if line.strip() == "QUEUE_START"]
    end_lines = [i for i, line in enumerate(lines) if line.strip() == "QUEUE_END"]
    
    print(f"🟢 QUEUE_START markers found at lines: {start_lines}")
    print(f"🔴 QUEUE_END markers found at lines: {end_lines}")
    
    if len(start_lines) != len(end_lines):
        print("⚠️  MISMATCH: Different number of START and END markers!")
    
    # Check specific problematic lines
    for i in range(min(len(start_lines), 3)):  # Check first 3 queues
        start_line = start_lines[i]
        if i < len(end_lines):
            end_line = end_lines[i]
            queue_lines = lines[start_line:end_line+1]
            print(f"\n📋 Queue {i+1} lines ({start_line}-{end_line}):")
            for j, qline in enumerate(queue_lines):
                print(f"   {start_line + j}: '{qline}'")

if __name__ == "__main__":
    result = test_parsing_logic()
    analyze_output_issues()
    
    print(f"\n🎯 FINAL RESULT: {result}")
    
    if result and result['count'] > 0:
        print("✅ PARSING WORKS - Issue must be elsewhere!")
    else:
        print("❌ PARSING FAILED - This is the root cause!")