# Complaints Analysis — AWS Bedrock AgentCore Demo

An agentic solution for analyzing customer call transcripts using [Strands Agents SDK](https://github.com/strands-agents/sdk-python) and [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/). A Supervisor Agent classifies transcripts and routes complaints to a specialized Complaints Agent for severity assessment, categorization, and team routing.

The system includes a Streamlit web interface, AWS CDK infrastructure, and two deployment modes: fully local or fully deployed on AgentCore.

## Architecture

There are two ways to run this demo:

**Local mode** — everything runs on your machine, no AWS deployment needed:

```
┌──────────────────────────────────────────────────────┐
│                  Streamlit Web UI                    │
│  ┌─────────────┐ ┌────────────┐ ┌──────────────────┐ │
│  │Conversation │ │ Evaluation │ │ Agent Actions    │ │
│  └──────┬──────┘ └────────────┘ └──────────────────┘ │
│         │                                            │
│         ▼                                            │
│  ┌─────────────────────┐                             │
│  │  Supervisor Agent   │  Classifies transcript      │
│  │  (in-process)       │                             │
│  └──────┬──────────────┘                             │
│         │ complaint detected                         │
│         ▼                                            │
│  ┌─────────────────────┐                             │
│  │  Complaints Agent   │  Severity, routing, actions │
│  │  (local tool)       │                             │
│  └─────────────────────┘                             │
└──────────────────────────────────────────────────────┘
```

**Deployed mode** — agents run on AWS Bedrock AgentCore:

```
┌──────────────────────────┐
│    Streamlit Web UI      │
└──────────┬───────────────┘
           │ invokes
           ▼
┌──────────────────────────┐     ┌──────────────────────────┐
│  Supervisor Agent        │────▶│  Complaints Agent        │
│  (AgentCore Runtime)     │ MCP │  (AgentCore Gateway)     │
└──────────────────────────┘     └──────────────────────────┘
```

## Prerequisites

- Python 3.10+
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) configured with credentials
- [AWS CDK CLI](https://docs.aws.amazon.com/cdk/v2/guide/getting-started.html) (`npm install -g aws-cdk`)
- [AgentCore CLI](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-cli.html) (`pip install bedrock-agentcore`)
- Docker (for container-based AgentCore deployments)
- Access to Amazon Bedrock foundation models (Claude Sonnet 4.6 by default)
- Permissions to invoke the Agent on AgentCore (deployed solution) or just invoke the model (using solution locally).

## Getting Started

### 1. Clone and install

```bash
git clone <repository-url>
cd <repository-name>
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project and its dependencies:

```bash
python3 -m pip install -e ".[infra]"
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
BEDROCK_TEMPERATURE=0.0
OTEL_SDK_DISABLED=true
```

### 3. Run the Streamlit UI (local mode)

This runs both agents locally — only requires AWS permissions for calls to Amazon Bedrock for generation:

```bash
# If using AWS IAM Identity Center
aws sso config
export AWS_DEFAULT_PROFILE='<profile_name>'
aws sso login
```
```bash
# Run from root of repository
streamlit run streamlit_app.py
```

The UI opens at `http://localhost:8501`. You can:
- Upload a `.txt` transcript file from the sidebar
- Select a built-in demo conversation (Billing Dispute or Account Inquiry)
- View classification results, severity, routing, and recommended actions

## Deploying to AWS (Deployed Mode)

When you're ready to move beyond local mode, deploy both agents to AgentCore. The Supervisor Agent runs on AgentCore Runtime and the Complaints Agent runs on AgentCore Gateway as an MCP server.

### 4. Deploy CDK infrastructure

The CDK stacks create IAM execution roles that AgentCore needs to invoke Bedrock models.

```bash
cd infra
cdk bootstrap  # first time only
cdk deploy --all
```

This deploys two stacks:
- `ComplaintsAgentCore-dev` — IAM role for the Supervisor Agent (AgentCore Runtime)
- `ComplaintsAgentMCP-dev` — IAM role for the Complaints Agent (AgentCore Gateway)

Note the `ExecutionRoleArn` outputs — you'll need them for the AgentCore deployment step.

### 5. Deploy agents to AgentCore

After the CDK stacks are deployed, use the AgentCore CLI to deploy each agent.

**Deploy the Complaints Agent MCP server** (AgentCore Gateway):

```bash
cd agents/complaints-agent
agentcore deploy
```

This deploys the `complaints-agent` with `MCP` protocol to AgentCore Gateway.

**Deploy the Supervisor Agent** (AgentCore Runtime, from the project root):

```bash
agentcore deploy
```

This deploys the `complaints-supervisor` agent with `CUSTOM` protocol to AgentCore Runtime. The Supervisor discovers and calls the Complaints Agent MCP server through AgentCore.

### 6. Connect Streamlit to AgentCore

Once both agents are deployed, point the Streamlit UI at the Supervisor Agent endpoint:

```bash
streamlit run streamlit_app.py
```

In the sidebar, toggle "Use AgentCore deployment" and enter the Supervisor Agent's AgentCore endpoint URL. The Supervisor handles routing to the Complaints Agent internally — you don't need to configure the MCP endpoint separately.

## Project Structure

```
├── agent.py                          # Supervisor agent AgentCore entry point
├── agents/
│   └── complaints-agent/
│       ├── agent.py                  # Complaints MCP agent AgentCore entry point
│       └── src/complaints_agent_mcp/ # MCP server implementation
├── config/
│   └── complaint_criteria.json       # Keywords, sentiment indicators, severity thresholds
├── infra/
│   ├── app.py                        # CDK app entry point
│   └── stacks/
│       ├── agentcore_stack.py        # Supervisor agent IAM stack
│       └── complaints_agent_stack.py # Complaints MCP agent IAM stack
├── sample_transcripts/               # Example transcripts for testing
├── shared/                           # Shared agent logic and models
│   ├── complaints/agent_logic.py     # Core complaints processing logic
│   ├── models/                       # Shared data models
│   └── parsing/                      # JSON response parsing
├── src/complaint_system/
│   ├── agents/                       # Supervisor and complaints agent wrappers
│   ├── config/                       # Configuration loader
│   ├── models/                       # Domain models
│   ├── ui/                           # Streamlit web interface
│   └── utils/                        # Utilities
├── pyproject.toml                    # Python project config and dependencies
├── Dockerfile                        # Supervisor agent container
└── .env.example                      # Environment variable template
```

## How It Works

1. A customer call transcript is submitted through the Streamlit UI (file upload or demo conversation)
2. The Supervisor Agent reads the transcript and classifies it as `complaint` or `non_complaint` using configurable keywords and sentiment indicators from `config/complaint_criteria.json`
3. If classified as a complaint, the Supervisor calls the Complaints Agent (locally in local mode, or via MCP through AgentCore in deployed mode)
4. The Complaints Agent determines severity, category, routing group, actions taken, and next steps
5. Results stream back to the UI across three panels: Conversation, Evaluation, and Agent Actions
6. For complaints, an approval gate lets you review recommended actions before they execute

## License

MIT
