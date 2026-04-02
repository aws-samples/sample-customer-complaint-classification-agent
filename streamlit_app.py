"""Streamlit application entry point for the Complaints Agent.

Run this application with:
    streamlit run streamlit_app.py

The application provides a chat-like interface for submitting customer call
transcripts and receiving complaint analysis results including severity,
category, actions taken, and recommended next steps.
"""

import os
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from complaint_system.ui.app import main

if __name__ == "__main__":
    main()
