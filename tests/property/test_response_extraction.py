"""Property-based tests for response extraction validation.

Feature: codebase-cleanup, Property 4: Response Extraction Validation
"""

import json

from hypothesis import given, settings, strategies as st

from src.complaints_agent.utils.json_parser import extract_complaint_response
from src.complaints_agent.models.complaint_response import ComplaintResponse


severity_strategy = st.sampled_from(["low", "medium", "high", "critical"])

category_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())

actions_strategy = st.lists(
    st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    min_size=0,
    max_size=5
)

next_steps_strategy = st.lists(
    st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    min_size=0,
    max_size=5
)


@st.composite
def valid_complaint_response_json_strategy(draw):
    """Generate valid ComplaintResponse JSON objects with all required fields."""
    return {
        "severity": draw(severity_strategy),
        "category": draw(category_strategy),
        "actions_taken": draw(actions_strategy),
        "next_steps": draw(next_steps_strategy)
    }


@st.composite
def error_response_json_strategy(draw):
    """Generate error response JSON objects (with status: 'error')."""
    base = draw(valid_complaint_response_json_strategy())
    base["status"] = "error"
    return base


@st.composite
def missing_severity_json_strategy(draw):
    """Generate JSON missing the severity field."""
    return {
        "category": draw(category_strategy),
        "actions_taken": draw(actions_strategy),
        "next_steps": draw(next_steps_strategy)
    }


@st.composite
def missing_category_json_strategy(draw):
    """Generate JSON missing the category field."""
    return {
        "severity": draw(severity_strategy),
        "actions_taken": draw(actions_strategy),
        "next_steps": draw(next_steps_strategy)
    }


@st.composite
def missing_actions_taken_json_strategy(draw):
    """Generate JSON missing the actions_taken field."""
    return {
        "severity": draw(severity_strategy),
        "category": draw(category_strategy),
        "next_steps": draw(next_steps_strategy)
    }


@st.composite
def missing_next_steps_json_strategy(draw):
    """Generate JSON missing the next_steps field."""
    return {
        "severity": draw(severity_strategy),
        "category": draw(category_strategy),
        "actions_taken": draw(actions_strategy)
    }


prose_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'), blacklist_characters='{}[]"\\'),
    min_size=0,
    max_size=100
)


