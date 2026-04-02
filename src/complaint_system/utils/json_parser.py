"""Supervisor-specific JSON parsing utilities.

Builds on the shared parsing module with additional functions for
classification response parsing and tool result extraction.
"""

import json
from typing import Any

from shared.parsing.json_parser import find_json_objects, parse_agent_response
from ..models.complaint_response import ComplaintResponse


def _is_tool_call_input(data: dict) -> bool:
    """Check if this JSON looks like tool call input (not classification output)."""
    has_transcript = "transcript" in data
    has_classification_result = "classification_result" in data
    has_classification = "classification" in data
    has_reasoning = "reasoning" in data

    if has_transcript and has_classification_result and not has_reasoning:
        return True

    if has_classification and has_reasoning:
        return False

    return False


def _is_complaint_response(data: dict) -> bool:
    """Check if this JSON is a ComplaintResponse (tool output)."""
    complaint_response_fields = ["severity", "category", "actions_taken", "next_steps"]
    return all(field in data for field in complaint_response_fields)


def _is_classification_json(data: dict) -> bool:
    """Check if the parsed JSON is a classification response."""
    if not isinstance(data, dict):
        return False
    return "classification" in data


def _score_classification_json(data: dict) -> int:
    """Score how likely this JSON is the classification response (higher = better)."""
    score = 0
    if "classification" in data:
        score += 10
    if "matched_criteria" in data:
        score += 5
    if "reasoning" in data:
        score += 5
    if _is_tool_call_input(data):
        score -= 20
    if _is_complaint_response(data):
        score -= 15
    return score


def parse_classification_response(text: str) -> dict[str, Any]:
    """Parse classification JSON from agent response, filtering out tool inputs.

    Prioritizes JSON blocks with "classification" and "reasoning" fields,
    excluding tool inputs and complaint responses.

    Returns a default non_complaint classification if parsing fails.
    """
    if not text:
        return {
            "classification": "non_complaint",
            "matched_criteria": [],
            "reasoning": "Empty response text"
        }

    text = text.strip()

    try:
        data = json.loads(text)
        if (_is_classification_json(data) and
            not _is_tool_call_input(data) and
            not _is_complaint_response(data)):
            return data
    except json.JSONDecodeError:
        pass

    json_blocks = find_json_objects(text)

    classification_candidates = []
    for block in json_blocks:
        if _is_classification_json(block):
            score = _score_classification_json(block)
            classification_candidates.append((score, block))

    if classification_candidates:
        classification_candidates.sort(key=lambda x: x[0], reverse=True)
        best_candidate = classification_candidates[0][1]

        if not _is_tool_call_input(best_candidate) and not _is_complaint_response(best_candidate):
            return best_candidate

        for score, block in classification_candidates:
            if not _is_tool_call_input(block) and not _is_complaint_response(block):
                return block

    for block in json_blocks:
        if "classification" in block and not _is_tool_call_input(block) and not _is_complaint_response(block):
            return block

    text_lower = text.lower()
    if '"classification": "complaint"' in text_lower or '"classification":"complaint"' in text_lower:
        for block in json_blocks:
            if "classification" in block:
                classification_val = block.get("classification", "")
                if isinstance(classification_val, str) and "complaint" in classification_val.lower():
                    return block

    return {
        "classification": "non_complaint",
        "matched_criteria": [],
        "reasoning": "Could not parse classification response"
    }


def extract_complaint_response(text: str) -> ComplaintResponse | None:
    """Extract ComplaintResponse from text if present."""
    if not text:
        return None

    required_fields = ["severity", "category", "actions_taken", "next_steps"]
    if not all(field in text for field in required_fields):
        return None

    json_objects = find_json_objects(text)

    for data in json_objects:
        if all(field in data for field in required_fields):
            if 'status' in data and data.get('status') == 'error':
                continue
            try:
                return ComplaintResponse(
                    severity=data['severity'],
                    category=data['category'],
                    actions_taken=data.get('actions_taken', []),
                    next_steps=data.get('next_steps', [])
                )
            except (KeyError, TypeError):
                continue

    return None


def extract_from_tool_results(messages: list) -> ComplaintResponse | None:
    """Extract ComplaintResponse from agent message history."""
    if not messages:
        return None

    required_fields = ["severity", "category", "actions_taken", "next_steps"]

    for message in messages:
        if message.get('role') == 'user':
            content = message.get('content', [])
            for item in content:
                if isinstance(item, dict) and 'toolResult' in item:
                    tool_result = item['toolResult']
                    result_content = tool_result.get('content', [])
                    for result_item in result_content:
                        if isinstance(result_item, dict) and 'text' in result_item:
                            try:
                                data = json.loads(result_item['text'])
                                if (isinstance(data, dict) and
                                    'status' not in data and
                                    all(field in data for field in required_fields)):
                                    return ComplaintResponse(
                                        severity=data['severity'],
                                        category=data['category'],
                                        actions_taken=data.get('actions_taken', []),
                                        next_steps=data.get('next_steps', [])
                                    )
                            except (json.JSONDecodeError, KeyError):
                                pass
    return None
