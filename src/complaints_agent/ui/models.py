"""Data models for the Streamlit UI."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from complaints_agent.models import AgentResponse


@dataclass
class ChatMessage:
    """Represents a message in the chat history.
    
    Attributes:
        role: Either "user" or "assistant"
        content: The text content of the message
        timestamp: When the message was created
        agent_response: Optional structured response for assistant messages
    """
    role: str
    content: str
    timestamp: datetime
    agent_response: Optional[AgentResponse] = None