class TestResponseExtractionValidation:
    """
    Feature: codebase-cleanup, Property 4: Response Extraction Validation

    *For any* text containing a mix of valid ComplaintResponse JSON objects and
    invalid/error responses, extract_complaint_response() SHALL return only valid
    ComplaintResponse objects with all required fields (severity, category,
    actions_taken, next_steps), skipping error responses.

    **Validates: Requirements 3.3, 3.4**
    """

    @settings(max_examples=10)
    @given(valid_response=valid_complaint_response_json_strategy())
    def test_extracts_valid_complaint_response_from_plain_json(self, valid_response: dict):
        """Valid ComplaintResponse JSON is extracted correctly from plain text."""
        text = json.dumps(valid_response)
        result = extract_complaint_response(text)
        assert result is not None
        assert isinstance(result, ComplaintResponse)
        assert result.severity == valid_response["severity"]
        assert result.category == valid_response["category"]
        assert result.actions_taken == valid_response["actions_taken"]
        assert result.next_steps == valid_response["next_steps"]

    @settings(max_examples=10)
    @given(valid_response=valid_complaint_response_json_strategy())
    def test_extracts_valid_complaint_response_from_markdown(self, valid_response: dict):
        """Valid ComplaintResponse JSON is extracted from markdown code blocks."""
        json_str = json.dumps(valid_response)
        text = f"Here is the response:\n```json\n{json_str}\n```"
        result = extract_complaint_response(text)
        assert result is not None
        assert isinstance(result, ComplaintResponse)
        assert result.severity == valid_response["severity"]
        assert result.category == valid_response["category"]

    @settings(max_examples=10)
    @given(
        valid_response=valid_complaint_response_json_strategy(),
        prefix=prose_strategy,
        suffix=prose_strategy
    )
    def test_extracts_valid_complaint_response_from_prose(
        self, valid_response: dict, prefix: str, suffix: str
    ):
        """Valid ComplaintResponse JSON is extracted from prose text."""
        json_str = json.dumps(valid_response)
        text = f"{prefix} {json_str} {suffix}"
        result = extract_complaint_response(text)
        assert result is not None
        assert isinstance(result, ComplaintResponse)
        assert result.severity == valid_response["severity"]
        assert result.category == valid_response["category"]

    @settings(max_examples=10)
    @given(error_response=error_response_json_strategy())
    def test_skips_error_responses(self, error_response: dict):
        """Error responses (with status: 'error') are skipped."""
        text = json.dumps(error_response)
        result = extract_complaint_response(text)
        assert result is None

    @settings(max_examples=10)
    @given(
        valid_response=valid_complaint_response_json_strategy(),
        error_response=error_response_json_strategy()
    )
    def test_returns_valid_response_when_error_response_present(
        self, valid_response: dict, error_response: dict
    ):
        """Valid response is returned when error response is also present."""
        error_json = json.dumps(error_response)
        valid_json = json.dumps(valid_response)
        text = f"Error: {error_json}\nValid: {valid_json}"
        result = extract_complaint_response(text)
        assert result is not None
        assert isinstance(result, ComplaintResponse)
        assert result.severity == valid_response["severity"]
        assert result.category == valid_response["category"]

    @settings(max_examples=10)
    @given(
        error_response=error_response_json_strategy(),
        valid_response=valid_complaint_response_json_strategy()
    )
    def test_skips_error_and_finds_valid_regardless_of_order(
        self, error_response: dict, valid_response: dict
    ):
        """Valid response is found regardless of order with error response."""
        valid_json = json.dumps(valid_response)
        error_json = json.dumps(error_response)
        text = f"Valid: {valid_json}\nError: {error_json}"
        result = extract_complaint_response(text)
        assert result is not None
        assert isinstance(result, ComplaintResponse)
        assert result.severity == valid_response["severity"]

    @settings(max_examples=10)
    @given(missing_severity=missing_severity_json_strategy())
    def test_skips_response_missing_severity(self, missing_severity: dict):
        """Responses missing severity field are skipped."""
        text = json.dumps(missing_severity)
        result = extract_complaint_response(text)
        assert result is None

    @settings(max_examples=10)
    @given(missing_category=missing_category_json_strategy())
    def test_skips_response_missing_category(self, missing_category: dict):
        """Responses missing category field are skipped."""
        text = json.dumps(missing_category)
        result = extract_complaint_response(text)
        assert result is None

    @settings(max_examples=10)
    @given(missing_actions=missing_actions_taken_json_strategy())
    def test_skips_response_missing_actions_taken(self, missing_actions: dict):
        """Responses missing actions_taken field are skipped."""
        text = json.dumps(missing_actions)
        result = extract_complaint_response(text)
        assert result is None

    @settings(max_examples=10)
    @given(missing_next_steps=missing_next_steps_json_strategy())
    def test_skips_response_missing_next_steps(self, missing_next_steps: dict):
        """Responses missing next_steps field are skipped."""
        text = json.dumps(missing_next_steps)
        result = extract_complaint_response(text)
        assert result is None

    @settings(max_examples=10)
    @given(
        valid_response=valid_complaint_response_json_strategy(),
        missing_severity=missing_severity_json_strategy()
    )
    def test_returns_valid_when_incomplete_response_present(
        self, valid_response: dict, missing_severity: dict
    ):
        """Valid response is returned when incomplete response is also present."""
        incomplete_json = json.dumps(missing_severity)
        valid_json = json.dumps(valid_response)
        text = f"Incomplete: {incomplete_json}\nValid: {valid_json}"
        result = extract_complaint_response(text)
        assert result is not None
        assert isinstance(result, ComplaintResponse)
        assert result.severity == valid_response["severity"]
        assert result.category == valid_response["category"]

    @settings(max_examples=10)
    @given(
        valid_response=valid_complaint_response_json_strategy(),
        error_response=error_response_json_strategy(),
        missing_category=missing_category_json_strategy()
    )
    def test_returns_valid_from_mixed_invalid_responses(
        self, valid_response: dict, error_response: dict, missing_category: dict
    ):
        """Valid response is returned from text with multiple invalid responses."""
        error_json = json.dumps(error_response)
        missing_json = json.dumps(missing_category)
        valid_json = json.dumps(valid_response)
        text = f"Error: {error_json}\nMissing: {missing_json}\nValid: {valid_json}"
        result = extract_complaint_response(text)
        assert result is not None
        assert isinstance(result, ComplaintResponse)
        assert result.severity == valid_response["severity"]
        assert result.category == valid_response["category"]

    @settings(max_examples=10)
    @given(st.text(min_size=0, max_size=200).filter(lambda x: '{' not in x))
    def test_returns_none_for_text_without_json(self, text: str):
        """Text without JSON returns None."""
        result = extract_complaint_response(text)
        assert result is None

    @settings(max_examples=10)
    @given(valid_response=valid_complaint_response_json_strategy())
    def test_extracted_response_has_all_required_fields(self, valid_response: dict):
        """Extracted ComplaintResponse has all required fields populated."""
        text = json.dumps(valid_response)
        result = extract_complaint_response(text)
        assert result is not None
        assert hasattr(result, 'severity')
        assert hasattr(result, 'category')
        assert hasattr(result, 'actions_taken')
        assert hasattr(result, 'next_steps')
        assert result.severity is not None
        assert result.category is not None
        assert isinstance(result.actions_taken, list)
        assert isinstance(result.next_steps, list)
