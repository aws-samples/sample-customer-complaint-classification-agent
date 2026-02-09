# Requirements Document

## Introduction

This document defines requirements for cleaning up and consolidating the complaints-agent repository to reduce complexity and make it accessible for newcomers to AgentCore. The cleanup focuses on eliminating duplicate code, removing excessive documentation, and creating shared utilities.

## Glossary

- **Model**: A dataclass representing domain objects (Complaint, ComplaintResponse, ComplaintCriteria, AgentResponse)
- **JSON_Parser**: Utility module for extracting and parsing JSON from agent response text
- **Serializable**: A mixin or base providing to_json()/from_json() methods for dataclasses
- **Hypothesis_Strategy**: A reusable data generator for property-based testing
- **Conftest**: pytest's shared fixture configuration file

## Requirements

### Requirement 1: Unified JSON Serialization

**User Story:** As a developer, I want model classes to use a shared serialization approach, so that I don't have to maintain duplicate to_json()/from_json() implementations.

#### Acceptance Criteria

1. THE Serializable mixin SHALL provide to_json() and from_json() methods for dataclasses
2. WHEN a Model uses Serializable, THE Model SHALL serialize all fields to JSON without custom implementation
3. WHEN deserializing, THE Serializable SHALL handle datetime fields by converting ISO format strings
4. WHEN deserializing, THE Serializable SHALL handle nested Model objects by recursively deserializing them
5. FOR ALL Model objects, serializing then deserializing SHALL produce an equivalent object (round-trip property)

### Requirement 2: Consolidated JSON Parsing

**User Story:** As a developer, I want a single JSON parsing utility, so that I don't have duplicate parsing logic across multiple files.

#### Acceptance Criteria

1. THE JSON_Parser SHALL extract JSON objects from plain text, markdown code blocks, and raw JSON strings
2. WHEN parsing agent responses, THE JSON_Parser SHALL handle nested braces and escaped characters correctly
3. WHEN multiple JSON objects exist in text, THE JSON_Parser SHALL return all valid JSON objects found
4. THE JSON_Parser SHALL distinguish between classification responses, tool inputs, and complaint responses
5. IF no valid JSON is found, THEN THE JSON_Parser SHALL return an empty list or appropriate default

### Requirement 3: Consolidated Response Extraction

**User Story:** As a developer, I want response extraction logic in one place, so that SupervisorAgent and StreamingSupervisorAgent share the same implementation.

#### Acceptance Criteria

1. THE JSON_Parser SHALL provide extract_complaint_response() for extracting ComplaintResponse from text
2. THE JSON_Parser SHALL provide extract_from_tool_results() for extracting responses from agent message history
3. WHEN extracting responses, THE JSON_Parser SHALL validate required fields (severity, category, actions_taken, next_steps)
4. WHEN an error response is encountered, THE JSON_Parser SHALL skip it and continue searching

### Requirement 4: Docstring Cleanup

**User Story:** As a developer, I want only meaningful docstrings in the codebase, so that the code is concise and readable.

#### Acceptance Criteria

1. THE codebase SHALL retain docstrings only for functions and classes that require explanation
2. THE codebase SHALL remove docstrings from trivial methods like to_json(), from_json(), and simple getters
3. THE codebase SHALL remove inline comments except where they explain non-obvious logic
4. WHEN a function's purpose is clear from its name and signature, THE function SHALL NOT have a docstring

### Requirement 5: Consolidated Test Fixtures

**User Story:** As a developer, I want shared Hypothesis strategies in conftest.py, so that property tests don't duplicate strategy definitions.

#### Acceptance Criteria

1. THE conftest.py SHALL define reusable Hypothesis strategies for severity, category, actions, next_steps, transcript, and matched_criteria
2. WHEN a property test needs a strategy, THE test SHALL import it from conftest.py
3. THE conftest.py SHALL provide composite strategies for generating complete Model objects
4. THE test files SHALL NOT define duplicate strategies that exist in conftest.py

### Requirement 6: Simplified Classification Parsing

**User Story:** As a developer, I want classification parsing to be straightforward, so that newcomers can understand the logic quickly.

#### Acceptance Criteria

1. THE JSON_Parser SHALL provide parse_classification_response() with clear, linear logic
2. THE parse_classification_response() SHALL prioritize JSON blocks with "classification" and "reasoning" fields
3. THE parse_classification_response() SHALL exclude tool inputs and complaint responses from classification candidates
4. IF parsing fails, THEN THE JSON_Parser SHALL return a default non_complaint classification

### Requirement 7: Consolidated Dependency Management

**User Story:** As a developer, I want a single source of truth for dependencies, so that I don't have to maintain both requirements.txt and pyproject.toml.

#### Acceptance Criteria

1. THE pyproject.toml SHALL be the single source for all dependencies
2. THE pyproject.toml SHALL include all runtime dependencies (strands-agents, streamlit, bedrock-agentcore)
3. THE pyproject.toml SHALL include infrastructure dependencies (aws-cdk-lib, constructs) as optional extras
4. THE requirements.txt file SHALL be removed from the repository
5. WHEN installing the project, THE developer SHALL use `pip install -e .` or `pip install -e .[dev,infra]`

### Requirement 8: Code Reduction Target

**User Story:** As a maintainer, I want the codebase reduced by approximately 25-30%, so that it's easier to maintain and understand.

#### Acceptance Criteria

1. THE cleanup SHALL reduce total lines of code by at least 25%
2. THE cleanup SHALL eliminate duplicate implementations across files
3. THE cleanup SHALL preserve all existing functionality and test coverage
4. THE cleanup SHALL not introduce new dependencies beyond the standard library
