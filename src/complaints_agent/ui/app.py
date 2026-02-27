"""Streamlit web interface for the complaints agent system.

This module provides the main Streamlit application for interacting with
the complaints agent system through a split-panel UI with file upload.
"""

import os
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

from complaints_agent.config.loader import ConfigurationLoader, ConfigurationError
from .layout import PanelLayout
from .conversation import ConversationRenderer
from .evaluation import EvaluationRenderer
from .actions import ActionsRenderer
from .approval import render_approval_gate, render_approval_dismissed
from .session import (
    initialize_session_state,
    get_messages,
    add_message,
    clear_chat_history,
    is_valid_transcript,
)
from .streaming import StreamingSupervisorAgent, SplitPanelStreamingHandler
from .mock_conversation import SAMPLE_CONVERSATIONS, ConversationSimulator


def render_live_conversation(
    conversation_idx: int,
    conversation_container,
    evaluation_container,
    actions_container,
) -> None:
    """Play a mock conversation and then analyze it."""
    sample = SAMPLE_CONVERSATIONS[conversation_idx]

    turn_placeholder = conversation_container.empty()
    accumulated_turns = []

    def on_turn(turn, index):
        accumulated_turns.append(turn)
        lines = []
        for t in accumulated_turns:
            if t.speaker == "Agent":
                lines.append(
                    f'<div style="padding: 0.3rem 0;">'
                    f'<span style="color: #1976d2; font-weight: 600;">🎧 Agent:</span> {t.message}</div>'
                )
            else:
                lines.append(
                    f'<div style="padding: 0.3rem 0;">'
                    f'<span style="color: #28a745; font-weight: 600;">👤 Customer:</span> {t.message}</div>'
                )

        turn_placeholder.markdown(
            f'<div style="background-color: var(--secondary-background-color); '
            f'border-left: 4px solid #1976d2; padding: 1rem; margin: 0.5rem 0; '
            f'border-radius: 0 8px 8px 0;">{"".join(lines)}</div>',
            unsafe_allow_html=True,
        )

    simulator = ConversationSimulator(sample, on_turn, min_delay=1.0, max_delay=3.0)
    transcript = simulator.play_all()

    turn_placeholder.empty()
    handle_transcript(transcript, conversation_container, evaluation_container, actions_container)


def display_history(conversation_container, evaluation_container, actions_container) -> None:
    """Render all messages from session state to separate panels."""
    messages = get_messages()
    ConversationRenderer().render_history(conversation_container, messages)
    EvaluationRenderer().render_history(evaluation_container, messages)
    ActionsRenderer().render_history(actions_container, messages)


def handle_transcript(
    transcript: str,
    conversation_container,
    evaluation_container,
    actions_container,
) -> None:
    """Process a transcript through the streaming agent and queue approval if needed."""
    user_message = add_message(role="user", content=transcript)
    ConversationRenderer().render_transcript(conversation_container, user_message)

    spinner_placeholder = conversation_container.empty()
    spinner_placeholder.status("Analyzing transcript…", expanded=False, state="running")

    try:
        criteria = ConfigurationLoader.load_from_default()
        agent = StreamingSupervisorAgent(criteria)

        ctx = get_script_run_ctx()

        def on_token(token: str) -> None:
            add_script_run_ctx(ctx=ctx)

        def on_agent_change(agent_name: str) -> None:
            add_script_run_ctx(ctx=ctx)

        streaming_handler = SplitPanelStreamingHandler(
            evaluation_container=evaluation_container,
            on_token=on_token,
            on_agent_change=on_agent_change,
        )
        streaming_handler.initialize_placeholders()

        response = agent.process_transcript_streaming(
            transcript,
            streaming_handler.handle_token,
            streaming_handler.handle_agent_change,
        )

        final_content = streaming_handler.finalize() or response.summary
        spinner_placeholder.empty()
        complaints_raw = streaming_handler.complaints_content

        complaints_column = streaming_handler.get_complaints_column()
        if complaints_column:
            EvaluationRenderer().render_classification_result(complaints_column, response)

        if response.is_complaint:
            add_message(
                role="assistant",
                content=final_content,
                agent_response=response,
                actions_approved=False,
                complaints_content=complaints_raw,
            )
            st.session_state["pending_approval"] = "waiting"
            st.session_state["pending_approval_response"] = response
            st.rerun()
        else:
            ActionsRenderer().render_actions_streaming(actions_container, response)
            add_message(
                role="assistant",
                content=final_content,
                agent_response=response,
                complaints_content=complaints_raw,
            )

    except ConfigurationError as e:
        spinner_placeholder.empty()
        with evaluation_container:
            st.error(f"Configuration error: {e}")
    except Exception as e:
        spinner_placeholder.empty()
        import traceback
        with evaluation_container:
            st.error(f"An error occurred while processing your request: {e}")
            with st.expander("Error Details"):
                st.code(traceback.format_exc(), language="python")


