#!/usr/bin/env python3
"""CDK Application entry point for AgentCore deployment.

Supports deploying supervisor agent, complaints agent MCP, or both.
Use context variables to control deployment:
  - deploy_supervisor: Deploy the supervisor agent stack (default: true)
  - deploy_complaints_mcp: Deploy the complaints agent MCP stack (default: true)
  - environment: Deployment environment name (default: dev)

Examples:
  cdk deploy --all                                    # Deploy both stacks
  cdk deploy -c deploy_complaints_mcp=false           # Deploy only supervisor
  cdk deploy -c deploy_supervisor=false               # Deploy only complaints MCP
  cdk deploy ComplaintsAgentMCP-dev                   # Deploy specific stack
"""

import os

import aws_cdk as cdk

from stacks.agentcore_stack import AgentCoreDeploymentStack
from stacks.complaints_agent_stack import ComplaintsAgentMCPStack


app = cdk.App()

environment = app.node.try_get_context("environment") or os.environ.get("ENVIRONMENT", "dev")
deploy_supervisor = app.node.try_get_context("deploy_supervisor") != "false"
deploy_complaints_mcp = app.node.try_get_context("deploy_complaints_mcp") != "false"

bedrock_model_ids = [
    "us.anthropic.claude-sonnet-4-6",
]

cdk_env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
)

if deploy_supervisor:
    AgentCoreDeploymentStack(
        app,
        f"ComplaintsAgentCore-{environment}",
        environment=environment,
        bedrock_model_ids=bedrock_model_ids,
        env=cdk_env,
    )

if deploy_complaints_mcp:
    ComplaintsAgentMCPStack(
        app,
        f"ComplaintsAgentMCP-{environment}",
        environment=environment,
        bedrock_model_ids=bedrock_model_ids,
        env=cdk_env,
    )

app.synth()
