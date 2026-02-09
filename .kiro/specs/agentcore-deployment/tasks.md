# Implementation Plan: AgentCore Deployment

## Overview

This plan implements the containerization and deployment of the existing Strands-based complaints agent to AWS using Amazon Bedrock AgentCore. Tasks are organized to build incrementally, starting with the entry point wrapper, then infrastructure, and finally deployment automation.

## Tasks

- [x] 1. Create AgentCore Entry Point Wrapper
  - [x] 1.1 Create agent.py with BedrockAgentCoreApp wrapper
    - Import BedrockAgentCoreApp from bedrock_agentcore
    - Define invoke function with @app.entrypoint decorator
    - Implement payload validation and error handling
    - Wire up SupervisorAgent for transcript processing
    - Serialize AgentResponse to JSON for return
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [x] 1.2 Write property test for response serialization round-trip
    - **Property 1: Response Serialization Round-Trip**
    - **Validates: Requirements 1.4, 9.3**

  - [x] 1.3 Write property test for invalid input error handling
    - **Property 2: Invalid Input Error Handling**
    - **Validates: Requirements 1.5, 9.5**

  - [x] 1.4 Write property test for exception error response structure
    - **Property 3: Exception Error Response Structure**
    - **Validates: Requirements 1.6, 9.4**

- [x] 2. Update Dependencies and Configuration
  - [x] 2.1 Update requirements.txt with bedrock-agentcore dependency
    - Add bedrock-agentcore package
    - Preserve existing strands-agents dependencies
    - Add aws-cdk-lib and constructs for CDK
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 2.2 Create configuration helper module for environment-aware config loading
    - Implement get_config_path() with environment variable override
    - Add validation for configuration files
    - Raise ConfigurationError for invalid configs
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 2.3 Write property test for configuration override via environment
    - **Property 6: Configuration Override via Environment**
    - **Validates: Requirements 8.2**

  - [x] 2.4 Write property test for configuration validation fail-fast
    - **Property 7: Configuration Validation Fail-Fast**
    - **Validates: Requirements 8.3**

- [ ] 3. Checkpoint - Verify entry point and configuration
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Create Container Configuration
  - [x] 4.1 Create Dockerfile for AgentCore deployment
    - Use Python 3.12 base image
    - Copy source code, config, and requirements
    - Install dependencies
    - Set PYTHONPATH and entry point
    - Add non-root user for security
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 4.2 Create .dockerignore file
    - Exclude tests, __pycache__, .git, .kiro
    - _Requirements: 3.6_

- [x] 5. Create CDK Infrastructure Stack
  - [x] 5.1 Initialize CDK project structure
    - Create infra/ directory with CDK app
    - Create cdk.json configuration
    - Create app.py entry point
    - _Requirements: 4.1_

  - [x] 5.2 Implement AgentCoreDeploymentStack
    - Create IAM execution role with trust policy for AgentCore
    - Add bedrock:InvokeModel permissions for specified model IDs
    - Configure environment variables
    - Add CloudFormation outputs for role ARN
    - Support environment parameterization (dev/staging/prod)
    - Apply tags for environment identification
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6, 4.7, 5.1, 5.2, 5.3, 5.5_

  - [x] 5.3 Write property test for IAM least privilege policy
    - **Property 4: IAM Least Privilege Policy**
    - **Validates: Requirements 5.1, 5.2, 5.5**

  - [x] 5.4 Write property test for environment parameterization
    - **Property 5: Environment Parameterization**
    - **Validates: Requirements 4.7**

  - [x] 5.5 Write CDK snapshot tests for stack template
    - Verify CloudFormation template structure
    - _Requirements: 4.1, 4.2_

- [x] 6. Checkpoint - Verify CDK stack synthesizes correctly
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Create Deployment Scripts
  - [x] 7.1 Create scripts/deploy.sh for deployment automation
    - Validate prerequisites (AWS CLI, agentcore CLI)
    - Configure agent with agentcore configure
    - Deploy with agentcore launch
    - Support environment parameter
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 7.2 Create scripts/local-dev.sh for local development
    - Start local dev server with agentcore dev
    - Support hot reloading
    - _Requirements: 7.1, 7.2_

  - [x] 7.3 Create scripts/test-local.sh for local testing
    - Send test payloads to local dev server
    - Verify response structure
    - _Requirements: 7.2_

- [x] 8. Implement Request/Response Contract Validation
  - [x] 8.1 Add request validation to entry point wrapper
    - Validate transcript field presence and content
    - Handle optional config_override field
    - Return structured error responses
    - _Requirements: 9.1, 9.2, 9.4, 9.5_

  - [x] 8.2 Write property test for request contract validation
    - **Property 8: Request Contract Validation**
    - **Validates: Requirements 9.1, 9.2**

- [x] 9. Verify Local Development Workflow
  - [x] 9.1 Ensure main.py demo script still works
    - Verify backward compatibility
    - _Requirements: 7.3_

  - [x] 9.2 Write property test for local/production config consistency
    - **Property 9: Local/Production Configuration Consistency**
    - **Validates: Requirements 7.4**

- [x] 10. Final Checkpoint - Complete integration verification
  - Ensure all tests pass, ask the user if questions arise.
  - Verify local dev server starts and responds correctly
  - Verify CDK stack synthesizes without errors

## Notes

- All tasks including property-based tests are required
- Each task references specific requirements for traceability
- Property tests use the hypothesis library already in project dependencies
- CDK tests use aws_cdk.assertions for template verification
- Local development uses `agentcore dev` command from bedrock-agentcore-starter-toolkit
