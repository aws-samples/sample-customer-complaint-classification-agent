# Design Document: Codebase Cleanup

## Overview

This design consolidates duplicate code across the complaints-agent repository into shared utilities, removes excessive documentation, and simplifies the codebase for AgentCore newcomers. The cleanup targets ~25-30% code reduction while preserving all functionality.

## Architecture

The cleanup introduces a new `utils` module containing shared JSON parsing and serialization logic. Model classes will use a mixin for serialization, and test files will share strategies via conftest.py.

```
src/complaints_agent/
├── agents/
│   ├── complaints_agent.py    # Simplified, uses utils
│   └── supervisor_agent.py    # Simplified, uses utils
├── models/
│   ├── __init__.py
│   ├── base.py                # NEW: Serializable mixin
│   ├── complaint.py           # Uses Serializable
│   ├── complaint_response.py  # Uses Serializable
│   ├── complaint_criteria.py  # Uses Serializable
│   └── agent_response.py      # Uses Serializable
├── utils/
│   ├── __init__.py            # NEW
│   └── json_parser.py         # NEW: Consolidated JSON parsing
├── config/
│   └── loader.py
└── ui/
    ├── streaming.py           # Simplified, uses utils
    └── ...

tests/
├── conftest.py                # NEW: Shared Hypothesis strategies
└── property/
    └── ...                    # Simplified, uses conftest strategies
```

## Components and Interfaces

### Serializable Mixin (models/base.py)

Provides automatic JSON serialization for dataclasses.

```python
from dataclasses import asdict, fields
from datetime import datetime
from typing import TypeVar, get_type_hints
import json

T = TypeVar('T', bound='Serializable')

class Serializable:
    def to_json(self) -> str:
        def serialize_value(val):
            if isinstance(val, datetime):
                return val.isoformat()
            if isinstance(val, Serializable):
                return json.loads(val.to_json())
            return val
        
        data = {}
        for field in fields(self):
            val = getattr(self, field.name)
            data[field.name] = serialize_value(val)
        return json.dumps(data)
    
    @classmethod
    def from_json(cls: type[T], json_str: str) -> T:
        data = json.loads(json_str)
        hints = get_type_hints(cls)
        kwargs = {}
        for field in fields(cls):
            val = data.get(field.name)
            field_type = hints.get(field.name)
            if val is not None:
                if field_type == datetime:
                    val = datetime.fromisoformat(val)
                elif hasattr(field_type, 'from_json') and isinstance(val, dict):
                    val = field_type.from_json(json.dumps(val))
            kwargs[field.name] = val
        return cls(**kwargs)
```

### JSON Parser (utils/json_parser.py)

Consolidates all JSON extraction and parsing logic.

```python
def find_json_objects(text: str) -> list[dict]:
    """Extract all valid JSON objects from text with proper brace matching."""
    ...

def parse_agent_response(text: str) -> dict:
    """Parse JSON from agent response, handling markdown blocks."""
    ...

def parse_classification_response(text: str) -> dict:
    """Parse classification JSON, filtering out tool inputs and complaint responses."""
    ...

def extract_complaint_response(text: str) -> ComplaintResponse | None:
    """Extract ComplaintResponse from text if present."""
    ...

def extract_from_tool_results(messages: list) -> ComplaintResponse | None:
    """Extract ComplaintResponse from agent message history."""
    ...
```

### Simplified Model Classes

Each model becomes a simple dataclass inheriting from Serializable:

```python
@dataclass
class Complaint(Serializable):
    transcript: str
    classification_result: str
    timestamp: datetime
    matched_criteria: list[str] = field(default_factory=list)
```

### Shared Test Strategies (tests/conftest.py)

```python
from hypothesis import strategies as st

severity_strategy = st.sampled_from(["low", "medium", "high", "critical"])
category_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
actions_strategy = st.lists(st.text(min_size=1, max_size=200).filter(lambda x: x.strip()), max_size=5)
next_steps_strategy = st.lists(st.text(min_size=1, max_size=200).filter(lambda x: x.strip()), max_size=5)
transcript_strategy = st.text(min_size=1, max_size=500).filter(lambda x: x.strip())
matched_criteria_strategy = st.lists(st.text(min_size=1, max_size=50).filter(lambda x: x.strip()), max_size=5)
summary_strategy = st.text(min_size=1, max_size=500).filter(lambda x: x.strip())

@st.composite
def complaint_response_strategy(draw):
    return ComplaintResponse(
        severity=draw(severity_strategy),
        category=draw(category_strategy),
        actions_taken=draw(actions_strategy),
        next_steps=draw(next_steps_strategy)
    )
```

## Data Models

No changes to the data model structure - only the implementation of serialization moves to the mixin.

| Model | Fields | Notes |
|-------|--------|-------|
| Complaint | transcript, classification_result, timestamp, matched_criteria | timestamp is datetime |
| ComplaintResponse | severity, category, actions_taken, next_steps | All strings/lists |
| ComplaintCriteria | keywords, sentiment_indicators, severity_thresholds | severity_thresholds is dict |
| AgentResponse | is_complaint, summary, complaint, complaint_response | Contains nested models |



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Serialization Round-Trip

*For any* valid Model object (Complaint, ComplaintResponse, ComplaintCriteria, or AgentResponse), serializing it to JSON and deserializing it back SHALL produce an equivalent object with identical field values, including datetime fields and nested Model objects.

**Validates: Requirements 1.3, 1.4, 1.5**

### Property 2: JSON Extraction Completeness

*For any* text containing one or more valid JSON objects (whether as plain JSON, within markdown code blocks, or embedded in prose), find_json_objects() SHALL return all valid JSON objects found, correctly handling nested braces and escaped characters.

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 3: Classification Parsing Correctness

*For any* text containing multiple JSON objects of different types (classification responses, tool inputs, complaint responses), parse_classification_response() SHALL return only the classification JSON (containing "classification" and "reasoning" fields), excluding tool inputs and complaint responses.

**Validates: Requirements 2.4, 6.2, 6.3**

### Property 4: Response Extraction Validation

*For any* text containing a mix of valid ComplaintResponse JSON objects and invalid/error responses, extract_complaint_response() SHALL return only valid ComplaintResponse objects with all required fields (severity, category, actions_taken, next_steps), skipping error responses.

**Validates: Requirements 3.3, 3.4**

## Error Handling

| Scenario | Handling |
|----------|----------|
| Invalid JSON in text | find_json_objects() skips invalid JSON, returns only valid objects |
| Missing required fields | extract_complaint_response() returns None |
| Error response in tool results | Skipped, continues searching for valid response |
| Empty/whitespace text | Returns empty list or None as appropriate |
| Malformed datetime string | Raises ValueError during deserialization |

## Testing Strategy

### Dual Testing Approach

The cleanup preserves existing unit tests while consolidating property-based tests to use shared strategies.

**Unit Tests**: Verify specific examples, edge cases, and error conditions
- Existing tests in `tests/test_*.py` remain unchanged
- Focus on integration points and specific scenarios

**Property Tests**: Verify universal properties across all inputs
- Use Hypothesis with minimum 100 iterations per property
- Import strategies from `tests/conftest.py`
- Each property test references its design document property

### Property-Based Testing Configuration

- Library: Hypothesis (already in use)
- Minimum iterations: 100 per property
- Tag format: `Feature: codebase-cleanup, Property N: {property_text}`

### Test File Changes

1. Create `tests/conftest.py` with shared strategies
2. Update property test files to import from conftest
3. Remove duplicate strategy definitions from individual test files
4. Ensure all existing tests pass after refactoring
