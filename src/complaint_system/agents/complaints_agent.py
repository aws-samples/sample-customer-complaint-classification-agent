"""Strands @tool wrapper for the complaints agent.

This is a thin wrapper that delegates to the shared ComplaintsAgentLogic.
Used by the supervisor agent when running locally (no MCP endpoint configured).
"""

import json

from strands import tool

from shared.complaints.agent_logic import ComplaintsAgentLogic, get_model_config


@tool
def complaints_agent(complaint_data: str) -> str:
    """Process a classified complaint and determine appropriate actions."""
    try:
        try:
            data = json.loads(complaint_data)
        except json.JSONDecodeError as e:
            return json.dumps({
                "status": "error",
                "error": f"Invalid JSON input: {str(e)}"
            })

        if "transcript" not in data:
            return json.dumps({
                "status": "error",
                "error": "Missing required field: transcript"
            })

        transcript = data.get("transcript", "")
        if not transcript or not transcript.strip():
            return json.dumps({
                "status": "error",
                "error": "Transcript cannot be empty"
            })

        matched_criteria = data.get("matched_criteria", [])

        logic = ComplaintsAgentLogic()
        response = logic.process(transcript, matched_criteria)
        return response.to_json()

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"Error processing complaint: {str(e)}"
        })
