"""Panel layout infrastructure for the split UI.

This module provides the PanelLayout class that creates and manages
the split-panel UI structure with conversation and evaluation sections.
"""

import streamlit as st
from streamlit.delta_generator import DeltaGenerator


AGENT_LABELS = {
    "supervisor": "🔍 **Supervisor Agent**",
    "complaints": "📋 **Complaints Agent**",
}


def format_agent_label(agent_name: str) -> str:
    """Format an agent name into its display label.
    
    Args:
        agent_name: The agent identifier ("supervisor" or "complaints")
        
    Returns:
        The formatted label string with emoji and markdown bold formatting
        
    Raises:
        ValueError: If agent_name is not a valid agent identifier
    """
    if agent_name not in AGENT_LABELS:
        raise ValueError(f"Unknown agent name: {agent_name}")
    return AGENT_LABELS[agent_name]


PANEL_CSS = """
<style>
.conversation-panel {
    border-bottom: 2px solid var(--secondary-background-color);
    padding-bottom: 0.5rem;
    margin-bottom: 0.5rem;
    max-height: 25vh;
    overflow-y: auto;
}

.panel-header {
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    margin-bottom: 0.75rem;
    padding: 0.6rem 0.85rem;
    background-color: var(--secondary-background-color);
    color: var(--text-color);
    border-radius: 6px;
    border-left: 4px solid;
}

.panel-header-conversation { border-left-color: #1976d2; }
.panel-header-evaluation   { border-left-color: #28a745; }
.panel-header-actions      { border-left-color: #6f42c1; }
</style>
"""


class PanelLayout:
    """Manages the three-panel UI layout."""
    
    def __init__(self):
        self.conversation_container: DeltaGenerator = None
        self.evaluation_container: DeltaGenerator = None
        self.actions_container: DeltaGenerator = None
    
    def create_layout(self) -> tuple[DeltaGenerator, DeltaGenerator, DeltaGenerator]:
        """Create the three-panel layout with conversation, evaluation, and actions sections.
        
        Returns:
            A tuple of (conversation_container, evaluation_container, actions_container)
        """
        st.markdown(PANEL_CSS, unsafe_allow_html=True)

        st.markdown(
            '<div class="panel-header panel-header-conversation">💬 Customer Conversation</div>',
            unsafe_allow_html=True,
        )
        self.conversation_container = st.container()

        st.markdown(
            '<div class="conversation-panel"></div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")

        st.markdown(
            '<div class="panel-header panel-header-evaluation">🤖 Agent Evaluation</div>',
            unsafe_allow_html=True,
        )
        self.evaluation_container = st.container()

        st.markdown("---")

        st.markdown(
            '<div class="panel-header panel-header-actions">⚡ Agent Actions</div>',
            unsafe_allow_html=True,
        )
        self.actions_container = st.container()

        return self.conversation_container, self.evaluation_container, self.actions_container
    
    def get_conversation_panel(self) -> DeltaGenerator:
        """Return the conversation panel container."""
        return self.conversation_container
    
    def get_evaluation_panel(self) -> DeltaGenerator:
        """Return the evaluation panel container."""
        return self.evaluation_container
    
    def get_actions_panel(self) -> DeltaGenerator:
        """Return the actions panel container."""
        return self.actions_container
