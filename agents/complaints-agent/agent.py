"""AgentCore Entry Point Wrapper for Complaints Agent MCP Server."""

import sys
from pathlib import Path

src_path = Path(__file__).parent / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

shared_root = Path(__file__).parent.parent.parent
if str(shared_root) not in sys.path:
    sys.path.insert(0, str(shared_root))

from bedrock_agentcore import BedrockAgentCoreApp

from complaints_agent_mcp.mcp_server import ComplaintsAgentMCPServer

app = BedrockAgentCoreApp()
mcp_server = ComplaintsAgentMCPServer()


@app.entrypoint
def invoke(payload: dict, context: dict) -> dict:
    """Handle incoming requests by delegating to the MCP server.

    Args:
        payload: Dictionary containing the request with 'transcript' and
                optional 'matched_criteria' fields.
        context: AgentCore context dictionary (unused).

    Returns:
        Dictionary containing either the result or error information.
    """
    return mcp_server.handle_request(payload)


if __name__ == "__main__":
    app.run()
