"""Unit tests for the json_parser utility module."""

import json
import pytest

from src.complaints_agent.utils.json_parser import (
    find_json_objects,
    parse_agent_response,
    parse_classification_response,
    extract_complaint_response,
    extract_from_tool_results,
)
from src.complaints_agent.models.complaint_response import ComplaintResponse


class TestFindJsonObjects:
    """Tests for find_json_objects function."""

    def test_empty_text_returns_empty_list(self):
        assert find_json_objects("") == []
        assert find_json_objects(None) == []

    def test_plain_json_object(self):
        text = '{"key": "value"}'
        result = find_json_objects(text)
        assert len(result) == 1
        assert result[0] == {"key": "value"}

    def test_json_in_markdown_code_block(self):
        text = '''Here is some JSON:
```json
{"classification": "complaint", "reasoning": "test"}
```
'''
        result = find_json_objects(text)
        assert len(result) == 1
        assert result[0]["classification"] == "complaint"

    def test_multiple_json_objects(self):
        text = '{"first": 1} some text {"second": 2}'
        result = find_json_objects(text)
        assert len(result) == 2
        assert {"first": 1} in result
        assert {"second": 2} in result

    def test_nested_braces(self):
        text = '{"outer": {"inner": "value"}}'
        result = find_json_objects(text)
        assert len(result) == 1
        assert result[0] == {"outer": {"inner": "value"}}

    def test_escaped_characters_in_strings(self):
        text = '{"message": "He said \\"hello\\""}'
        result = find_json_objects(text)
        assert len(result) == 1
        assert result[0]["message"] == 'He said "hello"'

    def test_braces_inside_strings_ignored(self):
        text = '{"text": "contains { and } braces"}'
        result = find_json_objects(text)
        assert len(result) == 1
        assert result[0]["text"] == "contains { and } braces"


class TestParseAgentResponse:
    """Tests for parse_agent_response function."""

    def test_empty_text_returns_empty_dict(self):
        assert parse_agent_response("") == {}
        assert parse_agent_response(None) == {}

    def test_direct_json_parsing(self):
        text = '{"severity": "high", "category": "fraud"}'
        result = parse_agent_response(text)
        assert result == {"severity": "high", "category": "fraud"}

    def test_json_in_markdown_block(self):
        text = '''Here is the response:
```json
{"severity": "medium"}
```
'''
        result = parse_agent_response(text)
        assert result["severity"] == "medium"

    def test_returns_first_json_object(self):
        text = '{"first": 1} {"second": 2}'
        result = parse_agent_response(text)
        assert result == {"first": 1}


class TestParseClassificationResponse:
    """Tests for parse_classification_response function."""

    def test_empty_text_returns_default(self):
        result = parse_classification_response("")
        assert result["classification"] == "non_complaint"
        assert result["matched_criteria"] == []

    def test_valid_classification_json(self):
        text = '{"classification": "complaint", "matched_criteria": ["frustrated"], "reasoning": "Customer expressed frustration"}'
        result = parse_classification_response(text)
        assert result["classification"] == "complaint"
        assert "frustrated" in result["matched_criteria"]

    def test_filters_tool_call_inputs(self):
        text = '''
{"transcript": "test", "classification_result": "complaint"}
{"classification": "complaint", "matched_criteria": [], "reasoning": "test"}
'''
        result = parse_classification_response(text)
        assert "transcript" not in result
        assert result["classification"] == "complaint"

    def test_filters_complaint_responses(self):
        text = '''
{"severity": "high", "category": "fraud", "actions_taken": [], "next_steps": []}
{"classification": "complaint", "matched_criteria": [], "reasoning": "test"}
'''
        result = parse_classification_response(text)
        assert "severity" not in result
        assert result["classification"] == "complaint"

    def test_prioritizes_classification_with_reasoning(self):
        text = '''
{"classification": "non_complaint"}
{"classification": "complaint", "matched_criteria": ["angry"], "reasoning": "Customer was angry"}
'''
        result = parse_classification_response(text)
        assert result["classification"] == "complaint"
        assert "reasoning" in result


class TestExtractComplaintResponse:
    """Tests for extract_complaint_response function."""

    def test_empty_text_returns_none(self):
        assert extract_complaint_response("") is None
        assert extract_complaint_response(None) is None

    def test_missing_required_fields_returns_none(self):
        text = '{"severity": "high"}'
        assert extract_complaint_response(text) is None

    def test_valid_complaint_response(self):
        text = '{"severity": "high", "category": "fraud", "actions_taken": ["logged"], "next_steps": ["follow up"]}'
        result = extract_complaint_response(text)
        assert isinstance(result, ComplaintResponse)
        assert result.severity == "high"
        assert result.category == "fraud"
        assert result.actions_taken == ["logged"]
        assert result.next_steps == ["follow up"]

    def test_skips_error_responses(self):
        text = '''
{"status": "error", "severity": "high", "category": "fraud", "actions_taken": [], "next_steps": []}
{"severity": "medium", "category": "billing", "actions_taken": ["reviewed"], "next_steps": ["contact"]}
'''
        result = extract_complaint_response(text)
        assert result is not None
        assert result.severity == "medium"
        assert result.category == "billing"


class TestExtractFromToolResults:
    """Tests for extract_from_tool_results function."""

    def test_empty_messages_returns_none(self):
        assert extract_from_tool_results([]) is None
        assert extract_from_tool_results(None) is None

    def test_no_tool_results_returns_none(self):
        messages = [
            {"role": "assistant", "content": [{"text": "Hello"}]},
            {"role": "user", "content": [{"text": "Hi"}]},
        ]
        assert extract_from_tool_results(messages) is None

    def test_extracts_from_tool_result(self):
        complaint_json = json.dumps({
            "severity": "high",
            "category": "fraud",
            "actions_taken": ["logged"],
            "next_steps": ["escalate"]
        })
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "toolResult": {
                            "content": [{"text": complaint_json}]
                        }
                    }
                ]
            }
        ]
        result = extract_from_tool_results(messages)
        assert isinstance(result, ComplaintResponse)
        assert result.severity == "high"
        assert result.category == "fraud"

    def test_skips_error_tool_results(self):
        error_json = json.dumps({
            "status": "error",
            "severity": "high",
            "category": "fraud",
            "actions_taken": [],
            "next_steps": []
        })
        valid_json = json.dumps({
            "severity": "medium",
            "category": "billing",
            "actions_taken": ["reviewed"],
            "next_steps": ["contact"]
        })
        messages = [
            {
                "role": "user",
                "content": [
                    {"toolResult": {"content": [{"text": error_json}]}},
                    {"toolResult": {"content": [{"text": valid_json}]}}
                ]
            }
        ]
        result = extract_from_tool_results(messages)
        assert result is not None
        assert result.severity == "medium"
