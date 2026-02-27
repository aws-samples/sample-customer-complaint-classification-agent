"""Complaints Agent MCP CDK Stack.

This stack defines the AWS infrastructure for deploying the standalone
Complaints Agent MCP server to Amazon Bedrock AgentCore runtime.
"""

from aws_cdk import (
    CfnOutput,
    Stack,
    Tags,
    aws_iam as iam,
)
from constructs import Construct


class ComplaintsAgentMCPStack(Stack):
    """CDK Stack for Complaints Agent MCP deployment infrastructure."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        environment: str,
        bedrock_model_ids: list[str],
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self._env_name = environment
        self._bedrock_model_ids = bedrock_model_ids

        self.execution_role = self._create_execution_role()
        self._add_outputs()
        self._apply_tags()

    @property
    def env_name(self) -> str:
        """Return the deployment environment name."""
        return self._env_name

    @property
    def model_ids(self) -> list[str]:
        """Return the configured Bedrock model IDs."""
        return self._bedrock_model_ids

    def _create_execution_role(self) -> iam.Role:
        """Create IAM execution role with least-privilege permissions for the MCP agent."""
        execution_role = iam.Role(
            self,
            "ComplaintsAgentMCPExecutionRole",
            role_name=f"complaints-agent-mcp-execution-{self._env_name}",
            assumed_by=iam.ServicePrincipal("agentcore.bedrock.amazonaws.com"),
            description=f"Execution role for Complaints Agent MCP Server in AgentCore ({self._env_name})",
        )

        model_arns = [
            f"arn:aws:bedrock:{self.region}::foundation-model/{model_id}"
            for model_id in self._bedrock_model_ids
        ]

        bedrock_policy = iam.PolicyStatement(
            sid="BedrockInvokeModel",
            effect=iam.Effect.ALLOW,
            actions=["bedrock:InvokeModel"],
            resources=model_arns,
        )
        execution_role.add_to_policy(bedrock_policy)

        return execution_role

    def _add_outputs(self) -> None:
        """Add CloudFormation outputs for the stack."""
        CfnOutput(
            self,
            "ExecutionRoleArn",
            value=self.execution_role.role_arn,
            description="ARN of the Complaints Agent MCP execution role",
            export_name=f"ComplaintsAgentMCP-ExecutionRoleArn-{self._env_name}",
        )

        CfnOutput(
            self,
            "ExecutionRoleName",
            value=self.execution_role.role_name or "",
            description="Name of the Complaints Agent MCP execution role",
        )

        CfnOutput(
            self,
            "Environment",
            value=self._env_name,
            description="Deployment environment",
        )

        CfnOutput(
            self,
            "AgentEndpoint",
            value=f"https://agentcore.{self.region}.amazonaws.com/agents/complaints-agent-mcp-{self._env_name}",
            description="Placeholder endpoint URL for the Complaints Agent MCP server",
            export_name=f"ComplaintsAgentMCP-Endpoint-{self._env_name}",
        )

        CfnOutput(
            self,
            "MCPProtocol",
            value="mcp",
            description="Protocol used for agent communication",
        )

    def _apply_tags(self) -> None:
        """Apply tags for environment and MCP protocol identification."""
        Tags.of(self).add("Environment", self._env_name)
        Tags.of(self).add("Application", "complaints-agent-mcp")
        Tags.of(self).add("Protocol", "MCP")
        Tags.of(self).add("AgentType", "standalone")
        Tags.of(self).add("ManagedBy", "CDK")
