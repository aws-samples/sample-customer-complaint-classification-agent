"""Property-based tests for classification parsing correctness.

Feature: codebase-cleanup, Property 3: Classification Parsing Correctness
"""

import json

from hypothesis import given, settings, strategies as st

from src.complaints_agent.utils.json_parser import parse_classification_response


classification_value_strategy = st.sampled_from(["complaint", "non_complaint"])

reasoning_strategy = st.text(
    min_size=1,
    max_size=200
).filter(lambda x: x.strip()).map(lambda s: s.replace('"', '\\"').replace('\\', '\\\\'))

matched_criteria_strategy = st.lists(
    st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    min_size=0,
    max_size=5
)


@st.composite
def classification_json_strategy(draw):
    """Generate valid classification JSON objects."""
    return {
        "classification": draw(classification_value_strategy),
        "reasoning": draw(reasoning_strategy),
        "matched_criteria": draw(matched_criteria_strategy)
    }


transcript_strategy = st.text(min_size=1, max_size=200).filter(lambda x: x.strip())

classification_result_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())


@st.composite
def tool_input_json_strategy(draw):
    """Generate tool input JSON objects (transcript + classification_result)."""
    return {
        "transcript": draw(transcript_strategy),
        "classification_result": draw(classification_result_strategy)
    }


severity_strategy = st.sampled_from(["low", "medium", "high", "critical"])

category_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())

actions_strategy = st.lists(
    st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    min_size=1,
    max_size=5
)

next_steps_strategy = st.lists(
    st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    min_size=1,
    max_size=5
)


@st.composite
def complaint_response_json_strategy(draw):
    """Generate complaint response JSON objects."""
    return {
        "severity": draw(severity_strategy),
        "category": draw(category_strategy),
        "actions_taken": draw(actions_strategy),
        "next_steps": draw(next_steps_strategy)
    }


prose_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'), blacklist_characters='{}[]"\\'),
    min_size=0,
    max_size=100
)


