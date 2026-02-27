# Handling customer complaints using Amazon Bedrock AgentCore

A demonstration of building an agentic solution for customer complaint analysis using the Strands Agents SDK and Amazon Bedrock.

## Overview

This project implements a multi-agent system that analyzes customer call transcripts to identify and process complaints. A supervisor agent classifies incoming transcripts and routes identified complaints to a specialized complaints agent for severity assessment and action recommendations.

The system is designed to run locally via Streamlit or deploy to Amazon Bedrock AgentCore.

## Architecture

- **Supervisor Agent**: Classifies transcripts as complaints or non-complaints based on configurable keywords and sentiment indicators
- **Complaints Agent**: Analyzes identified complaints to determine severity, category, recommended actions, and next steps

## Requirements

- Python 3.10+
- AWS credentials configured for Bedrock access
- Claude model access in Amazon Bedrock

## Installation

```bash
python3 -m pip install -e .
```

For development:

```bash
python3 -m pip install -e ".[dev]"
```

## Running Locally

Start the Streamlit interface:

```bash
streamlit run streamlit_app.py
```

## Configuration

Complaint classification criteria are defined in `config/complaint_criteria.json`. This includes:

- Keywords that indicate a complaint
- Sentiment indicators for negative customer sentiment
- Severity thresholds for classification

## Deployment

Infrastructure is defined using AWS CDK in the `infra/` directory. The project includes two stacks:

- **ComplaintsAgentCore**: Provisions IAM execution role for the supervisor agent
- **ComplaintsAgentMCP**: Provisions IAM execution role for the standalone complaints agent MCP server

### Prerequisites

1. AWS CLI configured with appropriate credentials
2. AWS CDK CLI installed (`npm install -g aws-cdk`)
3. Bootstrap CDK in your account/region (if not already done):

```bash
cdk bootstrap aws://ACCOUNT_ID/REGION
```

### Install Infrastructure Dependencies

```bash
python3 -m pip install -e ".[infra]"
```

### Deploy Both Stacks

```bash
cd infra
cdk deploy --all
```

### Deploy Individual Stacks

Deploy only the supervisor agent stack:

```bash
cd infra
cdk deploy ComplaintsAgentCore-dev
```

Deploy only the complaints agent MCP stack:

```bash
cd infra
cdk deploy ComplaintsAgentMCP-dev
```

### Deployment Options

Use CDK context variables to control deployment:

```bash
cdk deploy -c deploy_supervisor=false      # Skip supervisor stack
cdk deploy -c deploy_complaints_mcp=false  # Skip MCP stack
cdk deploy -c environment=prod             # Deploy to prod environment
```

### Stack Outputs

After deployment, the stacks output:

- **ExecutionRoleArn**: IAM role ARN for AgentCore
- **ExecutionRoleName**: IAM role name
- **Environment**: Deployment environment name
- **AgentEndpoint** (MCP stack only): Placeholder endpoint URL

## Testing

```bash
python3 -m pytest tests/
```

The test suite includes property-based tests using Hypothesis to verify correctness properties of the classification and response handling logic.

## Project Structure

```
├── agent.py                 # AgentCore entry point
├── streamlit_app.py         # Local Streamlit interface
├── config/                  # Classification criteria configuration
├── src/complaints_agent/    # Core agent implementation
│   ├── agents/              # Supervisor and complaints agents
│   ├── models/              # Data models
│   ├── ui/                  # Streamlit UI components
│   └── utils/               # JSON parsing utilities
├── infra/                   # CDK infrastructure
└── tests/                   # Unit and property-based tests
```

## License

MIT
