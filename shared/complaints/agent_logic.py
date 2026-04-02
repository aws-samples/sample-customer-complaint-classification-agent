"""Core complaints agent logic for processing customer complaints.

This module is the single source of truth for the complaints agent behavior.
Both the local @tool wrapper and the remote MCP server delegate to this class.
"""

import os

from strands import Agent
from strands.models import BedrockModel

from shared.models.complaint_response import ComplaintResponse
from shared.parsing.json_parser import parse_agent_response


DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-6"
DEFAULT_TEMPERATURE = 0.0

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


def get_model_config() -> tuple[str, float]:
    """Get model configuration from environment variables."""
    model_id = os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
    temperature = float(os.environ.get("BEDROCK_TEMPERATURE", DEFAULT_TEMPERATURE))
    return model_id, temperature


class ComplaintsAgentLogic:
    """Core logic for processing customer complaints using a Strands agent.

    Used by both the local @tool wrapper (supervisor in-process) and
    the remote MCP server (standalone deployment).
    """

    def __init__(self, model_id: str | None = None, temperature: float | None = None):
        """Initialize the complaints agent with model configuration.

        Args:
            model_id: Bedrock model ID. Defaults to env var or DEFAULT_MODEL_ID.
            temperature: Model temperature. Defaults to env var or DEFAULT_TEMPERATURE.
        """
        if model_id is None or temperature is None:
            env_model_id, env_temperature = get_model_config()
            model_id = model_id or env_model_id
            temperature = temperature if temperature is not None else env_temperature

        self.model_id = model_id
        self.temperature = temperature
        self.model = BedrockModel(model_id=model_id, temperature=temperature)
        self.agent = Agent(
            model=self.model,
            system_prompt=COMPLAINTS_AGENT_SYSTEM_PROMPT,
        )

    def process(self, transcript: str, matched_criteria: list[str] | None = None) -> ComplaintResponse:
        """Process a complaint transcript and return a structured response.

        Args:
            transcript: The customer call transcript containing the complaint.
            matched_criteria: Optional list of complaint criteria keywords that matched.

        Returns:
            A ComplaintResponse with severity, category, actions_taken, and next_steps.
        """
        if matched_criteria is None:
            matched_criteria = []

        prompt = self._build_prompt(transcript, matched_criteria)
        response = self.agent(prompt)
        return self._parse_response(str(response))

    def _build_prompt(self, transcript: str, matched_criteria: list[str]) -> str:
        """Build the prompt for the agent from transcript and criteria."""
        criteria_str = ", ".join(matched_criteria) if matched_criteria else "None specified"
        return f"""Analyze the following customer complaint and provide your assessment.

Transcript:
{transcript}

Matched Complaint Criteria: {criteria_str}

Provide your assessment in readable markdown, then include the structured JSON code block at the end."""

    def _parse_response(self, response_text: str) -> ComplaintResponse:
        """Parse the agent response into a ComplaintResponse object."""
        parsed = parse_agent_response(response_text)

        severity = parsed.get("severity", "medium")
        if severity not in ["low", "medium", "high", "critical"]:
            severity = "medium"

        category = parsed.get("category", "general_complaint")
        routing_group = parsed.get("routing_group", "disputes")
        actions_taken = parsed.get("actions_taken", [])
        next_steps = parsed.get("next_steps", [])

        if not actions_taken:
            actions_taken = ["Complaint logged for review"]
        if not next_steps:
            next_steps = ["Follow up with customer"]

        if not isinstance(actions_taken, list):
            actions_taken = [actions_taken]
        if not isinstance(next_steps, list):
            next_steps = [next_steps]

        return ComplaintResponse(
            severity=severity,
            category=category,
            routing_group=routing_group,
            actions_taken=actions_taken,
            next_steps=next_steps,
        )
