"""Human-in-the-loop approval gate between agent evaluation and agent actions."""

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from complaints_agent.models import AgentResponse
from .evaluation import ROUTING_GROUP_CONFIG, SEVERITY_COLORS


def render_approval_gate(container: DeltaGenerator, response: AgentResponse) -> None:
    """Render the human approval prompt between evaluation and actions.

    Shows a summary of the complaints agent recommendation and presents
    approve/dismiss buttons. On approval, sets session state to trigger
    the actions panel. On dismissal, marks the case as closed.

    Args:
        container: The Streamlit container to render into
        response: The AgentResponse from the supervisor agent
    """
    if not response.is_complaint:
        return

    cr = response.complaint_response
    if not cr:
        return

    routing = ROUTING_GROUP_CONFIG.get(cr.routing_group, ROUTING_GROUP_CONFIG["disputes"])
    severity_color = SEVERITY_COLORS.get(cr.severity.lower(), "#6c757d")

    with container:
        st.markdown(
            f"<div style='border: 1px solid {routing['color']}; border-radius: 8px; "
            f"padding: 1rem 1.25rem; margin: 0.5rem 0;'>"
            f"<div style='font-size:0.75rem; opacity:0.6; text-transform:uppercase; "
            f"letter-spacing:0.05em; margin-bottom:0.5rem;'>👤 Human Agent Review</div>"
            f"<div style='font-size:0.95rem; margin-bottom:0.25rem;'>"
            f"Route to <strong style='color:{routing['color']};'>{routing['icon']} {routing['label']}</strong> "
            f"with severity <strong style='color:{severity_color};'>{cr.severity.upper()}</strong>?</div>"
            f"<div style='font-size:0.82rem; opacity:0.7;'>"
            f"{cr.category.replace('_', ' ').title()}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        col_approve, col_dismiss, _ = st.columns([1, 1, 4])
        with col_approve:
            if st.button("✅ Approve", key="approval_approve", type="primary", use_container_width=True):
                st.session_state["pending_approval"] = "approved"
                st.rerun()
        with col_dismiss:
            if st.button("✗ Dismiss", key="approval_dismiss", use_container_width=True):
                st.session_state["pending_approval"] = "dismissed"
                st.rerun()


def render_approval_dismissed(container: DeltaGenerator) -> None:
    """Render a closed/dismissed state in the actions panel."""
    with container:
        st.markdown(
            "<div style='opacity:0.5; font-size:0.85rem; padding:0.5rem 0;'>"
            "✗ Recommendation dismissed — no actions taken."
            "</div>",
            unsafe_allow_html=True,
        )
