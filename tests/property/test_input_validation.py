"""Property-based tests for invalid input error handling.

Feature: agentcore-deployment, Property 2: Invalid Input Error Handling
"""

from hypothesis import given, settings, strategies as st

from agent import invoke_handler


class TestInvalidInputErrorHandling:
    """
    Feature: agentcore-deployment, Property 2: Invalid Input Error Handling
    
    *For any* payload that is missing the required `transcript` field or contains 
    an empty/whitespace-only transcript, the invoke function SHALL return an error 
    response with `status: "error"` and a non-empty `error_message` field.
    
    **Validates: Requirements 1.5, 9.5**
    """

    @settings(max_examples=10)
    @given(
        payload=st.dictionaries(
            keys=st.text(min_size=1, max_size=50).filter(lambda x: x != "transcript"),
            values=st.text(min_size=0, max_size=100),
            min_size=0,
            max_size=5
        )
    )
    def test_missing_transcript_returns_error(self, payload: dict):
        """Payloads without transcript field return error response."""
        result = invoke_handler(payload, {})
        
        assert result.get("status") == "error"
        assert "error_message" in result
        assert len(result["error_message"]) > 0
        assert "transcript" in result["error_message"].lower()

    @settings(max_examples=10)
    @given(
        whitespace=st.text(
            alphabet=" \t\n\r",
            min_size=0,
            max_size=20
        )
    )
    def test_empty_or_whitespace_transcript_returns_error(self, whitespace: str):
        """Empty or whitespace-only transcripts return error response."""
        payload = {"transcript": whitespace}
        result = invoke_handler(payload, {})
        
        assert result.get("status") == "error"
        assert "error_message" in result
        assert len(result["error_message"]) > 0

    @settings(max_examples=10)
    @given(
        non_string_value=st.one_of(
            st.integers(),
            st.floats(allow_nan=False),
            st.lists(st.text(), max_size=3),
            st.dictionaries(st.text(max_size=10), st.text(max_size=10), max_size=3),
            st.none(),
            st.booleans()
        )
    )
    def test_non_string_transcript_returns_error(self, non_string_value):
        """Non-string transcript values return error response."""
        payload = {"transcript": non_string_value}
        result = invoke_handler(payload, {})
        
        assert result.get("status") == "error"
        assert "error_message" in result
        assert len(result["error_message"]) > 0

    @settings(max_examples=10)
    @given(
        extra_fields=st.dictionaries(
            keys=st.text(min_size=1, max_size=20).filter(lambda x: x != "transcript"),
            values=st.text(min_size=0, max_size=50),
            min_size=1,
            max_size=5
        )
    )
    def test_missing_transcript_with_extra_fields_returns_error(self, extra_fields: dict):
        """Payloads with extra fields but no transcript return error."""
        result = invoke_handler(extra_fields, {})
        
        assert result.get("status") == "error"
        assert "error_message" in result
        assert "transcript" in result["error_message"].lower()

    def test_empty_payload_returns_error(self):
        """Empty payload returns error response."""
        result = invoke_handler({}, {})
        
        assert result.get("status") == "error"
        assert "error_message" in result
        assert "transcript" in result["error_message"].lower()

    def test_none_payload_transcript_returns_error(self):
        """Payload with None transcript returns error response."""
        result = invoke_handler({"transcript": None}, {})
        
        assert result.get("status") == "error"
        assert "error_message" in result