def _handle_pending_approval(actions_container) -> None:
    """Render the approval gate or process an approval decision."""
    approval_state = st.session_state.get("pending_approval")
    pending_response = st.session_state.get("pending_approval_response")

    if not pending_response:
        return

    if approval_state == "waiting":
        render_approval_gate(actions_container, pending_response)

    elif approval_state == "approved":
        messages = get_messages()
        for msg in reversed(messages):
            if msg.role == "assistant" and not msg.actions_approved and msg.agent_response is pending_response:
                msg.actions_approved = True
                break
        ActionsRenderer().render_actions_streaming(actions_container, pending_response)
        st.session_state.pop("pending_approval", None)
        st.session_state.pop("pending_approval_response", None)

    elif approval_state == "dismissed":
        render_approval_dismissed(actions_container)
        st.session_state.pop("pending_approval", None)
        st.session_state.pop("pending_approval_response", None)


def main() -> None:
    """Main entry point for the Streamlit application."""
    st.set_page_config(page_title="Complaints Analysis", page_icon="📞", layout="wide")

    st.title("📞 Complaints Agent")
    st.markdown(
        "Upload a customer call transcript or select a demo conversation to analyze. "
        "The system will classify the interaction and provide routing, severity assessment, "
        "and recommended actions."
    )

    initialize_session_state()

    with st.sidebar:
        st.header("Options")
        if st.button("🗑️ Clear History"):
            clear_chat_history()
            st.rerun()

        st.divider()

        st.header("📄 Upload Transcript")
        uploaded_file = st.file_uploader(
            "Upload a .txt file containing a call transcript",
            type=["txt"],
            key="transcript_upload",
        )
        if uploaded_file is not None:
            if "last_uploaded_file" not in st.session_state or st.session_state["last_uploaded_file"] != uploaded_file.name:
                st.session_state["last_uploaded_file"] = uploaded_file.name
                st.session_state["pending_transcript"] = uploaded_file.read().decode("utf-8")
                st.rerun()

        st.divider()

        st.header("🎭 Demo Conversations")
        st.markdown("Select a sample conversation:")

        for idx, sample in enumerate(SAMPLE_CONVERSATIONS):
            icon = "🚨" if "complaint" in sample.name.lower() or "dispute" in sample.name.lower() else "💬"
            if st.button(f"{icon} {sample.name}", key=f"demo_{idx}", use_container_width=True):
                st.session_state["pending_demo"] = idx
                st.rerun()

    layout = PanelLayout()
    conversation_container, evaluation_container, actions_container = layout.create_layout()

    display_history(conversation_container, evaluation_container, actions_container)

    if "pending_approval" in st.session_state:
        _handle_pending_approval(actions_container)

    if "pending_transcript" in st.session_state:
        transcript = st.session_state.pop("pending_transcript")
        if is_valid_transcript(transcript):
            handle_transcript(transcript, conversation_container, evaluation_container, actions_container)
        else:
            st.warning("Uploaded file was empty or contained only whitespace.")

    if "pending_demo" in st.session_state:
        demo_idx = st.session_state.pop("pending_demo")
        render_live_conversation(demo_idx, conversation_container, evaluation_container, actions_container)


if __name__ == "__main__":
    main()
