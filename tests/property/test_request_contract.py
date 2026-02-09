"""Property-based tests for request contract validation.

Feature: agentcore-deployment, Property 8: Request Contract Validation

**Validates: Requirements 9.1, 9.2**
"""

from unittest.mock import patch, MagicMock

from hypothesis import given, settings, strategies as st

from agent import invoke_handler


class TestRequestContractValidation:
    """
    Feature: agentcore-deployment, Property 8: Request Contract Validation
    
    *For any* valid JSON payload containing a non-empty `transcript` field, 
    the invoke function SHALL accept the request and return a response with 
    a `result` field. Optional `config_override` fields SHALL be processed 
    when present without causing errors.
    
    **Validates: Requirements 9.1, 9.2**
    """

    @settings(max_examples=10)
    @given(
        transcript=st.text(min_size=1, max_size=200).filter(lambda x: x.strip())
    )
    def test_valid_transcript_returns_result(self, transcript: str):
        """Valid non-empty transcript returns response with result field."""
        mock_response = MagicMock()
        mock_response.to_json.return_value = '{"is_complaint": false, "summary": "test", "complaint": null, "complaint_response": null}'
        
        with patch('agent.SupervisorAgent') as mock_supervisor:
            mock_supervisor.return_value.process_transcript.return_value = mock_response
            
            payload = {"transcript": transcript}
            result = invoke_handler(payload, {})
            
            assert "result" in result
            assert "status" not in result or result.get("status") != "error"

    @settings(max_examples=10)
    @given(
        transcript=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
        keywords=st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=5),
        sentiment_indicators=st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=5),
    )
    def test_valid_transcript_with_config_override_returns_result(
        self, transcript: str, keywords: list, sentiment_indicators: list
    ):
        """Valid transcript with config_override returns response with result field."""
        mock_response = MagicMock()
        mock_response.to_json.return_value = '{"is_complaint": false, "summary": "test", "complaint": null, "complaint_response": null}'
        
        with patch('agent.SupervisorAgent') as mock_supervisor:
            mock_supervisor.return_value.process_transcript.return_value = mock_response
            
            payload = {
                "transcript": transcript,
                "config_override": {
                    "keywords": keywords,
                    "sentiment_indicators": sentiment_indicators
                }
            }
            result = invoke_handler(payload, {})
            
            assert "result" in result
            assert "status" not in result or result.get("status") != "error"

    @settings(max_examples=10)
    @given(
        transcript=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
        severity_thresholds=st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.integers(min_value=0, max_value=100),
            min_size=0,
            max_size=3
        )
    )
    def test_config_override_with_severity_thresholds(
        self, transcript: str, severity_thresholds: dict
    ):
        """Config override with severity_thresholds is processed without errors."""
        mock_response = MagicMock()
        mock_response.to_json.return_value = '{"is_complaint": false, "summary": "test", "complaint": null, "complaint_response": null}'
        
        with patch('agent.SupervisorAgent') as mock_supervisor:
            mock_supervisor.return_value.process_transcript.return_value = mock_response
            
            payload = {
                "transcript": transcript,
                "config_override": {
                    "severity_thresholds": severity_thresholds
                }
            }
            result = invoke_handler(payload, {})
            
            assert "result" in result
            assert "status" not in result or result.get("status") != "error"

    @settings(max_examples=10)
    @given(
        transcript=st.text(min_size=1, max_size=200).filter(lambda x: x.strip())
    )
    def test_empty_config_override_is_valid(self, transcript: str):
        """Empty config_override dict is processed without errors."""
        mock_response = MagicMock()
        mock_response.to_json.return_value = '{"is_complaint": false, "summary": "test", "complaint": null, "complaint_response": null}'
        
        with patch('agent.SupervisorAgent') as mock_supervisor:
            mock_supervisor.return_value.process_transcript.return_value = mock_response
            
            payload = {
                "transcript": transcript,
                "config_override": {}
            }
            result = invoke_handler(payload, {})
            
            assert "result" in result
            assert "status" not in result or result.get("status") != "error"

    @settings(max_examples=10)
    @given(
        transcript=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
        invalid_override=st.one_of(
            st.integers(),
            st.text(min_size=1, max_size=20),
            st.lists(st.text(), max_size=3),
            st.booleans()
        )
    )
    def test_invalid_config_override_type_returns_error(
        self, transcript: str, invalid_override
    ):
        """Non-dict config_override returns error response."""
        payload = {
            "transcript": transcript,
            "config_override": invalid_override
        }
        result = invoke_handler(payload, {})
        
        assert result.get("status") == "error"
        assert "error_message" in result
        assert "config_override" in result["error_message"].lower()

    def test_valid_transcript_without_config_override(self):
        """Valid transcript without config_override returns result."""
        mock_response = MagicMock()
        mock_response.to_json.return_value = '{"is_complaint": false, "summary": "test", "complaint": null, "complaint_response": null}'
        
        with patch('agent.SupervisorAgent') as mock_supervisor:
            mock_supervisor.return_value.process_transcript.return_value = mock_response
            
            payload = {"transcript": "Customer called about their account."}
            result = invoke_handler(payload, {})
            
            assert "result" in result

    def test_config_override_partial_fields(self):
        """Config override with only some fields is valid."""
        mock_response = MagicMock()
        mock_response.to_json.return_value = '{"is_complaint": false, "summary": "test", "complaint": null, "complaint_response": null}'
        
        with patch('agent.SupervisorAgent') as mock_supervisor:
            mock_supervisor.return_value.process_transcript.return_value = mock_response
            
            payload = {
                "transcript": "Customer inquiry about services.",
                "config_override": {
                    "keywords": ["complaint", "issue"]
                }
            }
            result = invoke_handler(payload, {})
            
            assert "result" in result
