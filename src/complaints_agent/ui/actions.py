"""Agent actions panel rendering for the split UI.

This module provides the ActionsRenderer class that renders
mock agent actions (API calls, case lookups, ticket creation)
in the actions panel at the bottom of the UI.
"""

import time
import random
from dataclasses import dataclass, field
from typing import List, Optional

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from complaints_agent.models import AgentResponse
from .session import ChatMessage


@dataclass
class AgentAction:
    """Represents a single action taken by the agent."""
    method: str
    endpoint: str
    status_code: int
    description: str
    detail: Optional[str] = None


ACTIONS_CSS = """
<style>
.actions-container {
    background-color: var(--secondary-background-color);
    border-left: 4px solid #6f42c1;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 0 8px 8px 0;
}

.actions-timestamp {
    font-size: 0.75rem;
    color: var(--text-color);
    opacity: 0.7;
    margin-bottom: 0.5rem;
}

.action-row {
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 0.85rem;
    padding: 0.35rem 0.6rem;
    margin: 0.25rem 0;
    border-radius: 4px;
    background-color: rgba(0, 0, 0, 0.15);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.action-method {
    font-weight: 700;
    padding: 0.1rem 0.4rem;
    border-radius: 3px;
    font-size: 0.75rem;
    min-width: 3.5rem;
    text-align: center;
    display: inline-block;
}

.method-get { background-color: #1976d2; color: white; }
.method-post { background-color: #28a745; color: white; }
.method-put { background-color: #fd7e14; color: white; }

.action-endpoint {
    color: var(--text-color);
    opacity: 0.9;
}

.action-status {
    margin-left: auto;
    font-weight: 600;
    font-size: 0.75rem;
}

.status-200 { color: #28a745; }
.status-201 { color: #28a745; }
.status-404 { color: #ffc107; }

.action-desc {
    font-size: 0.8rem;
    color: var(--text-color);
    opacity: 0.7;
    padding-left: 4.5rem;
    margin-top: -0.15rem;
    margin-bottom: 0.3rem;
}

.actions-summary {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    margin-top: 0.75rem;
    padding-top: 0.75rem;
}

.actions-summary-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: #6f42c1;
    margin-bottom: 0.4rem;
}

.actions-summary-text {
    font-size: 0.85rem;
    color: var(--text-color);
    opacity: 0.85;
    line-height: 1.5;
}

.actions-summary-list {
    font-size: 0.85rem;
    color: var(--text-color);
    opacity: 0.85;
    margin: 0.25rem 0 0 1.2rem;
    padding: 0;
}

.actions-summary-list li {
    margin-bottom: 0.15rem;
}
</style>
"""


def _generate_case_id() -> str:
    return f"CASE-{random.randint(100000, 999999)}"


def _generate_ticket_id() -> str:
    return f"TKT-{random.randint(10000, 99999)}"


def build_complaint_actions(response: AgentResponse) -> List[AgentAction]:
    """Build a list of mock agent actions based on the complaint response.

    For complaints, simulates looking up existing cases, checking status,
    and creating a new ticket if none exists. For non-complaints, returns
    a minimal set of logging actions.
    """
    if not response.is_complaint:
        return [
            AgentAction("GET", "/api/v1/classify", 200, "Transcript classified as non-complaint"),
            AgentAction("POST", "/api/v1/audit/log", 201, "Classification result logged"),
        ]

    category = response.complaint_response.category if response.complaint_response else "general"
    severity = response.complaint_response.severity if response.complaint_response else "medium"
    routing_group = response.complaint_response.routing_group if response.complaint_response else "disputes"
    case_id = _generate_case_id()
    ticket_id = _generate_ticket_id()
    queue_label = routing_group.replace("_", " ").title()

    actions = [
        AgentAction(
            "GET", "/api/v1/classify", 200,
            "Transcript classified as complaint",
            f"Category: {category} | Severity: {severity}",
        ),
        AgentAction(
            "GET", f"/api/v1/routing/group/{routing_group}", 200,
            f"Routing group resolved: {queue_label}",
            f"Category '{category}' mapped to {queue_label} queue",
        ),
        AgentAction(
            "GET", f"/api/v1/cases?routing_group={routing_group}&status=open", 200,
            "Searching for existing open cases",
            "Checking case management system for matching records",
        ),
        AgentAction(
            "GET", f"/api/v1/cases/{case_id}/description", 404,
            "No matching open case found",
            f"Case {case_id} not found — will create new ticket",
        ),
        AgentAction(
            "POST", "/api/v1/cases", 201,
            f"New case created: {case_id}",
            f"Severity: {severity.upper()} | Routing: {queue_label}",
        ),
        AgentAction(
            "POST", f"/api/v1/cases/{case_id}/tickets", 201,
            f"Support ticket created: {ticket_id}",
            f"Assigned to {queue_label} queue",
        ),
    ]

    if severity in ("high", "critical"):
        actions.append(AgentAction(
            "POST", f"/api/v1/cases/{case_id}/escalate", 201,
            f"Case escalated — severity {severity.upper()}",
            "Notification sent to senior support team",
        ))

    actions.append(AgentAction(
        "PUT", f"/api/v1/cases/{case_id}/status", 200,
        "Case status updated to IN_PROGRESS",
    ))

    return actions


