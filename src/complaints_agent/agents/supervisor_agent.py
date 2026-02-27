import json
import logging
import os
from datetime import datetime
from typing import Optional

# Breaks streamlit if not disabled
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

from ..models.agent_response import AgentResponse
from ..models.complaint import Complaint
from ..models.complaint_criteria import ComplaintCriteria
from ..models.complaint_response import ComplaintResponse
from ..utils.json_parser import (
    parse_classification_response,
    extract_complaint_response,
    extract_from_tool_results,
)
from .complaints_agent import complaints_agent, get_model_config

COMPLAINTS_AGENT_ENDPOINT_ENV = "COMPLAINTS_AGENT_ENDPOINT"

logger = logging.getLogger(__name__)


def _build_system_prompt(criteria: ComplaintCriteria) -> str:
    keywords_str = ", ".join(criteria.keywords) if criteria.keywords else "none specified"
    sentiment_str = ", ".join(criteria.sentiment_indicators) if criteria.sentiment_indicators else "none specified"
    
    return f"""You are a Supervisor Agent responsible for analyzing customer call transcripts and classifying the nature of the interaction.

A transcript may represent many things: a general inquiry, a service request, a compliment, feedback, or a complaint. Your job is to read the transcript objectively and determine what type of interaction it is.

If the interaction is a complaint, the following criteria can help confirm that classification:

COMPLAINT KEYWORDS: {keywords_str}
NEGATIVE SENTIMENT INDICATORS: {sentiment_str}

Classification Rules:
1. Read the full transcript and assess the customer's intent and tone
2. If the interaction is a complaint, classify as "complaint"
3. If the interaction is not a complaint, classify as "non_complaint"
4. The keywords and sentiment indicators above are supporting signals, not the sole basis for classification

When you classify an interaction as a complaint, you MUST use the complaints_agent tool to process it.

Always respond with a JSON object containing these three fields:
- classification: either "complaint" or "non_complaint"
- matched_criteria: list of keywords or sentiment indicators that matched (empty list if non_complaint)
- reasoning: REQUIRED. Two to three sentences. If classified as a complaint, you MUST describe what the customer is upset about, what specific language or tone led to that conclusion, and any matched criteria that supported it. If non_complaint, briefly explain why.

Example response format:
{{
    "classification": "complaint",
    "matched_criteria": ["frustrated", "overcharged"],
    "reasoning": "The customer is disputing unexpected charges on their account and expressing clear frustration with the billing process. Their tone is adversarial and they explicitly request a refund, which signals dissatisfaction. The words 'frustrated' and 'overcharged' further confirm this is a complaint."
}}

IMPORTANT:
- The "reasoning" field is mandatory and must never be empty or omitted.
- When classified as complaint, ALWAYS call the complaints_agent tool with the transcript.
- The complaints_agent tool expects a JSON string with transcript, classification_result, and matched_criteria.
- Do not add any text outside the JSON object.
- Do not use emojis in your response.
"""


