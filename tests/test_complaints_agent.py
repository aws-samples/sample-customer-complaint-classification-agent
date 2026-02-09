"""Property-based tests for the Complaints Agent tool.

These tests verify that the Complaints Agent produces correct structured
responses and handles errors appropriately.
"""

import json

from hypothesis import given, settings, strategies as st

from complaints_agent.agents.complaints_agent import complaints_agent
from complaints_agent.models import ComplaintResponse


# Strategies for generating valid complaint data
transcript_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S', 'Z')),
    min_size=10,
    max_size=500
).filter(lambda x: x.strip())

matched_criteria_strategy = st.lists(
    st.sampled_from([
        "frustrated", "angry", "disappointed", "complaint",
        "problem", "issue", "broken", "defective", "refund",
        "terrible", "worst", "unacceptable"
    ]),
    min_size=0,
    max_size=5
)


class TestComplaintsAgentStructuredResponse:
    """Property-based tests for Complaints Agent structured response."""

    @settings(max_examples=5, deadline=180000)  # 3 minute deadline for LLM calls, reduced examples
    @given(
        transcript=transcript_strategy,
        matched_criteria=matched_criteria_strategy
    )
    def test_complaints_agent_produces_complete_structured_response(
        self,
        transcript: str,
        matched_criteria: list
    ):
        """
        **Feature: complaints-agent, Property 5: Complaints Agent produces complete structured response**
        
        *For any* valid complaint input, the Complaints Agent SHALL return a 
        ComplaintResponse containing non-empty severity, category, actions_taken, 
        and next_steps fields.
        
        **Validates: Requirements 3.1, 3.2, 3.3**
        """
        # Build valid complaint data
        complaint_data = json.dumps({
            "transcript": transcript,
            "classification_result": "complaint",
            "matched_criteria": matched_criteria
        })
        
        # Call the complaints agent
        result = complaints_agent(complaint_data)
        
        # Parse the result
        result_data = json.loads(result)
        
        # If there's an error status, the test should fail
        # (valid input should not produce errors)
        assert "status" not in result_data or result_data.get("status") != "error", \
            f"Valid input produced error: {result_data.get('error', 'unknown')}"
        
        # Verify all required fields are present and non-empty
        assert "severity" in result_data, "Response missing severity field"
        assert result_data["severity"], "Severity field is empty"
        assert result_data["severity"] in ["low", "medium", "high", "critical"], \
            f"Invalid severity value: {result_data['severity']}"
        
        assert "category" in result_data, "Response missing category field"
        assert result_data["category"], "Category field is empty"
        
        assert "actions_taken" in result_data, "Response missing actions_taken field"
        assert isinstance(result_data["actions_taken"], list), "actions_taken should be a list"
        assert len(result_data["actions_taken"]) > 0, "actions_taken list is empty"
        
        assert "next_steps" in result_data, "Response missing next_steps field"
        assert isinstance(result_data["next_steps"], list), "next_steps should be a list"
        assert len(result_data["next_steps"]) > 0, "next_steps list is empty"
        
        # Verify we can deserialize into ComplaintResponse
        response = ComplaintResponse.from_json(result)
        assert response.severity is not None
        assert response.category is not None
        assert response.actions_taken is not None
        assert response.next_steps is not None



# Strategies for generating invalid/error inputs
invalid_json_strategy = st.text(min_size=1, max_size=100).filter(
    lambda x: not x.strip().startswith('{')
)

empty_transcript_strategy = st.sampled_from(["", "   ", "\n", "\t"])


class TestComplaintsAgentErrorHandling:
    """Property-based tests for Complaints Agent error handling."""

    @settings(max_examples=10)
    @given(invalid_input=invalid_json_strategy)
    def test_invalid_json_produces_error_response(self, invalid_input: str):
        """
        **Feature: complaints-agent, Property 6: Error inputs produce error responses**
        
        *For any* invalid or malformed complaint input, the Complaints Agent SHALL 
        return a response indicating an error with descriptive details.
        
        **Validates: Requirements 3.4**
        
        Test case: Invalid JSON input
        """
        result = complaints_agent(invalid_input)
        result_data = json.loads(result)
        
        assert "status" in result_data, "Error response missing status field"
        assert result_data["status"] == "error", "Invalid JSON should produce error status"
        assert "error" in result_data, "Error response missing error details"
        assert result_data["error"], "Error details should not be empty"

    @settings(max_examples=10)
    @given(empty_transcript=empty_transcript_strategy)
    def test_empty_transcript_produces_error_response(self, empty_transcript: str):
        """
        **Feature: complaints-agent, Property 6: Error inputs produce error responses**
        
        *For any* invalid or malformed complaint input, the Complaints Agent SHALL 
        return a response indicating an error with descriptive details.
        
        **Validates: Requirements 3.4**
        
        Test case: Empty transcript
        """
        complaint_data = json.dumps({
            "transcript": empty_transcript,
            "classification_result": "complaint"
        })
        
        result = complaints_agent(complaint_data)
        result_data = json.loads(result)
        
        assert "status" in result_data, "Error response missing status field"
        assert result_data["status"] == "error", "Empty transcript should produce error status"
        assert "error" in result_data, "Error response missing error details"

    @settings(max_examples=10)
    @given(
        data=st.fixed_dictionaries({
            "classification_result": st.just("complaint"),
            "matched_criteria": st.just([])
        })
    )
    def test_missing_transcript_produces_error_response(self, data: dict):
        """
        **Feature: complaints-agent, Property 6: Error inputs produce error responses**
        
        *For any* invalid or malformed complaint input, the Complaints Agent SHALL 
        return a response indicating an error with descriptive details.
        
        **Validates: Requirements 3.4**
        
        Test case: Missing transcript field
        """
        complaint_data = json.dumps(data)
        
        result = complaints_agent(complaint_data)
        result_data = json.loads(result)
        
        assert "status" in result_data, "Error response missing status field"
        assert result_data["status"] == "error", "Missing transcript should produce error status"
        assert "error" in result_data, "Error response missing error details"
        assert "transcript" in result_data["error"].lower(), \
            "Error should mention missing transcript field"
