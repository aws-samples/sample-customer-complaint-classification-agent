"""Property-based tests for exception error response structure.

Feature: agentcore-deployment, Property 3: Exception Error Response Structure
"""

import os
import tempfile
from unittest.mock import patch, MagicMock

from hypothesis import given, settings, strategies as st

from agent import invoke_handler


class TestExceptionErrorResponseStructure:
    """
    Feature: agentcore-deployment, Property 3: Exception Error Response Structure
    
    *For any* exception that occurs during transcript processing, the invoke function 
    SHALL catch the exception and return a structured error response containing 
    `status: "error"` and `error_message` fields, never propagating the raw exception.
    
    **Validates: Requirements 1.6, 9.4**
    """

    @settings(max_examples=10)
    @given(
        transcript=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
        exception_message=st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
    )
    def test_supervisor_agent_exception_returns_structured_error(
        self, transcript: str, exception_message: str
    ):
        """Exceptions from SupervisorAgent are caught and return structured error."""
        with patch("agent.SupervisorAgent") as mock_supervisor:
            mock_instance = MagicMock()
            mock_instance.process_transcript.side_effect = Exception(exception_message)
            mock_supervisor.return_value = mock_instance
            
            payload = {"transcript": transcript}
            result = invoke_handler(payload, {})
            
            assert result.get("status") == "error"
            assert "error_message" in result
            assert len(result["error_message"]) > 0
            assert "Agent processing failed" in result["error_message"]

    @settings(max_examples=10)
    @given(
        transcript=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
    )
    def test_config_file_not_found_returns_structured_error(self, transcript: str):
        """Missing config file returns structured error, not exception."""
        with patch.dict(os.environ, {"COMPLAINT_CRITERIA_PATH": "/nonexistent/path.json"}):
            payload = {"transcript": transcript}
            result = invoke_handler(payload, {})
            
            assert result.get("status") == "error"
            assert "error_message" in result
            assert len(result["error_message"]) > 0
            assert "configuration" in result["error_message"].lower()

    @settings(max_examples=10)
    @given(
        transcript=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
        invalid_json=st.text(min_size=1, max_size=50).filter(
            lambda x: x.strip() and not x.strip().startswith("{")
        )
    )
    def test_invalid_config_json_returns_structured_error(
        self, transcript: str, invalid_json: str
    ):
        """Invalid JSON in config file returns structured error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(invalid_json)
            temp_path = f.name
        
        try:
            with patch.dict(os.environ, {"COMPLAINT_CRITERIA_PATH": temp_path}):
                payload = {"transcript": transcript}
                result = invoke_handler(payload, {})
                
                assert result.get("status") == "error"
                assert "error_message" in result
                assert len(result["error_message"]) > 0
        finally:
            os.unlink(temp_path)

    @settings(max_examples=10)
    @given(
        transcript=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
        error_types=st.sampled_from([
            ValueError,
            RuntimeError,
            TypeError,
            KeyError,
            AttributeError,
        ])
    )
    def test_various_exception_types_return_structured_error(
        self, transcript: str, error_types
    ):
        """Various exception types are caught and return structured error."""
        with patch("agent.SupervisorAgent") as mock_supervisor:
            mock_instance = MagicMock()
            mock_instance.process_transcript.side_effect = error_types("Test error")
            mock_supervisor.return_value = mock_instance
            
            payload = {"transcript": transcript}
            result = invoke_handler(payload, {})
            
            assert result.get("status") == "error"
            assert "error_message" in result
            assert isinstance(result["error_message"], str)

    def test_exception_does_not_propagate(self):
        """Exceptions are caught and do not propagate to caller."""
        with patch("agent.SupervisorAgent") as mock_supervisor:
            mock_instance = MagicMock()
            mock_instance.process_transcript.side_effect = Exception("Critical failure")
            mock_supervisor.return_value = mock_instance
            
            payload = {"transcript": "Test transcript"}
            
            result = invoke_handler(payload, {})
            
            assert isinstance(result, dict)
            assert result.get("status") == "error"

    def test_error_response_has_required_fields(self):
        """Error responses always contain status and error_message fields."""
        with patch("agent.SupervisorAgent") as mock_supervisor:
            mock_instance = MagicMock()
            mock_instance.process_transcript.side_effect = Exception("Test")
            mock_supervisor.return_value = mock_instance
            
            payload = {"transcript": "Test transcript"}
            result = invoke_handler(payload, {})
            
            assert "status" in result
            assert "error_message" in result
            assert result["status"] == "error"
            assert isinstance(result["error_message"], str)
