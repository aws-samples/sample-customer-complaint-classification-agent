#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Complaints Agent Local Development Server ==="
echo "Project Root: $PROJECT_ROOT"
echo ""

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "Error: $1 is not installed or not in PATH"
        echo "Please install $1 before running this script"
        exit 1
    fi
}

echo "Checking prerequisites..."
check_command "python3"

if ! command -v agentcore &> /dev/null; then
    echo "Installing bedrock-agentcore-starter-toolkit..."
    python3 -m pip install bedrock-agentcore-starter-toolkit
fi
echo "AgentCore CLI: OK"

cd "$PROJECT_ROOT"

if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found in project root"
    exit 1
fi

echo "Installing dependencies..."
python3 -m pip install -r requirements.txt

echo ""
echo "Starting local development server with hot reloading..."
echo "Press Ctrl+C to stop"
echo ""

agentcore dev --port 8080
