# Implementation Plan: Codebase Cleanup

## Overview

This plan consolidates duplicate code into shared utilities, removes excessive documentation, and simplifies the codebase. Tasks are ordered to build incrementally, with each step validating functionality before proceeding.

## Tasks

- [ ] 1. Create shared utilities module
  - [x] 1.1 Create `src/complaints_agent/utils/__init__.py` and `src/complaints_agent/utils/json_parser.py`
    - Implement `find_json_objects()` - extract JSON from text with proper brace matching
    - Implement `parse_agent_response()` - parse JSON from agent responses
    - Implement `parse_classification_response()` - parse classification JSON, filtering tool inputs
    - Implement `extract_complaint_response()` - extract ComplaintResponse from text
    - Implement `extract_from_tool_results()` - extract from agent message history
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 6.1, 6.2, 6.3, 6.4_

  - [x] 1.2 Write property test for JSON extraction
    - **Property 2: JSON Extraction Completeness**
    - **Validates: Requirements 2.1, 2.2, 2.3**

  - [x] 1.3 Write property test for classification parsing
    - **Property 3: Classification Parsing Correctness**
    - **Validates: Requirements 2.4, 6.2, 6.3**

  - [x] 1.4 Write property test for response extraction
    - **Property 4: Response Extraction Validation**
    - **Validates: Requirements 3.3, 3.4**

- [ ] 2. Create Serializable mixin for models
  - [ ] 2.1 Create `src/complaints_agent/models/base.py` with Serializable mixin
    - Implement `to_json()` method handling datetime and nested Serializable objects
    - Implement `from_json()` classmethod with type hint introspection
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 2.2 Write property test for serialization round-trip
    - **Property 1: Serialization Round-Trip**
    - **Validates: Requirements 1.3, 1.4, 1.5**

- [x] 3. Checkpoint - Verify utilities work
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Refactor model classes to use Serializable
  - [x] 4.1 Update `complaint.py` to inherit from Serializable, remove to_json/from_json
    - Remove verbose docstrings from trivial methods
    - _Requirements: 1.2, 4.1, 4.2_

  - [x] 4.2 Update `complaint_response.py` to inherit from Serializable, remove to_json/from_json
    - Remove verbose docstrings from trivial methods
    - _Requirements: 1.2, 4.1, 4.2_

  - [x] 4.3 Update `complaint_criteria.py` to inherit from Serializable, remove to_json/from_json
    - Remove verbose docstrings from trivial methods
    - _Requirements: 1.2, 4.1, 4.2_

  - [x] 4.4 Update `agent_response.py` to inherit from Serializable, remove to_json/from_json
    - Handle nested Complaint and ComplaintResponse objects
    - Remove verbose docstrings from trivial methods
    - _Requirements: 1.2, 1.4, 4.1, 4.2_

  - [x] 4.5 Update `src/complaints_agent/models/__init__.py` exports
    - _Requirements: 1.2_

- [x] 5. Checkpoint - Verify models work
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Refactor agents to use shared utilities
  - [x] 6.1 Update `complaints_agent.py` to use `json_parser.parse_agent_response()`
    - Remove duplicate `_parse_agent_response()` function
    - Remove excessive docstrings
    - _Requirements: 2.1, 4.1, 4.2, 4.3_

  - [x] 6.2 Update `supervisor_agent.py` to use shared JSON parsing utilities
    - Remove duplicate `_parse_classification_response()` function
    - Remove duplicate `_find_all_json_objects()` method
    - Remove duplicate `_extract_complaint_response()` method
    - Remove duplicate `_extract_from_tool_results()` method
    - Remove duplicate `_parse_complaint_response_from_text()` method
    - Remove excessive docstrings
    - _Requirements: 2.1, 2.4, 3.1, 3.2, 4.1, 4.2, 4.3, 6.1_

  - [x] 6.3 Update `streaming.py` to use shared JSON parsing utilities
    - Remove duplicate `_find_all_json_objects()` method
    - Remove duplicate `_extract_complaint_response()` method
    - Remove duplicate `_extract_from_tool_results()` method
    - Remove duplicate `_parse_complaint_response_from_text()` method
    - Remove excessive docstrings
    - _Requirements: 2.1, 3.1, 3.2, 4.1, 4.2, 4.3_

- [x] 7. Checkpoint - Verify agents work
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Consolidate test fixtures
  - [x] 8.1 Create `tests/conftest.py` with shared Hypothesis strategies
    - Define severity_strategy, category_strategy, actions_strategy, next_steps_strategy
    - Define transcript_strategy, matched_criteria_strategy, summary_strategy
    - Define composite strategies for Complaint, ComplaintResponse, AgentResponse
    - _Requirements: 5.1, 5.3_

  - [x] 8.2 Update property test files to import strategies from conftest
    - Remove duplicate strategy definitions from each test file
    - _Requirements: 5.2, 5.4_

- [ ] 9. Consolidate dependency management
  - [x] 9.1 Update `pyproject.toml` with all dependencies
    - Add streamlit, bedrock-agentcore to main dependencies
    - Add aws-cdk-lib, constructs as `[infra]` optional extras
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 9.2 Remove `requirements.txt`
    - _Requirements: 7.4_

- [ ] 10. Final cleanup and verification
  - [x] 10.1 Remove any remaining excessive docstrings and comments
    - Keep only docstrings that explain non-obvious logic
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 10.2 Run all tests to verify functionality preserved
    - _Requirements: 8.3_

- [x] 11. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Existing unit tests verify specific examples and edge cases
