"""Session state management and data models for the Streamlit UI."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import streamlit as st

from complaint_system.models import AgentResponse


@dataclass
class ChatMessage:
    """Represents a message in the chat history.

    Attributes:
        role: Either "user" or "assistant"
        content: The text content of the message (supervisor output for assistant messages)
        timestamp: When the message was created
        agent_response: Optional structured response for assistant messages
        actions_approved: Whether agent actions have been approved for this message
        complaints_content: Raw complaints agent output for two-column replay
    """

    role: str
    content: str
    timestamp: datetime
    agent_response: Optional[AgentResponse] = None
    actions_approved: bool = True
    complaints_content: str = ""


@dataclass
class PanelState:
    """Tracks the state of UI panels.

    Attributes:
        is_streaming: Whether content is currently being streamed
        current_agent: The currently active agent ("supervisor" or "complaints")
        streaming_content: Accumulated content during streaming
    """

    is_streaming: bool = False
    current_agent: str = "supervisor"
    streaming_content: str = ""


def is_valid_transcript(transcript: str) -> bool:
    """Validate that a transcript is non-empty and contains non-whitespace content."""
    if not isinstance(transcript, str):
        return False
    return bool(transcript.strip())


def initialize_session_state() -> None:
    """Initialize Streamlit session state with default values."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "panel_state" not in st.session_state:
        st.session_state.panel_state = PanelState()


def get_messages() -> List[ChatMessage]:
    """Retrieve all messages from session state."""
    initialize_session_state()
    return st.session_state.messages


def get_conversation_messages() -> List[ChatMessage]:
    """Get only user transcript messages for conversation panel."""
    initialize_session_state()
    return [msg for msg in st.session_state.messages if msg.role == "user"]


def get_evaluation_messages() -> List[ChatMessage]:
    """Get only assistant evaluation messages for evaluation panel."""
    initialize_session_state()
    return [msg for msg in st.session_state.messages if msg.role == "assistant"]


def add_message(
    role: str,
    content: str,
    agent_response: Optional[AgentResponse] = None,
    actions_approved: bool = True,
    complaints_content: str = "",
) -> ChatMessage:
    """Add a new message to the chat history."""
    initialize_session_state()
    message = ChatMessage(
        role=role,
        content=content,
        timestamp=datetime.now(),
        agent_response=agent_response,
        actions_approved=actions_approved,
        complaints_content=complaints_content,
    )
    st.session_state.messages.append(message)
    return message


def clear_chat_history() -> None:
    """Clear all messages from session state and reset panel state."""
    st.session_state.messages = []
    st.session_state.panel_state = PanelState()
    st.session_state.pop("pending_approval", None)
    st.session_state.pop("pending_approval_response", None)
