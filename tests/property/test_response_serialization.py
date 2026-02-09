"""Property-based tests for response serialization round-trip.

Feature: agentcore-deployment, Property 1: Response Serialization Round-Trip
"""

import json
from datetime import datetime

from hypothesis import given, settings, strategies as st

from complaints_agent.models import AgentResponse, Complaint, ComplaintResponse


severity_strategy = st.sampled_from(["low", "medium", "high", "critical"])
category_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
actions_strategy = st.lists(
    st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
    min_size=0,
    max_size=5
)
next_steps_strategy = st.lists(
    st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
    min_size=0,
    max_size=5
)
summary_strategy = st.text(min_size=1, max_size=500).filter(lambda x: x.strip())
transcript_strategy = st.text(min_size=1, max_size=500).filter(lambda x: x.strip())
matched_criteria_strategy = st.lists(
    st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    min_size=0,
    max_size=5
)


class TestResponseSerializationRoundTrip:
    """
    Feature: agentcore-deployment, Property 1: Response Serialization Round-Trip
    
    *For any* valid AgentResponse object returned by the SupervisorAgent, 
    serializing it to JSON and deserializing it back SHALL produce an 
    equivalent AgentResponse with identical field values.
    
    **Validates: Requirements 1.4, 9.3**
    """

    @settings(max_examples=10)
    @given(
        is_complaint=st.booleans(),
        summary=summary_strategy,
    )
    def test_non_complaint_response_round_trip(self, is_complaint: bool, summary: str):
        """Non-complaint responses serialize and deserialize correctly."""
        original = AgentResponse(
            is_complaint=False,
            summary=summary,
            complaint=None,
            complaint_response=None
        )
        
        json_str = original.to_json()
        restored = AgentResponse.from_json(json_str)
        
        assert restored.is_complaint == original.is_complaint
        assert restored.summary == original.summary
        assert restored.complaint == original.complaint
        assert restored.complaint_response == original.complaint_response

    @settings(max_examples=10)
    @given(
        summary=summary_strategy,
        transcript=transcript_strategy,
        matched_criteria=matched_criteria_strategy,
        severity=severity_strategy,
        category=category_strategy,
        actions_taken=actions_strategy,
        next_steps=next_steps_strategy,
    )
    def test_complaint_response_round_trip(
        self,
        summary: str,
        transcript: str,
        matched_criteria: list,
        severity: str,
        category: str,
        actions_taken: list,
        next_steps: list,
    ):
        """Complaint responses with full data serialize and deserialize correctly."""
        complaint = Complaint(
            transcript=transcript,
            classification_result="complaint",
            timestamp=datetime.now(),
            matched_criteria=matched_criteria
        )
        
        complaint_response = ComplaintResponse(
            severity=severity,
            category=category,
            actions_taken=actions_taken,
            next_steps=next_steps
        )
        
        original = AgentResponse(
            is_complaint=True,
            summary=summary,
            complaint=complaint,
            complaint_response=complaint_response
        )
        
        json_str = original.to_json()
        restored = AgentResponse.from_json(json_str)
        
        assert restored.is_complaint == original.is_complaint
        assert restored.summary == original.summary
        assert restored.complaint is not None
        assert restored.complaint.transcript == original.complaint.transcript
        assert restored.complaint.classification_result == original.complaint.classification_result
        assert restored.complaint.matched_criteria == original.complaint.matched_criteria
        assert restored.complaint_response is not None
        assert restored.complaint_response.severity == original.complaint_response.severity
        assert restored.complaint_response.category == original.complaint_response.category
        assert restored.complaint_response.actions_taken == original.complaint_response.actions_taken
        assert restored.complaint_response.next_steps == original.complaint_response.next_steps

    @settings(max_examples=10)
    @given(
        summary=summary_strategy,
        transcript=transcript_strategy,
        matched_criteria=matched_criteria_strategy,
    )
    def test_complaint_without_response_round_trip(
        self,
        summary: str,
        transcript: str,
        matched_criteria: list,
    ):
        """Complaint responses without ComplaintResponse serialize correctly."""
        complaint = Complaint(
            transcript=transcript,
            classification_result="complaint",
            timestamp=datetime.now(),
            matched_criteria=matched_criteria
        )
        
        original = AgentResponse(
            is_complaint=True,
            summary=summary,
            complaint=complaint,
            complaint_response=None
        )
        
        json_str = original.to_json()
        restored = AgentResponse.from_json(json_str)
        
        assert restored.is_complaint == original.is_complaint
        assert restored.summary == original.summary
        assert restored.complaint is not None
        assert restored.complaint.transcript == original.complaint.transcript
        assert restored.complaint_response is None

    @settings(max_examples=10)
    @given(
        summary=summary_strategy,
        severity=severity_strategy,
        category=category_strategy,
        actions_taken=actions_strategy,
        next_steps=next_steps_strategy,
    )
    def test_json_output_is_valid_json(
        self,
        summary: str,
        severity: str,
        category: str,
        actions_taken: list,
        next_steps: list,
    ):
        """Serialized output is always valid JSON."""
        complaint_response = ComplaintResponse(
            severity=severity,
            category=category,
            actions_taken=actions_taken,
            next_steps=next_steps
        )
        
        original = AgentResponse(
            is_complaint=True,
            summary=summary,
            complaint=None,
            complaint_response=complaint_response
        )
        
        json_str = original.to_json()
        parsed = json.loads(json_str)
        
        assert isinstance(parsed, dict)
        assert "is_complaint" in parsed
        assert "summary" in parsed
