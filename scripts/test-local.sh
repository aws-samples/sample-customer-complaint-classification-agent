#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

LOCAL_SERVER_URL="${LOCAL_SERVER_URL:-http://localhost:8080}"

echo "=== Complaints Agent Local Testing ==="
echo "Server URL: $LOCAL_SERVER_URL"
echo ""

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "Error: $1 is not installed or not in PATH"
        echo "Please install $1 before running this script"
        exit 1
    fi
}

check_command "curl"
check_command "python3"

echo "Checking if local server is running..."
if ! curl -s "$LOCAL_SERVER_URL" > /dev/null 2>&1; then
    echo "Warning: Local server may not be running at $LOCAL_SERVER_URL"
    echo "Start the server with: ./scripts/local-dev.sh"
    echo ""
fi

COMPLAINT_TRANSCRIPT="Customer: I've been waiting for over an hour and nobody has helped me. This is absolutely unacceptable service. I want to speak to a manager immediately. I'm very frustrated with how this has been handled."

NON_COMPLAINT_TRANSCRIPT="Customer: Hi, I'd like to check my account balance please. Agent: Of course, I can help you with that. Your current balance is \$1,234.56. Customer: Great, thank you for your help!"

test_payload() {
    local name="$1"
    local payload="$2"
    
    echo "----------------------------------------"
    echo "Test: $name"
    echo "----------------------------------------"
    
    response=$(curl -s -X POST "$LOCAL_SERVER_URL/invoke" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>&1)
    
    echo "Response:"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    echo ""
    
    if echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); exit(0 if 'result' in data or 'status' in data else 1)" 2>/dev/null; then
        echo "✓ Response structure valid"
    else
        echo "✗ Response structure invalid"
    fi
    echo ""
}

echo ""
echo "Running test cases..."
echo ""

test_payload "Complaint Transcript" "{\"transcript\": \"$COMPLAINT_TRANSCRIPT\"}"

test_payload "Non-Complaint Transcript" "{\"transcript\": \"$NON_COMPLAINT_TRANSCRIPT\"}"

test_payload "Missing Transcript Field" "{\"message\": \"This should fail\"}"

test_payload "Empty Transcript" "{\"transcript\": \"\"}"

echo "=== Testing Complete ==="
