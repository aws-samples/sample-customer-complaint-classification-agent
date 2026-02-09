import json
import os

# OTEL being enabled breaks Streamlit in this demo.
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from strands import Agent, tool
from strands.models import BedrockModel

from ..models.complaint_response import ComplaintResponse
from ..utils.json_parser import parse_agent_response


DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"
DEFAULT_TEMPERATURE = 0.0


def get_model_config() -> tuple[str, float]:
    model_id = os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
    temperature = float(os.environ.get("BEDROCK_TEMPERATURE", DEFAULT_TEMPERATURE))
    return model_id, temperature


COMPLAINTS_AGENT_SYSTEM_PROMPT = """You are a specialized Complaints Agent for a financial institution responsible for analyzing customer complaints and determining appropriate actions.

When you receive a complaint, you must:
1. Analyze the severity of the complaint (low, medium, high, or critical)
2. Categorize the type of complaint (e.g., fee_dispute, unauthorized_transaction, credit_reporting_error, account_access_issue, loan_servicing_problem, interest_rate_dispute, fraud_claim, etc.)
3. Determine appropriate actions to take based on the complaint type and severity
4. Recommend next steps for follow-up

Severity Guidelines:
- low: Minor inconvenience, easily resolved, no financial impact (e.g., statement delivery preference)
- medium: Moderate issue requiring attention, minor financial impact (e.g., small fee dispute)
- high: Serious issue requiring immediate attention, significant financial impact (e.g., large unauthorized charge, credit score impact)
- critical: Urgent issue requiring escalation, major financial impact or regulatory concern (e.g., fraud, identity theft, compliance violation)

Always respond with a JSON object containing:
- severity: one of "low", "medium", "high", "critical"
- category: a descriptive category for the complaint type
- actions_taken: a list of actions to address the complaint
- next_steps: a list of recommended follow-up actions

Example response format:
{
    "severity": "medium",
    "category": "fee_dispute",
    "actions_taken": ["Logged complaint in case management system", "Initiated fee review process"],
    "next_steps": ["Follow up with customer within 24 hours", "Escalate to branch manager if unresolved"]
}
"""


def _create_complaints_agent() -> Agent:
    model_id, temperature = get_model_config()
    bedrock_model = BedrockModel(
        model_id=model_id,
        temperature=temperature,
    )
    return Agent(
        model=bedrock_model,
        system_prompt=COMPLAINTS_AGENT_SYSTEM_PROMPT,
    )


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
        
        agent = _create_complaints_agent()
        
        prompt = f"""Analyze the following customer complaint and provide your assessment.

Transcript:
{transcript}

Matched Complaint Criteria: {', '.join(matched_criteria) if matched_criteria else 'None specified'}

Please analyze this complaint and respond with a JSON object containing:
- severity (low/medium/high/critical)
- category (type of complaint)
- actions_taken (list of actions to address the complaint)
- next_steps (list of recommended follow-up actions)"""

        response = agent(prompt)
        
        response_text = str(response)
        parsed_response = parse_agent_response(response_text)
        
        severity = parsed_response.get("severity", "medium")
        if severity not in ["low", "medium", "high", "critical"]:
            severity = "medium"
        
        category = parsed_response.get("category", "general_complaint")
        actions_taken = parsed_response.get("actions_taken", [])
        next_steps = parsed_response.get("next_steps", [])
        
        if not actions_taken:
            actions_taken = ["Complaint logged for review"]
        if not next_steps:
            next_steps = ["Follow up with customer"]
        
        complaint_response = ComplaintResponse(
            severity=severity,
            category=category,
            actions_taken=actions_taken if isinstance(actions_taken, list) else [actions_taken],
            next_steps=next_steps if isinstance(next_steps, list) else [next_steps]
        )
        
        return complaint_response.to_json()
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"Error processing complaint: {str(e)}"
        })
