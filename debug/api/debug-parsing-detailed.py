#!/usr/bin/env python3
"""
Detailed Parsing Debug
Purpose: Find exactly why parsing fails
"""

# Simulate the actual output
api_output = """QUEUE_START
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
QUEUE_END"""

def debug_parsing():
    print("🔍 DETAILED PARSING DEBUG")
    print("=" * 40)
    
    queues = []
    current_queue = None
    
    lines = api_output.split('\n')
    
    for i, line in enumerate(lines):
        original_line = line
        line = line.strip()
        
        print(f"Line {i}: '{original_line}' -> stripped: '{line}'")
        
        if line == "QUEUE_START":
            print(f"  🟢 QUEUE_START detected")
            current_queue = {}
        elif line == "QUEUE_END" and current_queue:
            print(f"  🔴 QUEUE_END detected, current_queue: {current_queue}")
            queues.append(current_queue)
            current_queue = None
        elif current_queue and ': ' in line:
            print(f"  📝 Processing data line (current_queue exists: {current_queue is not None})")
            key, value = line.split(': ', 1)
            key_formatted = key.lower().replace(' ', '_')
            current_queue[key_formatted] = value
            print(f"      Added: {key_formatted} = '{value}'")
            print(f"      Current queue now: {current_queue}")
        else:
            if current_queue:
                print(f"  ⚠️  Skipped line while in queue context: '{line}' (contains colon: {': ' in line})")
            else:
                print(f"  ⏭️  Skipped line (no queue context)")
    
    print(f"\n🎯 FINAL RESULT: {len(queues)} queues parsed")
    for i, queue in enumerate(queues):
        print(f"   Queue {i+1}: {queue}")

if __name__ == "__main__":
    debug_parsing()