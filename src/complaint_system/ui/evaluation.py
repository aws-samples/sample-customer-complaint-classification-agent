"""Evaluation panel rendering for the split UI.

This module provides the EvaluationRenderer class that renders
agent evaluation content including streaming, agent labels,
classification results, and complaint details.
"""

from typing import List

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from complaint_system.models import AgentResponse
from .session import ChatMessage
from .layout import AGENT_LABELS


SEVERITY_COLORS = {
    "critical": "#dc3545",
    "high": "#fd7e14",
    "medium": "#ffc107",
    "low": "#28a745",
}

ROUTING_GROUP_CONFIG = {
    "fraud_and_security": {"label": "Fraud & Security", "color": "#dc3545", "icon": "🔒"},
    "credit_services":    {"label": "Credit Services",  "color": "#6f42c1", "icon": "💳"},
    "account_services":   {"label": "Account Services", "color": "#1976d2", "icon": "🏦"},
    "billing_and_fees":   {"label": "Billing & Fees",   "color": "#fd7e14", "icon": "🧾"},
    "escalations":        {"label": "Escalations",      "color": "#dc3545", "icon": "🚨"},
    "disputes":           {"label": "Disputes",         "color": "#6c757d", "icon": "⚖️"},
}

TYPING_INDICATOR = "▌"


def format_streaming_content(content: str, is_streaming: bool) -> str:
    """Format streaming content with optional typing indicator."""
    if is_streaming:
        return content + TYPING_INDICATOR
    return content


EVALUATION_CSS = """
<style>
.evaluation-container {
    background-color: var(--secondary-background-color);
    border-left: 4px solid #28a745;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 0 8px 8px 0;
}

.evaluation-timestamp {
    font-size: 0.75rem;
    color: var(--text-color);
    opacity: 0.7;
    margin-bottom: 0.5rem;
}

.agent-separator {
    border-top: 1px dashed var(--secondary-background-color);
    margin: 1rem 0;
    padding-top: 0.5rem;
}
</style>
"""


class EvaluationRenderer:
    """Renders agent evaluation content in the evaluation panel."""

    def render_streaming_content(
        self,
        container: DeltaGenerator,
        content: str,
        is_streaming: bool,
    ) -> None:
        """Render streaming content with optional typing indicator."""
        with container:
            st.markdown(format_streaming_content(content, is_streaming))

    def render_agent_label(self, container: DeltaGenerator, agent_name: str) -> None:
        """Render the current agent label."""
        with container:
            if agent_name in AGENT_LABELS:
                st.markdown(AGENT_LABELS[agent_name])

    def render_classification_result(
        self,
        container: DeltaGenerator,
        response: AgentResponse,
    ) -> None:
        """Render a focused assessment summary for the complaints agent column."""
        with container:
            if not response.is_complaint:
                st.markdown("✅ **No complaint detected.**")
                st.caption(response.summary)
                return

            cr = response.complaint_response
            if not cr:
                st.markdown("🚨 **Complaint detected** — no details available.")
                return

            routing = ROUTING_GROUP_CONFIG.get(cr.routing_group, ROUTING_GROUP_CONFIG["disputes"])
            severity_color = SEVERITY_COLORS.get(cr.severity.lower(), "#6c757d")

            st.markdown(
                f"<div style='border-left: 4px solid {routing['color']}; "
                f"background: rgba(0,0,0,0.08); padding: 0.6rem 1rem; "
                f"margin: 0.4rem 0; border-radius: 0 6px 6px 0;'>"
                f"<span style='font-size:0.7rem; opacity:0.6; display:block; margin-bottom:0.25rem; text-transform:uppercase; letter-spacing:0.05em;'>Routed to</span>"
                f"<span style='font-size:1rem; font-weight:700; color:{routing['color']};'>{routing['icon']} {routing['label']}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            st.markdown(
                f"<div style='display:flex; gap:0.75rem; margin: 0.4rem 0; align-items:center;'>"
                f"<span style='font-size:0.8rem; font-weight:700; color:{severity_color}; "
                f"background:rgba(0,0,0,0.1); padding:0.15rem 0.5rem; border-radius:4px;'>"
                f"{cr.severity.upper()}</span>"
                f"<span style='font-size:0.85rem; opacity:0.85;'>{cr.category.replace('_', ' ').title()}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            if response.complaint and response.complaint.matched_criteria:
                criteria_str = " · ".join(response.complaint.matched_criteria)
                st.caption(f"Triggered by: {criteria_str}")

            st.markdown(
                "<div style='font-size:0.75rem; opacity:0.55; margin-top:0.75rem; "
                "text-transform:uppercase; letter-spacing:0.05em;'>Passing to Agent Actions ↓</div>",
                unsafe_allow_html=True,
            )

    def render_history(
        self,
        container: DeltaGenerator,
        messages: List[ChatMessage],
    ) -> None:
        """Render all evaluation results from session history in stacked layout."""
        assistant_messages = [msg for msg in messages if msg.role == "assistant"]

        for message in assistant_messages:
            with container:
                st.markdown(AGENT_LABELS["supervisor"])
                st.markdown(message.content)
                st.markdown("---")
                st.markdown(AGENT_LABELS["complaints"])
                if message.complaints_content:
                    st.markdown(message.complaints_content)
                if message.agent_response:
                    self.render_classification_result(container, message.agent_response)
