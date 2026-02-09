"""Property-based tests for environment parameterization.

Feature: agentcore-deployment, Property 5: Environment Parameterization
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "infra"))

import aws_cdk as cdk
from aws_cdk.assertions import Template
from hypothesis import given, settings, strategies as st

from stacks.agentcore_stack import AgentCoreDeploymentStack


ENVIRONMENTS = ["dev", "staging", "prod"]
VALID_MODEL_IDS = [
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
]


class TestEnvironmentParameterization:
    """
    Feature: agentcore-deployment, Property 5: Environment Parameterization
    
    *For any* two different environment configurations (dev, staging, prod), 
    instantiating the CDK stack with different environment parameters SHALL 
    produce stacks with distinct resource names and appropriate environment-specific tags.
    
    **Validates: Requirements 4.7**
    """

    @settings(max_examples=10)
    @given(
        env1=st.sampled_from(ENVIRONMENTS),
        env2=st.sampled_from(ENVIRONMENTS),
    )
    def test_different_environments_produce_distinct_role_names(
        self, env1: str, env2: str
    ):
        """Different environments produce distinct IAM role names."""
        app1 = cdk.App()
        stack1 = AgentCoreDeploymentStack(
            app1,
            f"TestStack-{env1}",
            environment=env1,
            bedrock_model_ids=VALID_MODEL_IDS,
        )
        
        app2 = cdk.App()
        stack2 = AgentCoreDeploymentStack(
            app2,
            f"TestStack-{env2}",
            environment=env2,
            bedrock_model_ids=VALID_MODEL_IDS,
        )
        
        template1 = Template.from_stack(stack1)
        template2 = Template.from_stack(stack2)
        
        roles1 = template1.find_resources("AWS::IAM::Role")
        roles2 = template2.find_resources("AWS::IAM::Role")
        
        role_name1 = None
        role_name2 = None
        for role in roles1.values():
            if "RoleName" in role.get("Properties", {}):
                role_name1 = role["Properties"]["RoleName"]
        for role in roles2.values():
            if "RoleName" in role.get("Properties", {}):
                role_name2 = role["Properties"]["RoleName"]
        
        if env1 != env2:
            assert role_name1 != role_name2
        else:
            assert role_name1 == role_name2

    @settings(max_examples=10)
    @given(environment=st.sampled_from(ENVIRONMENTS))
    def test_environment_tag_applied_to_stack(self, environment: str):
        """Stack has Environment tag matching the configured environment."""
        app = cdk.App()
        stack = AgentCoreDeploymentStack(
            app,
            "TestStack",
            environment=environment,
            bedrock_model_ids=VALID_MODEL_IDS,
        )
        
        template = Template.from_stack(stack)
        roles = template.find_resources("AWS::IAM::Role")
        
        for role in roles.values():
            tags = role.get("Properties", {}).get("Tags", [])
            env_tags = [t for t in tags if t.get("Key") == "Environment"]
            assert len(env_tags) == 1
            assert env_tags[0]["Value"] == environment

    @settings(max_examples=10)
    @given(environment=st.sampled_from(ENVIRONMENTS))
    def test_environment_output_matches_parameter(self, environment: str):
        """CloudFormation output for Environment matches the input parameter."""
        app = cdk.App()
        stack = AgentCoreDeploymentStack(
            app,
            "TestStack",
            environment=environment,
            bedrock_model_ids=VALID_MODEL_IDS,
        )
        
        template = Template.from_stack(stack)
        
        template.has_output(
            "Environment",
            {"Value": environment}
        )

    @settings(max_examples=10)
    @given(environment=st.sampled_from(ENVIRONMENTS))
    def test_stack_exposes_environment_property(self, environment: str):
        """Stack exposes env_name property matching the configured environment."""
        app = cdk.App()
        stack = AgentCoreDeploymentStack(
            app,
            "TestStack",
            environment=environment,
            bedrock_model_ids=VALID_MODEL_IDS,
        )
        
        assert stack.env_name == environment
