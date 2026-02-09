#!/usr/bin/env python3
"""CDK Application entry point for AgentCore deployment."""

import os

import aws_cdk as cdk

from stacks.agentcore_stack import AgentCoreDeploymentStack


app = cdk.App()

environment = app.node.try_get_context("environment") or os.environ.get("ENVIRONMENT", "dev")

bedrock_model_ids = [
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
    "us.anthropic.claude-sonnet-4-20250514-v1:0",
]

AgentCoreDeploymentStack(
    app,
    f"ComplaintsAgentCore-{environment}",
    environment=environment,
    bedrock_model_ids=bedrock_model_ids,
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
    ),
)

app.synth()
