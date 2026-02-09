"""Session state management for the Streamlit UI."""

from datetime import datetime
from typing import List, Optional

import streamlit as st

from complaints_agent.models import AgentResponse
from .models import ChatMessage


def initialize_session_state() -> None:
    """Initialize Streamlit session state with default values."""
    if "messages" not in st.session_state:
        st.session_state.messages = []


def get_messages() -> List[ChatMessage]:
    """Retrieve all messages from session state.
    
    Returns:
        List of ChatMessage objects in chronological order
    """
    initialize_session_state()
    return st.session_state.messages


def add_message(
    role: str,
    content: str,
    agent_response: Optional[AgentResponse] = None
) -> ChatMessage:
    """Add a new message to the chat history.
    
    Args:
        role: Either "user" or "assistant"
        content: The text content of the message
        agent_response: Optional structured response for assistant messages
        
    Returns:
        The created ChatMessage
    """
    initialize_session_state()
    message = ChatMessage(
        role=role,
        content=content,
        timestamp=datetime.now(),
        agent_response=agent_response
    )
    st.session_state.messages.append(message)
    return message


def clear_chat_history() -> None:
    """Clear all messages from session state."""
    st.session_state.messages = []
