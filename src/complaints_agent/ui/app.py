"""Streamlit web interface for the complaints agent system.

This module provides the main Streamlit application for interacting with
the complaints agent system through a chat-like interface.
"""

import os
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

from complaints_agent.config.loader import ConfigurationLoader, ConfigurationError
from complaints_agent.models import AgentResponse
from .models import ChatMessage
from .session import (
    initialize_session_state,
    get_messages,
    add_message,
    clear_chat_history,
)
from .streaming import StreamingSupervisorAgent
from .validation import is_valid_transcript


SEVERITY_COLORS = {
    "critical": "#dc3545",
    "high": "#fd7e14",
    "medium": "#ffc107",
    "low": "#28a745",
}

AGENT_LABELS = {
    "supervisor": "🔍 **Supervisor Agent**",
    "complaints": "📋 **Complaints Agent**",
}


def display_complaint_details(response: AgentResponse) -> None:
    """Display complaint details in an expandable section.
    
    Args:
        response: The AgentResponse containing complaint information
    """
    if not response.complaint_response:
        return
    
    cr = response.complaint_response
    
    with st.expander("📋 Complaint Details", expanded=True):
        severity_color = SEVERITY_COLORS.get(cr.severity.lower(), "#6c757d")
        st.markdown(
            f"**Severity:** <span style='color: {severity_color}; "
            f"font-weight: bold;'>{cr.severity.upper()}</span>",
            unsafe_allow_html=True
        )
        
        st.markdown(f"**Category:** {cr.category}")
        
        if cr.actions_taken:
            st.markdown("**Actions Taken:**")
            for action in cr.actions_taken:
                st.markdown(f"- {action}")
        
        if cr.next_steps:
            st.markdown("**Next Steps:**")
            for step in cr.next_steps:
                st.markdown(f"- {step}")


def display_agent_response(response: AgentResponse) -> None:
    """Display structured agent response with complaint details.
    
    Args:
        response: The AgentResponse from the supervisor agent
    """
    if response.is_complaint:
        st.markdown("🚨 **Classification: COMPLAINT**")
        
        if response.complaint and response.complaint.matched_criteria:
            st.markdown("**Matched Criteria:**")
            for criteria in response.complaint.matched_criteria:
                st.markdown(f"- {criteria}")
        
        display_complaint_details(response)
    else:
        st.markdown("✅ **Classification: NON-COMPLAINT**")
        st.markdown(f"**Summary:** {response.summary}")


def display_chat_history() -> None:
    """Render all messages from session state chat history."""
    messages = get_messages()
    
    for message in messages:
        with st.chat_message(message.role):
            st.markdown(message.content)
            
            if message.role == "assistant" and message.agent_response:
                display_agent_response(message.agent_response)


def handle_user_input(transcript: str) -> None:
    """Process user input and invoke the streaming agent.
    
    Args:
        transcript: The user's input transcript
    """
    add_message(role="user", content=transcript)
    
    with st.chat_message("user"):
        st.markdown(transcript)
    
    try:
        criteria = ConfigurationLoader.load_from_default()
        agent = StreamingSupervisorAgent(criteria)
        
        with st.chat_message("assistant"):
            agent_label_placeholder = st.empty()
            placeholder = st.empty()
            streamed_content = []
            current_agent_label = ["supervisor"]
            ctx = get_script_run_ctx()
            
            agent_label_placeholder.markdown(AGENT_LABELS["supervisor"])
            
            def on_token(token: str) -> None:
                add_script_run_ctx(ctx=ctx)
                streamed_content.append(token)
                placeholder.markdown("".join(streamed_content) + "▌")
            
            def on_agent_change(agent_name: str) -> None:
                add_script_run_ctx(ctx=ctx)
                if agent_name != current_agent_label[0]:
                    current_agent_label[0] = agent_name
                    if agent_name in AGENT_LABELS:
                        streamed_content.append(f"\n\n---\n\n{AGENT_LABELS[agent_name]}\n\n")
                        placeholder.markdown("".join(streamed_content))
            
            response = agent.process_transcript_streaming(transcript, on_token, on_agent_change)
            
            final_content = "".join(streamed_content) if streamed_content else response.summary
            placeholder.markdown(final_content)
            
            display_agent_response(response)
            
            add_message(
                role="assistant",
                content=final_content,
                agent_response=response
            )
    
    except ConfigurationError as e:
        st.error(f"Configuration error: {e}")
    except Exception as e:
        st.error(f"An error occurred while processing your request: {e}")


def main() -> None:
    """Main entry point for the Streamlit application."""
    st.set_page_config(
        page_title="Complaints Agent",
        page_icon="📞",
        layout="wide"
    )
    
    st.title("📞 Complaints Agent")
    st.markdown(
        "Submit customer call transcripts to analyze and classify them. "
        "The system will identify complaints and provide severity assessment, "
        "categorization, and recommended actions."
    )
    
    initialize_session_state()
    
    with st.sidebar:
        st.header("Options")
        if st.button("🗑️ Clear Chat History"):
            clear_chat_history()
            st.rerun()
        
        st.divider()
        st.header("Sample Transcripts")
        
        complaint_sample = """Customer: I've been trying to get a refund for three weeks now and nobody is helping me. This is absolutely ridiculous! I was charged twice for the same transaction and your customer service has been completely unhelpful. I want to speak to a manager immediately."""
        
        normal_sample = """Customer: Hi, I'd like to check my account balance and see if my recent deposit has cleared. Also, could you tell me what the current interest rate is on savings accounts?"""
        
        st.markdown("**Complaint Example:**")
        st.code(complaint_sample, language=None)
        
        st.markdown("**Normal Question:**")
        st.code(normal_sample, language=None)
    
    display_chat_history()
    
    transcript = st.chat_input("Enter a customer call transcript...")
    
    if transcript:
        if is_valid_transcript(transcript):
            handle_user_input(transcript)
        else:
            st.warning("Please enter a valid transcript (non-empty text).")


if __name__ == "__main__":
    main()
