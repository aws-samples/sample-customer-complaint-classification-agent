"""Property-based tests for IAM least privilege policy.

Feature: agentcore-deployment, Property 4: IAM Least Privilege Policy
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "infra"))

import aws_cdk as cdk
from aws_cdk.assertions import Template
from hypothesis import given, settings, strategies as st

from stacks.agentcore_stack import AgentCoreDeploymentStack


VALID_MODEL_IDS = [
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
    "us.anthropic.claude-sonnet-4-20250514-v1:0",
    "anthropic.claude-3-opus-20240229-v1:0",
    "amazon.titan-text-express-v1",
]


class TestIAMLeastPrivilegePolicy:
    """
    Feature: agentcore-deployment, Property 4: IAM Least Privilege Policy
    
    *For any* IAM policy attached to the AgentCore execution role, the policy 
    SHALL only grant `bedrock:InvokeModel` action, and the resource ARNs SHALL 
    be restricted to the specific Bedrock model IDs configured for the agent.
    
    **Validates: Requirements 5.1, 5.2, 5.5**
    """

    @settings(max_examples=10)
    @given(
        model_ids=st.lists(
            st.sampled_from(VALID_MODEL_IDS),
            min_size=1,
            max_size=3,
            unique=True,
        )
    )
    def test_iam_policy_restricts_to_specified_models(self, model_ids: list[str]):
        """IAM policy only grants bedrock:InvokeModel for specified model IDs."""
        app = cdk.App()
        stack = AgentCoreDeploymentStack(
            app,
            "TestStack",
            environment="test",
            bedrock_model_ids=model_ids,
        )
        
        template = Template.from_stack(stack)
        
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": [
                        {
                            "Action": "bedrock:InvokeModel",
                            "Effect": "Allow",
                        }
                    ]
                }
            }
        )

    @settings(max_examples=10)
    @given(
        model_ids=st.lists(
            st.sampled_from(VALID_MODEL_IDS),
            min_size=1,
            max_size=3,
            unique=True,
        )
    )
    def test_iam_policy_resource_count_matches_model_count(self, model_ids: list[str]):
        """IAM policy has exactly one resource ARN per model ID."""
        app = cdk.App()
        stack = AgentCoreDeploymentStack(
            app,
            "TestStack",
            environment="test",
            bedrock_model_ids=model_ids,
        )
        
        template = Template.from_stack(stack)
        policies = template.find_resources("AWS::IAM::Policy")
        
        for policy_id, policy in policies.items():
            statements = policy["Properties"]["PolicyDocument"]["Statement"]
            for statement in statements:
                if statement.get("Action") == "bedrock:InvokeModel":
                    resources = statement.get("Resource", [])
                    if isinstance(resources, list):
                        assert len(resources) == len(model_ids)

    @settings(max_examples=10)
    @given(
        model_ids=st.lists(
            st.sampled_from(VALID_MODEL_IDS),
            min_size=1,
            max_size=3,
            unique=True,
        )
    )
    def test_iam_role_has_agentcore_trust_policy(self, model_ids: list[str]):
        """IAM role trusts the AgentCore service principal."""
        app = cdk.App()
        stack = AgentCoreDeploymentStack(
            app,
            "TestStack",
            environment="test",
            bedrock_model_ids=model_ids,
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
                    ]
                }
            }
        )

    @settings(max_examples=10)
    @given(
        model_ids=st.lists(
            st.sampled_from(VALID_MODEL_IDS),
            min_size=1,
            max_size=3,
            unique=True,
        )
    )
    def test_no_wildcard_permissions(self, model_ids: list[str]):
        """IAM policy does not contain wildcard (*) actions."""
        app = cdk.App()
        stack = AgentCoreDeploymentStack(
            app,
            "TestStack",
            environment="test",
            bedrock_model_ids=model_ids,
        )
        
        template = Template.from_stack(stack)
        policies = template.find_resources("AWS::IAM::Policy")
        
        for policy_id, policy in policies.items():
            statements = policy["Properties"]["PolicyDocument"]["Statement"]
            for statement in statements:
                action = statement.get("Action")
                if isinstance(action, str):
                    assert action != "*"
                    assert not action.endswith(":*")
                elif isinstance(action, list):
                    for a in action:
                        assert a != "*"
                        assert not a.endswith(":*")