class SupervisorAgent:
    """Primary agent for transcript classification and complaint routing."""
    
    def __init__(
        self,
        criteria_config: ComplaintCriteria,
        complaints_agent_endpoint: Optional[str] = None
    ):
        self.criteria = criteria_config
        self._complaints_agent_endpoint = (
            complaints_agent_endpoint or os.environ.get(COMPLAINTS_AGENT_ENDPOINT_ENV)
        )
        self._mcp_client: Optional[MCPClient] = None
        self._agent = self._create_agent()
    
    def _create_mcp_client(self) -> MCPClient:
        """Create an MCP client for the complaints agent endpoint."""
        from mcp.client.streamable_http import streamablehttp_client
        
        endpoint = self._complaints_agent_endpoint
        return MCPClient(lambda: streamablehttp_client(endpoint))
    
    def _build_mcp_request(self, transcript: str, matched_criteria: list[str]) -> dict:
        """Build an MCP request for the complaints agent.

        Constructs a properly formatted MCP tools/call request with the
        transcript and matched criteria for complaint processing.
        """
        return {
            "method": "tools/call",
            "params": {
                "name": "process_complaint",
                "arguments": {
                    "transcript": transcript,
                    "matched_criteria": matched_criteria
                }
            }
        }

    def _parse_mcp_response(self, response: dict) -> ComplaintResponse | None:
        """Parse a ComplaintResponse from an MCP response.

        Extracts the text content from the MCP response structure and
        parses it into a ComplaintResponse object.

        Args:
            response: The MCP response dictionary containing content array.

        Returns:
            ComplaintResponse if parsing succeeds, None otherwise.
        """
        try:
            content = response.get("content", [])
            if not content:
                return None

            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = item.get("text", "")
                    if text:
                        return ComplaintResponse.from_json(text)

            return None
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def _invoke_complaints_agent_mcp(
        self, transcript: str, matched_criteria: list[str]
    ) -> ComplaintResponse | None:
        """Invoke the complaints agent via MCP protocol.

        Calls the complaints agent MCP server to process a complaint,
        handling various error conditions gracefully.

        Args:
            transcript: The customer call transcript.
            matched_criteria: List of matched complaint criteria.

        Returns:
            ComplaintResponse if successful, None on any failure.
        """
        if not self._mcp_client:
            logger.error("MCP client not initialized")
            return None

        try:
            response = self._mcp_client.call_tool(
                "process_complaint",
                {"transcript": transcript, "matched_criteria": matched_criteria}
            )
            return ComplaintResponse.from_json(response.content[0].text)
        except ConnectionError as e:
            logger.error(f"MCP connection failed: {e}")
            return None
        except TimeoutError as e:
            logger.error(f"MCP call timed out: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid response from complaints agent: {e}")
            return None
        except (AttributeError, IndexError, TypeError) as e:
            logger.error(f"Malformed MCP response structure: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling complaints agent: {e}")
            return None

    def _create_agent(self) -> Agent:
        model_id, temperature = get_model_config()
        bedrock_model = BedrockModel(
            model_id=model_id,
            temperature=temperature,
        )
        system_prompt = _build_system_prompt(self.criteria)
        
        if self._complaints_agent_endpoint:
            self._mcp_client = self._create_mcp_client()
            return Agent(
                model=bedrock_model,
                system_prompt=system_prompt,
                tools=[self._mcp_client],
            )
        else:
            return Agent(
                model=bedrock_model,
                system_prompt=system_prompt,
                tools=[complaints_agent],
            )
    
    def _extract_full_response_text(self) -> str:
        text_parts = []
        if hasattr(self._agent, 'messages') and self._agent.messages:
            for message in self._agent.messages:
                if message.get('role') == 'assistant':
                    content = message.get('content', [])
                    for item in content:
                        if isinstance(item, dict) and 'text' in item:
                            text_parts.append(item['text'])
        return '\n'.join(text_parts)
    
    def process_transcript(self, transcript: str) -> AgentResponse:
        if not transcript or not transcript.strip():
            return AgentResponse(
                is_complaint=False,
                summary="Empty transcript provided - no classification performed",
                complaint=None,
                complaint_response=None
            )
        
        prompt = f"""Analyze the following customer call transcript and classify the nature of the interaction.

TRANSCRIPT:
{transcript}

Instructions:
1. Read the transcript and determine what type of interaction this is
2. Provide your classification as JSON
3. If this is a complaint, you MUST call the complaints_agent tool with the complaint data

Respond with a JSON object containing classification, matched_criteria, and reasoning."""

        response = self._agent(prompt)
        response_text = self._extract_full_response_text()
        classification_data = parse_classification_response(response_text)
        
        classification = classification_data.get("classification", "non_complaint")
        matched_criteria = classification_data.get("matched_criteria", [])
        reasoning = classification_data.get("reasoning", "")
        is_complaint = classification.lower() in ["complaint", "complaints"]
        
        if is_complaint:
            complaint = Complaint(
                transcript=transcript,
                classification_result="complaint",
                timestamp=datetime.now(),
                matched_criteria=matched_criteria
            )
            
            complaint_response = self._extract_complaint_response(response_text)
            
            if complaint_response is None:
                complaint_data = json.dumps({
                    "transcript": transcript,
                    "classification_result": "complaint",
                    "matched_criteria": matched_criteria
                })
                tool_result = complaints_agent(complaint_data)
                try:
                    result_data = json.loads(tool_result)
                    if "status" not in result_data or result_data.get("status") != "error":
                        complaint_response = ComplaintResponse.from_json(tool_result)
                except (json.JSONDecodeError, KeyError):
                    pass
            
            summary = f"Complaint identified: {reasoning}" if reasoning else "Complaint identified and processed"
            if complaint_response:
                summary += f" Severity: {complaint_response.severity}, Category: {complaint_response.category}"
            
            return AgentResponse(
                is_complaint=True,
                summary=summary,
                complaint=complaint,
                complaint_response=complaint_response
            )
        else:
            return AgentResponse(
                is_complaint=False,
                summary=f"Non-complaint: {reasoning}" if reasoning else "No complaint indicators found",
                complaint=None,
                complaint_response=None
            )
    
    def _extract_complaint_response(self, response_text: str) -> ComplaintResponse | None:
        messages = self._agent.messages if hasattr(self._agent, 'messages') else None
        if messages:
            complaint_response = extract_from_tool_results(messages)
            if complaint_response:
                return complaint_response
        return extract_complaint_response(response_text)