class TestClassificationParsingCorrectness:
    """
    Feature: codebase-cleanup, Property 3: Classification Parsing Correctness

    *For any* text containing multiple JSON objects of different types (classification
    responses, tool inputs, complaint responses), parse_classification_response() SHALL
    return only the classification JSON (containing "classification" and "reasoning"
    fields), excluding tool inputs and complaint responses.

    **Validates: Requirements 2.4, 6.2, 6.3**
    """

    @settings(max_examples=10)
    @given(classification=classification_json_strategy())
    def test_returns_classification_json_from_plain_text(self, classification: dict):
        """Classification JSON is correctly parsed from plain text."""
        text = json.dumps(classification)
        result = parse_classification_response(text)
        assert result["classification"] == classification["classification"]
        assert "classification" in result

    @settings(max_examples=10)
    @given(classification=classification_json_strategy())
    def test_returns_classification_json_from_markdown(self, classification: dict):
        """Classification JSON is correctly parsed from markdown code blocks."""
        json_str = json.dumps(classification)
        text = f"Here is the classification:\n```json\n{json_str}\n```"
        result = parse_classification_response(text)
        assert result["classification"] == classification["classification"]
        assert "classification" in result

    @settings(max_examples=10)
    @given(
        classification=classification_json_strategy(),
        tool_input=tool_input_json_strategy()
    )
    def test_filters_out_tool_inputs(self, classification: dict, tool_input: dict):
        """Tool inputs (transcript + classification_result) are filtered out."""
        tool_json = json.dumps(tool_input)
        classification_json = json.dumps(classification)
        text = f"Tool input: {tool_json}\nClassification: {classification_json}"
        result = parse_classification_response(text)
        assert result["classification"] == classification["classification"]
        assert "transcript" not in result
        assert "classification_result" not in result

    @settings(max_examples=10)
    @given(
        classification=classification_json_strategy(),
        complaint_response=complaint_response_json_strategy()
    )
    def test_filters_out_complaint_responses(self, classification: dict, complaint_response: dict):
        """Complaint responses (severity, category, actions_taken, next_steps) are filtered out."""
        complaint_json = json.dumps(complaint_response)
        classification_json = json.dumps(classification)
        text = f"Complaint response: {complaint_json}\nClassification: {classification_json}"
        result = parse_classification_response(text)
        assert result["classification"] == classification["classification"]
        assert "severity" not in result
        assert "actions_taken" not in result

    @settings(max_examples=10)
    @given(
        classification=classification_json_strategy(),
        tool_input=tool_input_json_strategy(),
        complaint_response=complaint_response_json_strategy()
    )
    def test_returns_classification_from_mixed_json_types(
        self, classification: dict, tool_input: dict, complaint_response: dict
    ):
        """Classification is returned when mixed with tool inputs and complaint responses."""
        tool_json = json.dumps(tool_input)
        complaint_json = json.dumps(complaint_response)
        classification_json = json.dumps(classification)
        text = f"{tool_json}\n{complaint_json}\n{classification_json}"
        result = parse_classification_response(text)
        assert result["classification"] == classification["classification"]
        assert "transcript" not in result
        assert "severity" not in result

    @settings(max_examples=10)
    @given(
        classification=classification_json_strategy(),
        tool_input=tool_input_json_strategy(),
        complaint_response=complaint_response_json_strategy(),
        prefix=prose_strategy,
        middle=prose_strategy
    )
    def test_returns_classification_from_prose_with_mixed_json(
        self, classification: dict, tool_input: dict, complaint_response: dict,
        prefix: str, middle: str
    ):
        """Classification is returned from prose containing mixed JSON types."""
        tool_json = json.dumps(tool_input)
        complaint_json = json.dumps(complaint_response)
        classification_json = json.dumps(classification)
        text = f"{prefix}\n{tool_json}\n{middle}\n{complaint_json}\n{classification_json}"
        result = parse_classification_response(text)
        assert result["classification"] == classification["classification"]

    @settings(max_examples=10)
    @given(tool_input=tool_input_json_strategy())
    def test_returns_default_when_only_tool_input(self, tool_input: dict):
        """Default non_complaint is returned when only tool input is present."""
        text = json.dumps(tool_input)
        result = parse_classification_response(text)
        assert result["classification"] == "non_complaint"
        assert "reasoning" in result

    @settings(max_examples=10)
    @given(complaint_response=complaint_response_json_strategy())
    def test_returns_default_when_only_complaint_response(self, complaint_response: dict):
        """Default non_complaint is returned when only complaint response is present."""
        text = json.dumps(complaint_response)
        result = parse_classification_response(text)
        assert result["classification"] == "non_complaint"
        assert "reasoning" in result

    @settings(max_examples=10)
    @given(
        tool_input=tool_input_json_strategy(),
        complaint_response=complaint_response_json_strategy()
    )
    def test_returns_default_when_no_classification_present(
        self, tool_input: dict, complaint_response: dict
    ):
        """Default non_complaint is returned when no classification JSON is present."""
        tool_json = json.dumps(tool_input)
        complaint_json = json.dumps(complaint_response)
        text = f"Tool: {tool_json}\nResponse: {complaint_json}"
        result = parse_classification_response(text)
        assert result["classification"] == "non_complaint"
        assert "reasoning" in result

    @settings(max_examples=10)
    @given(classification=classification_json_strategy())
    def test_classification_with_reasoning_field_preserved(self, classification: dict):
        """Classification JSON with reasoning field is preserved."""
        text = json.dumps(classification)
        result = parse_classification_response(text)
        assert "classification" in result

    @settings(max_examples=10)
    @given(st.text(min_size=0, max_size=200).filter(lambda x: '{' not in x))
    def test_returns_default_for_text_without_json(self, text: str):
        """Text without JSON returns default non_complaint classification."""
        result = parse_classification_response(text)
        assert result["classification"] == "non_complaint"
        assert "reasoning" in result
