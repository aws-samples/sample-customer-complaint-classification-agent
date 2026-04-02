"""Conversation panel rendering for the split UI.

This module provides the ConversationRenderer class that renders
customer transcripts in the conversation panel.
"""

from typing import List

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from .session import ChatMessage


TRANSCRIPT_CSS = """
<style>
.transcript-container {
    background-color: var(--secondary-background-color);
    border-left: 4px solid #1976d2;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 0 8px 8px 0;
}

.transcript-timestamp {
    font-size: 0.75rem;
    color: var(--text-color);
    opacity: 0.7;
    margin-bottom: 0.5rem;
}

.transcript-content {
    font-size: 1rem;
    line-height: 1.5;
    color: var(--text-color);
}

.conversation-turn {
    padding: 0.5rem 0;
}

.speaker-agent {
    color: #1976d2;
    font-weight: 600;
}

.speaker-customer {
    color: #28a745;
    font-weight: 600;
}

.turn-message {
    margin-left: 0.5rem;
    color: var(--text-color);
}
</style>
"""


class ConversationRenderer:
    """Renders conversation transcripts in the conversation panel."""
    
    def render_transcript(
        self,
        container: DeltaGenerator,
        message: ChatMessage
    ) -> None:
        """Render a single transcript in the conversation panel.
        
        Args:
            container: The Streamlit container to render into
            message: The ChatMessage containing the transcript
        """
        with container:
            timestamp_str = message.timestamp.strftime("%H:%M:%S")
            st.markdown(TRANSCRIPT_CSS, unsafe_allow_html=True)
            
            content_html = self._format_conversation_content(message.content)
            
            st.markdown(
                f'<div class="transcript-container">'
                f'<div class="transcript-timestamp">📝 {timestamp_str}</div>'
                f'<div class="transcript-content">{content_html}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
    
    def _format_conversation_content(self, content: str) -> str:
        """Format conversation content with speaker highlighting.
        
        Args:
            content: The raw transcript content
            
        Returns:
            HTML-formatted content with speaker styling
        """
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("Agent:"):
                speaker = "Agent"
                message = line[6:].strip()
                formatted_lines.append(
                    f'<div class="conversation-turn">'
                    f'<span class="speaker-agent">🎧 {speaker}:</span>'
                    f'<span class="turn-message">{message}</span>'
                    f'</div>'
                )
            elif line.startswith("Customer:"):
                speaker = "Customer"
                message = line[9:].strip()
                formatted_lines.append(
                    f'<div class="conversation-turn">'
                    f'<span class="speaker-customer">👤 {speaker}:</span>'
                    f'<span class="turn-message">{message}</span>'
                    f'</div>'
                )
            else:
                formatted_lines.append(f'<div class="conversation-turn">{line}</div>')
        
        return ''.join(formatted_lines)
    
    def render_history(
        self,
        container: DeltaGenerator,
        messages: List[ChatMessage]
    ) -> None:
        """Render all user transcripts from session history.
        
        Filters messages to show only user transcripts (role == "user")
        and displays them in chronological order with the most recent
        at the bottom.
        
        Args:
            container: The Streamlit container to render into
            messages: List of all ChatMessage objects from session
        """
        user_messages = [msg for msg in messages if msg.role == "user"]
        
        for message in user_messages:
            self.render_transcript(container, message)
