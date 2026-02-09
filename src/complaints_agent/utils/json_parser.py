"""Consolidated JSON extraction and parsing utilities.

This module provides functions for extracting and parsing JSON from agent
responses, handling markdown code blocks, nested braces, and escaped characters.
"""

import json
from typing import Any

from ..models.complaint_response import ComplaintResponse


def find_json_objects(text: str) -> list[dict]:
    """Extract all valid JSON objects from text with proper brace matching.
    
    Handles plain JSON, markdown code blocks, and embedded JSON in prose.
    Correctly handles nested braces and escaped characters within strings.
    """
    if not text:
        return []
    
    results = []
    seen = set()
    
    search_text = text
    while "```json" in search_text:
        start = search_text.find("```json") + 7
        end = search_text.find("```", start)
        if end > start:
            json_str = search_text[start:end].strip()
            try:
                data = json.loads(json_str)
                if isinstance(data, dict):
                    json_key = json.dumps(data, sort_keys=True)
                    if json_key not in seen:
                        seen.add(json_key)
                        results.append(data)
            except json.JSONDecodeError:
                pass
        search_text = search_text[end + 3:] if end > 0 else ""
    
    i = 0
    while i < len(text):
        if text[i] == '{':
            depth = 0
            j = i
            in_string = False
            escape_next = False
            
            while j < len(text):
                char = text[j]
                if escape_next:
                    escape_next = False
                elif char == '\\' and in_string:
                    escape_next = True
                elif char == '"' and not escape_next:
                    in_string = not in_string
                elif not in_string:
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            json_str = text[i:j+1]
                            try:
                                data = json.loads(json_str)
                                if isinstance(data, dict):
                                    json_key = json.dumps(data, sort_keys=True)
                                    if json_key not in seen:
                                        seen.add(json_key)
                                        results.append(data)
                            except json.JSONDecodeError:
                                pass
                            break
                j += 1
            i = j + 1
        else:
            i += 1
    
    return results


def parse_agent_response(text: str) -> dict:
    """Parse JSON from agent response, handling markdown blocks.
    
    Returns the first valid JSON object found, or an empty dict if none found.
    """
    if not text:
        return {}
    
    text = text.strip()
    
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    
    json_objects = find_json_objects(text)
    return json_objects[0] if json_objects else {}


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
    """Extract ComplaintResponse from text if present.
    
    Searches for valid JSON objects containing all required ComplaintResponse
    fields (severity, category, actions_taken, next_steps). Skips error responses.
    """
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
    """Extract ComplaintResponse from agent message history.
    
    Searches through tool results in the conversation history for valid
    ComplaintResponse JSON objects. Skips error responses.
    """
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
