import json
import os
from datetime import datetime
from typing import Any, Callable, Optional

os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from strands import Agent
from strands.models import BedrockModel
from streamlit.delta_generator import DeltaGenerator
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

from ..agents.complaints_agent import complaints_agent, get_model_config
from ..agents.supervisor_agent import _build_system_prompt
from ..models.agent_response import AgentResponse
from ..models.complaint import Complaint
from ..models.complaint_criteria import ComplaintCriteria
from ..models.complaint_response import ComplaintResponse
from ..utils.json_parser import (
    parse_classification_response,
    extract_complaint_response,
    extract_from_tool_results,
)
from .layout import AGENT_LABELS
from .evaluation import format_streaming_content


class StreamingCallbackHandler:
    """Callback handler that captures streaming tokens for Streamlit display."""
    
    def __init__(
        self, 
        on_token: Callable[[str], None],
        on_agent_change: Callable[[str], None] | None = None
    ):
        self.on_token = on_token
        self.on_agent_change = on_agent_change
        self.tool_count = 0
        self.previous_tool_use = None
        self.current_agent = "supervisor"
        self._notified_supervisor = False
        self._notified_complaints = False
    
    def __call__(self, **kwargs: Any) -> None:
        data = kwargs.get("data")
        complete = kwargs.get("complete", False)
        current_tool_use = kwargs.get("current_tool_use")
        
        if current_tool_use is not None:
            if current_tool_use != self.previous_tool_use:
                self.tool_count += 1
                self.previous_tool_use = current_tool_use
                
                tool_name = None
                if isinstance(current_tool_use, dict):
                    tool_name = current_tool_use.get("name")
                
                if tool_name == "complaints_agent":
                    if self.current_agent != "complaints":
                        self.current_agent = "complaints"
                        if self.on_agent_change and not self._notified_complaints:
                            self.on_agent_change("complaints")
                            self._notified_complaints = True
        
        if data and isinstance(data, str):
            if not self._notified_supervisor and self.current_agent == "supervisor":
                if self.on_agent_change:
                    self.on_agent_change("supervisor")
                self._notified_supervisor = True
            self.on_token(data)
        
        if complete:
            pass


class SplitPanelStreamingHandler:
    """Callback handler for streaming to the evaluation panel.
    
    This handler extends the streaming functionality to work with the split
    panel layout, rendering tokens and agent changes directly to the
    evaluation panel container with side-by-side agent columns.
    """
    
    def __init__(
        self,
        evaluation_container: DeltaGenerator,
        on_token: Optional[Callable[[str], None]] = None,
        on_agent_change: Optional[Callable[[str], None]] = None
    ):
        """Initialize the split panel streaming handler.
        
        Args:
            evaluation_container: The Streamlit container for the evaluation panel
            on_token: Optional callback invoked when a token is received
            on_agent_change: Optional callback invoked when the active agent changes
        """
        self.evaluation_container = evaluation_container
        self.on_token = on_token
        self.on_agent_change = on_agent_change
        self.supervisor_content = ""
        self.complaints_content = ""
        self.current_agent = "supervisor"
        self._is_streaming = True
        self._supervisor_placeholder = None
        self._complaints_placeholder = None
        self._notified_supervisor = False
        self._notified_complaints = False
        self.tool_count = 0
        self.previous_tool_use = None
        self._script_run_ctx = None
        self._complaints_column = None
    
    def get_complaints_column(self) -> Optional[DeltaGenerator]:
        """Get the complaints column container for rendering classification results."""
        return self._complaints_column
    
    def initialize_placeholders(self) -> None:
        """Initialize Streamlit placeholders for dynamic content updates."""
        import streamlit as st
        self._script_run_ctx = get_script_run_ctx()
        with self.evaluation_container:
            st.markdown(AGENT_LABELS["supervisor"])
            self._supervisor_placeholder = st.empty()
            st.markdown("---")
            st.markdown(AGENT_LABELS["complaints"])
            self._complaints_placeholder = st.empty()
            self._complaints_placeholder.markdown("*Waiting for classification...*")
            self._complaints_column = self.evaluation_container
    
    def _ensure_context(self) -> None:
        """Ensure the Streamlit script run context is set for the current thread."""
        if self._script_run_ctx is not None:
            add_script_run_ctx(ctx=self._script_run_ctx)
    
    def _update_content_display(self) -> None:
        """Update the appropriate placeholder with current streaming content."""
        self._ensure_context()
        if self.current_agent == "supervisor" and self._supervisor_placeholder is not None:
            formatted = format_streaming_content(self.supervisor_content, self._is_streaming)
            self._supervisor_placeholder.markdown(formatted)
        elif self.current_agent == "complaints" and self._complaints_placeholder is not None:
            formatted = format_streaming_content(self.complaints_content, self._is_streaming)
            self._complaints_placeholder.markdown(formatted)
    
    def handle_token(self, token: str) -> None:
        """Handle a streaming token.
        
        Args:
            token: The token string received from the agent
        """
        if self.current_agent == "supervisor":
            self.supervisor_content += token
        else:
            self.complaints_content += token
        self._update_content_display()
        if self.on_token:
            self.on_token(token)
    
    def handle_agent_change(self, agent_name: str) -> None:
        """Handle an agent change event.
        
        Args:
            agent_name: The new agent identifier
        """
        if agent_name != self.current_agent:
            self.current_agent = agent_name
            if agent_name == "complaints" and self._complaints_placeholder is not None:
                self._ensure_context()
                self._complaints_placeholder.markdown("")
            if self.on_agent_change:
                self.on_agent_change(agent_name)
    
    def finalize(self) -> str:
        """Finalize streaming and return the accumulated supervisor content."""
        self._is_streaming = False
        self._ensure_context()
        if self._supervisor_placeholder is not None:
            self._supervisor_placeholder.markdown(self.supervisor_content)
        if self._complaints_placeholder is not None:
            if self.complaints_content:
                self._complaints_placeholder.markdown(self.complaints_content)
            else:
                self._complaints_placeholder.markdown("*No complaint processing needed*")
        return self.supervisor_content
    
    def get_streaming_content(self) -> str:
        """Get the current accumulated streaming content."""
        return self.supervisor_content
    
    def is_streaming(self) -> bool:
        """Check if streaming is currently active.
        
        Returns:
            True if streaming is in progress, False otherwise
        """
        return self._is_streaming
    
    def __call__(self, **kwargs: Any) -> None:
        """Handle streaming callbacks from the agent.
        
        This method is called by the Strands agent during streaming.
        It processes tokens and agent change events.
        """
        data = kwargs.get("data")
        complete = kwargs.get("complete", False)
        current_tool_use = kwargs.get("current_tool_use")
        
        if current_tool_use is not None:
            if current_tool_use != self.previous_tool_use:
                self.tool_count += 1
                self.previous_tool_use = current_tool_use
                
                tool_name = None
                if isinstance(current_tool_use, dict):
                    tool_name = current_tool_use.get("name")
                
                if tool_name == "complaints_agent":
                    if self.current_agent != "complaints":
                        if not self._notified_complaints:
                            self.handle_agent_change("complaints")
                            self._notified_complaints = True
        
        if data and isinstance(data, str):
            if not self._notified_supervisor and self.current_agent == "supervisor":
                self._notified_supervisor = True
            self.handle_token(data)
        
        if complete:
            self.finalize()


