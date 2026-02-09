import json
import os
from datetime import datetime

os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from strands import Agent
from strands.models import BedrockModel

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


def _build_system_prompt(criteria: ComplaintCriteria) -> str:
    keywords_str = ", ".join(criteria.keywords) if criteria.keywords else "none specified"
    sentiment_str = ", ".join(criteria.sentiment_indicators) if criteria.sentiment_indicators else "none specified"
    
    return f"""You are a Supervisor Agent responsible for analyzing customer call transcripts to identify complaints.

Your task is to classify each transcript as either a "complaint" or "non_complaint" based on the following business criteria:

COMPLAINT KEYWORDS: {keywords_str}
NEGATIVE SENTIMENT INDICATORS: {sentiment_str}

Classification Rules:
1. If the transcript contains ANY of the complaint keywords, classify as "complaint"
2. If the transcript contains ANY of the negative sentiment indicators, classify as "complaint"
3. If the transcript does NOT contain any complaint keywords or negative sentiment indicators, classify as "non_complaint"

When you identify a complaint, you MUST use the complaints_agent tool to process it.

Always respond with a JSON object containing:
- classification: either "complaint" or "non_complaint"
- matched_criteria: list of keywords or sentiment indicators that matched (empty list if non_complaint)
- reasoning: brief explanation of your classification decision

Example response format:
{{
    "classification": "complaint",
    "matched_criteria": ["frustrated", "broken"],
    "reasoning": "The customer expressed frustration about a broken product."
}}

IMPORTANT: 
- Be thorough in checking for complaint indicators
- When classified as complaint, ALWAYS call the complaints_agent tool with the transcript
- The complaints_agent tool expects a JSON string with transcript, classification_result, and matched_criteria
"""


class SupervisorAgent:
    """Primary agent for transcript classification and complaint routing."""
    
    def __init__(self, criteria_config: ComplaintCriteria):
        self.criteria = criteria_config
        self._agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        model_id, temperature = get_model_config()
        bedrock_model = BedrockModel(
            model_id=model_id,
            temperature=temperature,
        )
        system_prompt = _build_system_prompt(self.criteria)
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
        
        prompt = f"""Analyze the following customer call transcript and classify it as either a complaint or non-complaint.

TRANSCRIPT:
{transcript}

Instructions:
1. Check if the transcript contains any complaint keywords or negative sentiment indicators
2. Provide your classification as JSON
3. If this is a complaint, you MUST call the complaints_agent tool with the complaint data

Remember to respond with a JSON object containing classification, matched_criteria, and reasoning."""

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
