"""Streamlit application entry point for the Complaints Agent.

Run this application with:
    streamlit run streamlit_app.py

The application provides a chat-like interface for submitting customer call
transcripts and receiving complaint analysis results including severity,
category, actions taken, and recommended next steps.
"""

import os
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

import opentelemetry.context.contextvars_context as otel_ctx

_original_detach = otel_ctx.ContextVarsRuntimeContext.detach

def _safe_detach(self, token):
    try:
        _original_detach(self, token)
    except ValueError:
        pass

otel_ctx.ContextVarsRuntimeContext.detach = _safe_detach

from complaints_agent.ui.app import main

if __name__ == "__main__":
    main()
