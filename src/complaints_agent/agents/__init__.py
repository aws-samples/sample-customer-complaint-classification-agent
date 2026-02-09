"""Agent implementations for the complaints system."""

import os
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from .complaints_agent import complaints_agent
from .supervisor_agent import SupervisorAgent

__all__ = [
    "complaints_agent",
    "SupervisorAgent",
]