def _render_action_html(action: AgentAction) -> str:
    method_lower = action.method.lower()
    status_cls = f"status-{action.status_code}"

    html = (
        f'<div class="action-row">'
        f'<span class="action-method method-{method_lower}">{action.method}</span>'
        f'<span class="action-endpoint">{action.endpoint}</span>'
        f'<span class="action-status {status_cls}">{action.status_code}</span>'
        f'</div>'
    )
    if action.detail:
        html += f'<div class="action-desc">{action.detail}</div>'
    return html

def _render_summary_html(response: AgentResponse) -> str:
    """Build an HTML summary block describing what the agent did."""
    parts = [
        '<div class="actions-summary">',
        '<div class="actions-summary-title">📋 Summary</div>',
        f'<div class="actions-summary-text">{response.summary}</div>',
    ]

    cr = response.complaint_response
    if cr and cr.actions_taken:
        parts.append('<ul class="actions-summary-list">')
        for item in cr.actions_taken:
            parts.append(f"<li>{item}</li>")
        parts.append("</ul>")

    parts.append("</div>")
    return "".join(parts)



class ActionsRenderer:
    """Renders mock agent actions in the actions panel."""

    def render_actions_streaming(
        self,
        container: DeltaGenerator,
        response: AgentResponse,
        delay_range: tuple[float, float] = (0.3, 0.8),
    ) -> None:
        """Render actions one-by-one with a simulated delay for demo effect."""
        actions = build_complaint_actions(response)
        placeholder = container.empty()
        rendered_html = ""

        for action in actions:
            time.sleep(random.uniform(*delay_range))
            rendered_html += _render_action_html(action)
            placeholder.markdown(
                ACTIONS_CSS + f'<div class="actions-container">{rendered_html}</div>',
                unsafe_allow_html=True,
            )

        time.sleep(random.uniform(*delay_range))
        rendered_html += _render_summary_html(response)
        placeholder.markdown(
            ACTIONS_CSS + f'<div class="actions-container">{rendered_html}</div>',
            unsafe_allow_html=True,
        )

    def render_actions_static(
        self,
        container: DeltaGenerator,
        response: AgentResponse,
    ) -> None:
        """Render all actions at once (used for history replay)."""
        actions = build_complaint_actions(response)
        if not actions:
            return

        html_parts = [_render_action_html(a) for a in actions]
        html_parts.append(_render_summary_html(response))
        with container:
            st.markdown(
                ACTIONS_CSS
                + f'<div class="actions-container">{"".join(html_parts)}</div>',
                unsafe_allow_html=True,
            )

    def render_history(
        self,
        container: DeltaGenerator,
        messages: List[ChatMessage],
    ) -> None:
        """Render action logs from session history for approved assistant messages."""
        assistant_messages = [
            m for m in messages
            if m.role == "assistant" and m.actions_approved
        ]

        for message in assistant_messages:
            if message.agent_response:
                timestamp_str = message.timestamp.strftime("%H:%M:%S")
                with container:
                    st.markdown(
                        f'<div style="font-size:0.75rem; opacity:0.7;">⚡ {timestamp_str}</div>',
                        unsafe_allow_html=True,
                    )
                self.render_actions_static(container, message.agent_response)
