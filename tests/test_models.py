"""Property-based tests and unit tests for data models."""

from datetime import datetime, timezone

from hypothesis import given, settings, strategies as st

from complaints_agent.models import ComplaintCriteria, Complaint, ComplaintResponse, AgentResponse


# Strategies for generating test data
keywords_strategy = st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=10)
sentiment_strategy = st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=10)
severity_thresholds_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=20),
    values=st.integers(min_value=0, max_value=100),
    min_size=0,
    max_size=5
)


class TestComplaintCriteriaProperties:
    """Property-based tests for ComplaintCriteria model."""

    @settings(max_examples=10)
    @given(
        keywords=keywords_strategy,
        sentiment_indicators=sentiment_strategy,
        severity_thresholds=severity_thresholds_strategy
    )
    def test_complaint_criteria_round_trip(
        self,
        keywords: list,
        sentiment_indicators: list,
        severity_thresholds: dict
    ):
        """
        **Feature: complaints-agent, Property 4: Complaint criteria round trip**
        
        *For any* valid ComplaintCriteria object, serializing to JSON and then 
        deserializing SHALL produce an equivalent ComplaintCriteria object.
        
        **Validates: Requirements 2.4, 2.5**
        """
        original = ComplaintCriteria(
            keywords=keywords,
            sentiment_indicators=sentiment_indicators,
            severity_thresholds=severity_thresholds
        )
        
        json_str = original.to_json()
        restored = ComplaintCriteria.from_json(json_str)
        
        assert restored.keywords == original.keywords
        assert restored.sentiment_indicators == original.sentiment_indicators
        assert restored.severity_thresholds == original.severity_thresholds



# Strategies for Complaint
transcript_strategy = st.text(min_size=1, max_size=500)
classification_result_strategy = st.sampled_from(["complaint", "non_complaint"])
timestamp_strategy = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 12, 31)
)
matched_criteria_strategy = st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=10)


class TestComplaintProperties:
    """Property-based tests for Complaint model."""

    @settings(max_examples=10)
    @given(
        transcript=transcript_strategy,
        classification_result=classification_result_strategy,
        timestamp=timestamp_strategy,
        matched_criteria=matched_criteria_strategy
    )
    def test_complaint_round_trip(
        self,
        transcript: str,
        classification_result: str,
        timestamp: datetime,
        matched_criteria: list
    ):
        """
        **Feature: complaints-agent, Property 11: Complaint data round trip**
        
        *For any* valid Complaint object, serializing to JSON and then 
        deserializing SHALL produce an equivalent Complaint object.
        
        **Validates: Requirements 6.4, 6.5**
        """
        original = Complaint(
            transcript=transcript,
            classification_result=classification_result,
            timestamp=timestamp,
            matched_criteria=matched_criteria
        )
        
        json_str = original.to_json()
        restored = Complaint.from_json(json_str)
        
        assert restored.transcript == original.transcript
        assert restored.classification_result == original.classification_result
        assert restored.timestamp == original.timestamp
        assert restored.matched_criteria == original.matched_criteria

    @settings(max_examples=10)
    @given(
        transcript=transcript_strategy,
        classification_result=classification_result_strategy,
        timestamp=timestamp_strategy,
        matched_criteria=matched_criteria_strategy
    )
    def test_complaint_required_fields(
        self,
        transcript: str,
        classification_result: str,
        timestamp: datetime,
        matched_criteria: list
    ):
        """
        **Feature: complaints-agent, Property 9: Complaint object contains required fields**
        
        *For any* Complaint object created by the system, the object SHALL contain 
        non-null transcript, classification_result, and timestamp fields.
        
        **Validates: Requirements 6.1**
        """
        complaint = Complaint(
            transcript=transcript,
            classification_result=classification_result,
            timestamp=timestamp,
            matched_criteria=matched_criteria
        )
        
        assert complaint.transcript is not None
        assert complaint.classification_result is not None
        assert complaint.timestamp is not None



# Strategies for ComplaintResponse
severity_strategy = st.sampled_from(["low", "medium", "high", "critical"])
category_strategy = st.text(min_size=1, max_size=100)
actions_taken_strategy = st.lists(st.text(min_size=1, max_size=200), min_size=0, max_size=10)
next_steps_strategy = st.lists(st.text(min_size=1, max_size=200), min_size=0, max_size=10)


class TestComplaintResponseProperties:
    """Property-based tests for ComplaintResponse model."""

    @settings(max_examples=10)
    @given(
        severity=severity_strategy,
        category=category_strategy,
        actions_taken=actions_taken_strategy,
        next_steps=next_steps_strategy
    )
    def test_complaint_response_round_trip(
        self,
        severity: str,
        category: str,
        actions_taken: list,
        next_steps: list
    ):
        """
        **Feature: complaints-agent, Property 12: ComplaintResponse data round trip**
        
        *For any* valid ComplaintResponse object, serializing to JSON and then 
        deserializing SHALL produce an equivalent ComplaintResponse object.
        
        **Validates: Requirements 6.4, 6.5**
        """
        original = ComplaintResponse(
            severity=severity,
            category=category,
            actions_taken=actions_taken,
            next_steps=next_steps
        )
        
        json_str = original.to_json()
        restored = ComplaintResponse.from_json(json_str)
        
        assert restored.severity == original.severity
        assert restored.category == original.category
        assert restored.actions_taken == original.actions_taken
        assert restored.next_steps == original.next_steps

    @settings(max_examples=10)
    @given(
        severity=severity_strategy,
        category=category_strategy,
        actions_taken=actions_taken_strategy,
        next_steps=next_steps_strategy
    )
    def test_complaint_response_required_fields(
        self,
        severity: str,
        category: str,
        actions_taken: list,
        next_steps: list
    ):
        """
        **Feature: complaints-agent, Property 10: Complaint response contains required fields**
        
        *For any* ComplaintResponse object created by the Complaints Agent, the object 
        SHALL contain non-null severity, category, actions_taken, and next_steps fields.
        
        **Validates: Requirements 6.2**
        """
        response = ComplaintResponse(
            severity=severity,
            category=category,
            actions_taken=actions_taken,
            next_steps=next_steps
        )
        
        assert response.severity is not None
        assert response.category is not None
        assert response.actions_taken is not None
        assert response.next_steps is not None
