"""Property-based tests for complaint response completeness.

Feature: streamlit-web-interface, Property 5: Complaint Response Completeness
"""

from datetime import datetime

from hypothesis import given, settings, strategies as st

from src.complaints_agent.models.agent_response import AgentResponse
from src.complaints_agent.models.complaint import Complaint
from src.complaints_agent.models.complaint_response import ComplaintResponse


severity_strategy = st.sampled_from(["low", "medium", "high", "critical"])
category_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
actions_strategy = st.lists(
    st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
    min_size=1,
    max_size=10
)
next_steps_strategy = st.lists(
    st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
    min_size=1,
    max_size=10
)
matched_criteria_strategy = st.lists(
    st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    min_size=1,
    max_size=10
)


class TestComplaintResponseCompleteness:
    """
    Feature: streamlit-web-interface, Property 5: Complaint Response Completeness
    
    *For any* AgentResponse where is_complaint is True, the complaint_response 
    field SHALL be non-None and SHALL contain: a non-empty severity string, 
    a non-empty category string, a non-empty actions_taken list, and a 
    non-empty next_steps list. Additionally, the complaint field SHALL 
    contain a non-empty matched_criteria list.
    
    **Validates: Requirements 3.3, 5.1, 5.2, 6.1, 6.2, 6.3, 6.4**
    """

    @settings(max_examples=10)
    @given(
        severity=severity_strategy,
        category=category_strategy,
        actions_taken=actions_strategy,
        next_steps=next_steps_strategy,
        matched_criteria=matched_criteria_strategy,
        transcript=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        summary=st.text(min_size=1, max_size=200).filter(lambda x: x.strip())
    )
    def test_complaint_response_has_non_empty_severity(
        self,
        severity: str,
        category: str,
        actions_taken: list[str],
        next_steps: list[str],
        matched_criteria: list[str],
        transcript: str,
        summary: str
    ):
        """Complaint responses have non-empty severity string."""
        complaint_response = ComplaintResponse(
            severity=severity,
            category=category,
            actions_taken=actions_taken,
            next_steps=next_steps
        )
        complaint = Complaint(
            transcript=transcript,
            classification_result="complaint",
            timestamp=datetime.now(),
            matched_criteria=matched_criteria
        )
        agent_response = AgentResponse(
            is_complaint=True,
            summary=summary,
            complaint=complaint,
            complaint_response=complaint_response
        )
        
        assert agent_response.is_complaint is True
        assert agent_response.complaint_response is not None
        assert isinstance(agent_response.complaint_response.severity, str)
        assert len(agent_response.complaint_response.severity) > 0

    @settings(max_examples=10)
    @given(
        severity=severity_strategy,
        category=category_strategy,
        actions_taken=actions_strategy,
        next_steps=next_steps_strategy,
        matched_criteria=matched_criteria_strategy,
        transcript=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        summary=st.text(min_size=1, max_size=200).filter(lambda x: x.strip())
    )
    def test_complaint_response_has_non_empty_category(
        self,
        severity: str,
        category: str,
        actions_taken: list[str],
        next_steps: list[str],
        matched_criteria: list[str],
        transcript: str,
        summary: str
    ):
        """Complaint responses have non-empty category string."""
        complaint_response = ComplaintResponse(
            severity=severity,
            category=category,
            actions_taken=actions_taken,
            next_steps=next_steps
        )
        complaint = Complaint(
            transcript=transcript,
            classification_result="complaint",
            timestamp=datetime.now(),
            matched_criteria=matched_criteria
        )
        agent_response = AgentResponse(
            is_complaint=True,
            summary=summary,
            complaint=complaint,
            complaint_response=complaint_response
        )
        
        assert agent_response.is_complaint is True
        assert agent_response.complaint_response is not None
        assert isinstance(agent_response.complaint_response.category, str)
        assert len(agent_response.complaint_response.category) > 0

    @settings(max_examples=10)
    @given(
        severity=severity_strategy,
        category=category_strategy,
        actions_taken=actions_strategy,
        next_steps=next_steps_strategy,
        matched_criteria=matched_criteria_strategy,
        transcript=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        summary=st.text(min_size=1, max_size=200).filter(lambda x: x.strip())
    )
    def test_complaint_response_has_non_empty_actions_taken(
        self,
        severity: str,
        category: str,
        actions_taken: list[str],
        next_steps: list[str],
        matched_criteria: list[str],
        transcript: str,
        summary: str
    ):
        """Complaint responses have non-empty actions_taken list."""
        complaint_response = ComplaintResponse(
            severity=severity,
            category=category,
            actions_taken=actions_taken,
            next_steps=next_steps
        )
        complaint = Complaint(
            transcript=transcript,
            classification_result="complaint",
            timestamp=datetime.now(),
            matched_criteria=matched_criteria
        )
        agent_response = AgentResponse(
            is_complaint=True,
            summary=summary,
            complaint=complaint,
            complaint_response=complaint_response
        )
        
        assert agent_response.is_complaint is True
        assert agent_response.complaint_response is not None
        assert isinstance(agent_response.complaint_response.actions_taken, list)
        assert len(agent_response.complaint_response.actions_taken) > 0

    @settings(max_examples=10)
    @given(
        severity=severity_strategy,
        category=category_strategy,
        actions_taken=actions_strategy,
        next_steps=next_steps_strategy,
        matched_criteria=matched_criteria_strategy,
        transcript=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        summary=st.text(min_size=1, max_size=200).filter(lambda x: x.strip())
    )
    def test_complaint_response_has_non_empty_next_steps(
        self,
        severity: str,
        category: str,
        actions_taken: list[str],
        next_steps: list[str],
        matched_criteria: list[str],
        transcript: str,
        summary: str
    ):
        """Complaint responses have non-empty next_steps list."""
        complaint_response = ComplaintResponse(
            severity=severity,
            category=category,
            actions_taken=actions_taken,
            next_steps=next_steps
        )
        complaint = Complaint(
            transcript=transcript,
            classification_result="complaint",
            timestamp=datetime.now(),
            matched_criteria=matched_criteria
        )
        agent_response = AgentResponse(
            is_complaint=True,
            summary=summary,
            complaint=complaint,
            complaint_response=complaint_response
        )
        
        assert agent_response.is_complaint is True
        assert agent_response.complaint_response is not None
        assert isinstance(agent_response.complaint_response.next_steps, list)
        assert len(agent_response.complaint_response.next_steps) > 0

    @settings(max_examples=10)
    @given(
        severity=severity_strategy,
        category=category_strategy,
        actions_taken=actions_strategy,
        next_steps=next_steps_strategy,
        matched_criteria=matched_criteria_strategy,
        transcript=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        summary=st.text(min_size=1, max_size=200).filter(lambda x: x.strip())
    )
    def test_complaint_has_non_empty_matched_criteria(
        self,
        severity: str,
        category: str,
        actions_taken: list[str],
        next_steps: list[str],
        matched_criteria: list[str],
        transcript: str,
        summary: str
    ):
        """Complaint field has non-empty matched_criteria list."""
        complaint_response = ComplaintResponse(
            severity=severity,
            category=category,
            actions_taken=actions_taken,
            next_steps=next_steps
        )
        complaint = Complaint(
            transcript=transcript,
            classification_result="complaint",
            timestamp=datetime.now(),
            matched_criteria=matched_criteria
        )
        agent_response = AgentResponse(
            is_complaint=True,
            summary=summary,
            complaint=complaint,
            complaint_response=complaint_response
        )
        
        assert agent_response.is_complaint is True
        assert agent_response.complaint is not None
        assert isinstance(agent_response.complaint.matched_criteria, list)
        assert len(agent_response.complaint.matched_criteria) > 0

    @settings(max_examples=10)
    @given(
        severity=severity_strategy,
        category=category_strategy,
        actions_taken=actions_strategy,
        next_steps=next_steps_strategy,
        matched_criteria=matched_criteria_strategy,
        transcript=st.text(min_size=1, max_size=500).filter(lambda x: x.strip()),
        summary=st.text(min_size=1, max_size=200).filter(lambda x: x.strip())
    )
    def test_complaint_response_completeness_all_fields(
        self,
        severity: str,
        category: str,
        actions_taken: list[str],
        next_steps: list[str],
        matched_criteria: list[str],
        transcript: str,
        summary: str
    ):
        """Complete complaint response has all required non-empty fields."""
        complaint_response = ComplaintResponse(
            severity=severity,
            category=category,
            actions_taken=actions_taken,
            next_steps=next_steps
        )
        complaint = Complaint(
            transcript=transcript,
            classification_result="complaint",
            timestamp=datetime.now(),
            matched_criteria=matched_criteria
        )
        agent_response = AgentResponse(
            is_complaint=True,
            summary=summary,
            complaint=complaint,
            complaint_response=complaint_response
        )
        
        assert agent_response.is_complaint is True
        assert agent_response.complaint_response is not None
        assert len(agent_response.complaint_response.severity) > 0
        assert len(agent_response.complaint_response.category) > 0
        assert len(agent_response.complaint_response.actions_taken) > 0
        assert len(agent_response.complaint_response.next_steps) > 0
        assert agent_response.complaint is not None
        assert len(agent_response.complaint.matched_criteria) > 0
