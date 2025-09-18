#!/bin/bash
# Simple Teams SDK Call Center Test
# This script demonstrates basic usage of the unified test script

echo "🎯 Running Simple Teams SDK Call Center Test"
echo "=============================================="

cd "$(dirname "$0")/.."

# Generate unique timestamp for usernames
TIMESTAMP=$(date +%s)
echo "Using timestamp: $TIMESTAMP for unique usernames"
echo ""

# Basic test with unique parameters
python3 test_unified_call_center.py \
    --user-name "Demo User $TIMESTAMP" \
    --user-email "demouser${TIMESTAMP}@cloudwarriors.onmicrosoft.com" \
    --queue-name "Simple Support Queue $TIMESTAMP" \
    --aa-name "Simple IVR $TIMESTAMP"

echo ""
echo "✅ Test complete! Check the output above for results."
echo "Note: Auto Attendant creation may fail (expected) - core functionality should work."