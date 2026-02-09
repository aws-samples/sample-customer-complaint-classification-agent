"""CDK snapshot tests for AgentCore deployment stack.

Verifies CloudFormation template structure for Requirements 4.1, 4.2.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "infra"))

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from stacks.agentcore_stack import AgentCoreDeploymentStack


VALID_MODEL_IDS = [
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
]


class TestAgentCoreDeploymentStack:
    """Tests for AgentCore deployment CDK stack template structure."""

    def test_stack_creates_iam_role(self):
        """Stack creates an IAM execution role."""
        app = cdk.App()
        stack = AgentCoreDeploymentStack(
            app,
            "TestStack",
            environment="dev",
            bedrock_model_ids=VALID_MODEL_IDS,
        )
        
        template = Template.from_stack(stack)
        template.resource_count_is("AWS::IAM::Role", 1)

    def test_stack_creates_iam_policy(self):
        """Stack creates an IAM policy for Bedrock access."""
        app = cdk.App()
        stack = AgentCoreDeploymentStack(
            app,
            "TestStack",
            environment="dev",
            bedrock_model_ids=VALID_MODEL_IDS,
        )
        
        template = Template.from_stack(stack)
        template.resource_count_is("AWS::IAM::Policy", 1)

    def test_stack_has_execution_role_arn_output(self):
        """Stack exports the execution role ARN."""
        app = cdk.App()
        stack = AgentCoreDeploymentStack(
            app,
            "TestStack",
            environment="dev",
            bedrock_model_ids=VALID_MODEL_IDS,
        )
        
        template = Template.from_stack(stack)
        template.has_output(
            "ExecutionRoleArn",
            {
                "Description": "ARN of the AgentCore execution role",
                "Export": {"Name": "ComplaintsAgent-ExecutionRoleArn-dev"},
            }
        )

    def test_stack_has_environment_output(self):
        """Stack exports the environment name."""
        app = cdk.App()
        stack = AgentCoreDeploymentStack(
            app,
            "TestStack",
            environment="staging",
            bedrock_model_ids=VALID_MODEL_IDS,
        )
        
        template = Template.from_stack(stack)
        template.has_output(
            "Environment",
            {"Value": "staging"}
        )

    def test_iam_role_has_correct_trust_policy(self):
        """IAM role trusts AgentCore service."""
        app = cdk.App()
        stack = AgentCoreDeploymentStack(
            app,
            "TestStack",
            environment="dev",
            bedrock_model_ids=VALID_MODEL_IDS,
        )
        
        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "AssumeRolePolicyDocument": {
                    "Statement": [
                        {
                            "Action": "sts:AssumeRole",
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "agentcore.bedrock.amazonaws.com"
                            }
                        }
                    ],
                    "Version": "2012-10-17"
                }
            }
        )

    def test_iam_policy_has_bedrock_invoke_permission(self):
        """IAM policy grants bedrock:InvokeModel permission."""
        app = cdk.App()
        stack = AgentCoreDeploymentStack(
            app,
            "TestStack",
            environment="dev",
            bedrock_model_ids=VALID_MODEL_IDS,
        )
        
        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with([
                        Match.object_like({
                            "Action": "bedrock:InvokeModel",
                            "Effect": "Allow",
                        })
                    ])
                }
            }
        )

    def test_stack_applies_required_tags(self):
        """Stack applies Application and ManagedBy tags."""
        app = cdk.App()
        stack = AgentCoreDeploymentStack(
            app,
            "TestStack",
            environment="prod",
            bedrock_model_ids=VALID_MODEL_IDS,
        )
        
        template = Template.from_stack(stack)
        roles = template.find_resources("AWS::IAM::Role")
        
        for role in roles.values():
            tags = role.get("Properties", {}).get("Tags", [])
            tag_keys = [t["Key"] for t in tags]
            assert "Environment" in tag_keys
            assert "Application" in tag_keys
            assert "ManagedBy" in tag_keys

    def test_snapshot_dev_environment(self):
        """Snapshot test for dev environment stack template."""
        app = cdk.App()
        stack = AgentCoreDeploymentStack(
            app,
            "TestStack",
            environment="dev",
            bedrock_model_ids=VALID_MODEL_IDS,
        )
        
        template = Template.from_stack(stack)
        template_json = template.to_json()
        
        assert "Resources" in template_json
        assert "Outputs" in template_json
        
        resources = template_json["Resources"]
        assert any("Role" in r for r in resources)
        assert any("Policy" in r for r in resources)

    def test_snapshot_prod_environment(self):
        """Snapshot test for prod environment stack template."""
        app = cdk.App()
        stack = AgentCoreDeploymentStack(
            app,
            "TestStack",
            environment="prod",
            bedrock_model_ids=VALID_MODEL_IDS,
        )
        
        template = Template.from_stack(stack)
        template_json = template.to_json()
        
        assert "Resources" in template_json
        assert "Outputs" in template_json
        
        outputs = template_json["Outputs"]
        env_output = outputs.get("Environment", {})
        assert env_output.get("Value") == "prod"
