#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Complaints Agent Deployment ==="
echo "Environment: $ENVIRONMENT"
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
check_command "aws"
check_command "python3"

if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS credentials not configured or invalid"
    echo "Please run 'aws configure' or set AWS environment variables"
    exit 1
fi
echo "AWS credentials: OK"

if ! python3 -c "import bedrock_agentcore" &> /dev/null; then
    echo "Installing bedrock-agentcore..."
    python3 -m pip install bedrock-agentcore
fi

if ! command -v agentcore &> /dev/null; then
    echo "Installing bedrock-agentcore-starter-toolkit..."
    python3 -m pip install bedrock-agentcore-starter-toolkit
fi
echo "AgentCore CLI: OK"

echo ""
echo "Installing project dependencies..."
cd "$PROJECT_ROOT"
python3 -m pip install -r requirements.txt

echo ""
echo "Configuring AgentCore agent..."
agentcore configure --entrypoint agent.py --non-interactive

echo ""
echo "Deploying to AgentCore..."
agentcore launch

echo ""
echo "=== Deployment Complete ==="
echo "Environment: $ENVIRONMENT"
echo ""
echo "To invoke the agent:"
echo "  agentcore invoke --payload '{\"transcript\": \"your transcript here\"}'"
echo ""
echo "To destroy the deployment:"
echo "  agentcore destroy"
