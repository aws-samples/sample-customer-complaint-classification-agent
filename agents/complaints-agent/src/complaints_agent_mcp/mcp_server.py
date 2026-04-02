"""MCP server implementation for the Complaints Agent."""

from botocore.exceptions import ClientError
from mcp.server import Server
from mcp.shared.exceptions import McpError
from mcp.types import (
    ErrorData,
    INTERNAL_ERROR,
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    Tool,
    TextContent,
)

from shared.complaints.agent_logic import ComplaintsAgentLogic


class ComplaintsAgentMCPServer:
    """MCP server that exposes the complaints agent functionality via Model Context Protocol."""

    def __init__(self, agent_logic: ComplaintsAgentLogic | None = None):
        """Initialize the MCP server with optional agent logic instance.
        
        Args:
            agent_logic: Optional ComplaintsAgentLogic instance. If not provided,
                        a new instance will be created with default configuration.
        """
        self.server = Server("complaints-agent")
        self.agent_logic = agent_logic or ComplaintsAgentLogic()
        self._register_tools()

    def _register_tools(self) -> None:
        """Register MCP tools with the server."""
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="process_complaint",
                    description="Process a classified complaint and determine appropriate actions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "transcript": {
                                "type": "string",
                                "description": "The customer call transcript"
                            },
                            "matched_criteria": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of matched complaint criteria"
                            }
                        },
                        "required": ["transcript"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            if name == "process_complaint":
                return await self._process_complaint(arguments)
            raise McpError(
                ErrorData(
                    code=METHOD_NOT_FOUND,
                    message="Method not found",
                )
            )

    def _validate_transcript(self, arguments: dict) -> str:
        """Validate the transcript field from arguments.
        
        Args:
            arguments: Dictionary containing request arguments.
            
        Returns:
            The validated transcript string.
            
        Raises:
            McpError: If transcript is missing or empty.
        """
        if "transcript" not in arguments:
            raise McpError(
                ErrorData(
                    code=INVALID_PARAMS,
                    message="Invalid params",
                    data={"field": "transcript", "reason": "required"},
                )
            )
        
        transcript = arguments["transcript"]
        
        if not isinstance(transcript, str) or not transcript.strip():
            raise McpError(
                ErrorData(
                    code=INVALID_PARAMS,
                    message="Invalid params",
                    data={"field": "transcript", "reason": "cannot be empty"},
                )
            )
        
        return transcript

    async def _process_complaint(self, arguments: dict) -> list[TextContent]:
        """Process a complaint request and return the response.
        
        Args:
            arguments: Dictionary containing 'transcript' and optional 'matched_criteria'.
            
        Returns:
            List containing a TextContent with the JSON-serialized ComplaintResponse.
            
        Raises:
            McpError: If validation fails or processing encounters an error.
        """
        transcript = self._validate_transcript(arguments)
        matched_criteria = arguments.get("matched_criteria", [])
        
        if not isinstance(matched_criteria, list):
            matched_criteria = []

        try:
            response = self.agent_logic.process(transcript, matched_criteria)
            return [TextContent(type="text", text=response.to_json())]
        except ClientError as e:
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message="Model invocation failed",
                    data={"details": str(e)},
                )
            ) from e
        except Exception as e:
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message="Internal error",
                    data={"details": str(e)},
                )
            ) from e
    def handle_request(self, payload: dict) -> dict:
        """Handle an incoming request from AgentCore entry point.

        This method provides a synchronous interface for the AgentCore entry point
        to invoke the MCP server's complaint processing functionality.

        Args:
            payload: Dictionary containing the request payload with 'transcript'
                    and optional 'matched_criteria' fields.

        Returns:
            Dictionary containing either:
            - {"result": {...}} on success with the ComplaintResponse data
            - {"status": "error", "error_message": "..."} on failure
        """
        try:
            transcript = self._validate_transcript(payload)
            matched_criteria = payload.get("matched_criteria", [])

            if not isinstance(matched_criteria, list):
                matched_criteria = []

            response = self.agent_logic.process(transcript, matched_criteria)
            return {"result": response.to_dict()}
        except McpError as e:
            return {
                "status": "error",
                "error_message": f"{e.error.message}: {e.error.data}" if e.error.data else e.error.message
            }
        except Exception as e:
            return {"status": "error", "error_message": f"Processing failed: {str(e)}"}