class StreamingSupervisorAgent:
    """Wrapper for SupervisorAgent that provides streaming capabilities."""
    
    def __init__(self, criteria_config: ComplaintCriteria):
        self.criteria = criteria_config
    
    def _create_agent_with_streaming(
        self, 
        callback_handler: StreamingCallbackHandler
    ) -> Agent:
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
            callback_handler=callback_handler,
        )
    
    def process_transcript_streaming(
        self, 
        transcript: str,
        on_token: Callable[[str], None],
        on_agent_change: Callable[[str], None] | None = None
    ) -> AgentResponse:
        if not transcript or not transcript.strip():
            return AgentResponse(
                is_complaint=False,
                summary="Empty transcript provided - no classification performed",
                complaint=None,
                complaint_response=None
            )
        
        callback_handler = StreamingCallbackHandler(
            on_token=on_token,
            on_agent_change=on_agent_change
        )
        agent = self._create_agent_with_streaming(callback_handler)
        
        prompt = f"""Analyze the following customer call transcript and classify the nature of the interaction.

TRANSCRIPT:
{transcript}

Instructions:
1. Read the transcript and determine what type of interaction this is
2. Provide your classification as JSON
3. If this is a complaint, you MUST call the complaints_agent tool with the complaint data

Respond with a JSON object containing classification, matched_criteria, and reasoning."""

        agent(prompt)
        
        response_text = self._extract_full_response_text(agent)
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
            
            complaint_response = self._extract_complaint_response(agent, response_text)
            
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
    
    def _extract_full_response_text(self, agent: Agent) -> str:
        text_parts = []
        if hasattr(agent, 'messages') and agent.messages:
            for message in agent.messages:
                if message.get('role') == 'assistant':
                    content = message.get('content', [])
                    for item in content:
                        if isinstance(item, dict) and 'text' in item:
                            text_parts.append(item['text'])
        return '\n'.join(text_parts)
    
    def _extract_complaint_response(
        self, 
        agent: Agent, 
        response_text: str
    ) -> ComplaintResponse | None:
        messages = agent.messages if hasattr(agent, 'messages') else None
        if messages:
            complaint_response = extract_from_tool_results(messages)
            if complaint_response:
                return complaint_response
        return extract_complaint_response(response_text)
