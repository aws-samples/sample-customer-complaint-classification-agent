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

Infrastructure is defined using AWS CDK in the `infra/` directory. The stack provisions an IAM execution role for AgentCore deployment.

```bash
python3 -m pip install -e ".[infra]"
cd infra
cdk deploy
```

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
