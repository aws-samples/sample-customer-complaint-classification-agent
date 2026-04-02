"""JSON extraction and parsing for agent responses.

Handles markdown code blocks, nested braces, and escaped characters.
"""

import json


def find_json_objects(text: str) -> list[dict]:
    """Extract all valid JSON objects from text with proper brace matching."""
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
