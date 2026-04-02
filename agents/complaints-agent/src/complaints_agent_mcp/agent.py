"""MCP-side re-export of shared complaints agent logic.

The actual implementation lives in shared/complaints/agent_logic.py.
This module re-exports it so existing imports within the MCP package continue to work.
"""

from shared.complaints.agent_logic import ComplaintsAgentLogic, get_model_config

__all__ = ["ComplaintsAgentLogic", "get_model_config"]
