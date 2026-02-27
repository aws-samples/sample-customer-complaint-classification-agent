import json
import os

# Breaks streamlit if not disabled
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from strands import Agent, tool
from strands.models import BedrockModel

from ..models.complaint_response import ComplaintResponse
from ..utils.json_parser import parse_agent_response


DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-6"
DEFAULT_TEMPERATURE = 0.0


def get_model_config() -> tuple[str, float]:
    model_id = os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
    temperature = float(os.environ.get("BEDROCK_TEMPERATURE", DEFAULT_TEMPERATURE))
    return model_id, temperature


COMPLAINTS_AGENT_SYSTEM_PROMPT = """You are a specialized Complaints Agent for a financial institution responsible for analyzing customer complaints, determining appropriate actions, and routing to the correct team.

When you receive a complaint, you must:
1. Analyze the severity (low, medium, high, or critical)
2. Categorize the complaint type
3. Determine the correct routing group
4. List actions to take
5. List next steps for follow-up

Severity Guidelines:
- low: Minor inconvenience, easily resolved, no financial impact
- medium: Moderate issue requiring attention, minor financial impact
- high: Serious issue requiring immediate attention, significant financial impact
- critical: Urgent issue requiring escalation, major financial impact or regulatory concern

Routing Groups:
- fraud_and_security: fraud_claim, unauthorized_transaction, identity_theft, account_takeover
- credit_services: credit_reporting_error, credit_limit_dispute, loan_servicing_problem, interest_rate_dispute
- account_services: account_access_issue, account_closure, statement_error, wrong_balance
- billing_and_fees: fee_dispute, overcharge, late_fee, hidden_fee, incorrect_charge
- escalations: any complaint with severity "critical" or "high" involving regulatory concerns
- disputes: all other complaint types

Respond in clean, readable markdown. Use this exact format:

**Severity:** Medium
**Category:** Fee Dispute
**Routing:** Billing & Fees

**Actions Taken:**
- Logged complaint
- Initiated fee review

**Next Steps:**
- Follow up within 24 hours
- Escalate if unresolved

Then include the structured data as a JSON code block at the end:

```json
{"severity": "medium", "category": "fee_dispute", "routing_group": "billing_and_fees", "actions_taken": ["Logged complaint", "Initiated fee review"], "next_steps": ["Follow up within 24 hours", "Escalate if unresolved"]}
```

Keep descriptions short. Do not use emojis.
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

Provide your assessment in readable markdown, then include the structured JSON code block at the end."""

        response = agent(prompt)
        
        response_text = str(response)
        parsed_response = parse_agent_response(response_text)
        
        severity = parsed_response.get("severity", "medium")
        if severity not in ["low", "medium", "high", "critical"]:
            severity = "medium"
        
        category = parsed_response.get("category", "general_complaint")
        routing_group = parsed_response.get("routing_group", "disputes")
        actions_taken = parsed_response.get("actions_taken", [])
        next_steps = parsed_response.get("next_steps", [])
        
        if not actions_taken:
            actions_taken = ["Complaint logged for review"]
        if not next_steps:
            next_steps = ["Follow up with customer"]
        
        complaint_response = ComplaintResponse(
            severity=severity,
            category=category,
            routing_group=routing_group,
            actions_taken=actions_taken if isinstance(actions_taken, list) else [actions_taken],
            next_steps=next_steps if isinstance(next_steps, list) else [next_steps]
        )
        
        return complaint_response.to_json()
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"Error processing complaint: {str(e)}"
        })
