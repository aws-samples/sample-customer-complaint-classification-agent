"""Property-based tests for serialization round-trip.

Feature: codebase-cleanup, Property 1: Serialization Round-Trip

**Validates: Requirements 1.3, 1.4, 1.5**
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from hypothesis import given, settings, strategies as st

from src.complaints_agent.models.base import Serializable


@dataclass
class MockComplaint(Serializable):
    """Mock Complaint model for testing serialization."""
    transcript: str
    classification_result: str
    timestamp: datetime
    matched_criteria: List[str] = field(default_factory=list)


@dataclass
class MockComplaintResponse(Serializable):
    """Mock ComplaintResponse model for testing serialization."""
    severity: str
    category: str
    actions_taken: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)


@dataclass
class MockComplaintCriteria(Serializable):
    """Mock ComplaintCriteria model for testing serialization."""
    keywords: List[str] = field(default_factory=list)
    sentiment_indicators: List[str] = field(default_factory=list)
    severity_thresholds: Dict[str, int] = field(default_factory=dict)


@dataclass
class MockAgentResponse(Serializable):
    """Mock AgentResponse model with nested models for testing serialization."""
    is_complaint: bool
    summary: str
    complaint: Optional[MockComplaint] = None
    complaint_response: Optional[MockComplaintResponse] = None


severity_strategy = st.sampled_from(["low", "medium", "high", "critical"])
category_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
classification_result_strategy = st.sampled_from(["complaint", "non_complaint"])
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
transcript_strategy = st.text(min_size=1, max_size=500).filter(lambda x: x.strip())
matched_criteria_strategy = st.lists(
    st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    min_size=0,
    max_size=5
)
summary_strategy = st.text(min_size=1, max_size=500).filter(lambda x: x.strip())
keywords_strategy = st.lists(
    st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    min_size=0,
    max_size=10
)
sentiment_indicators_strategy = st.lists(
    st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    min_size=0,
    max_size=10
)
severity_thresholds_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
    values=st.integers(min_value=0, max_value=100),
    min_size=0,
    max_size=5
)
datetime_strategy = st.datetimes(
    min_value=datetime(2000, 1, 1),
    max_value=datetime(2030, 12, 31)
)


@st.composite
def mock_complaint_strategy(draw):
    """Generate random MockComplaint objects for property testing."""
    return MockComplaint(
        transcript=draw(transcript_strategy),
        classification_result=draw(classification_result_strategy),
        timestamp=draw(datetime_strategy),
        matched_criteria=draw(matched_criteria_strategy)
    )


@st.composite
def mock_complaint_response_strategy(draw):
    """Generate random MockComplaintResponse objects for property testing."""
    return MockComplaintResponse(
        severity=draw(severity_strategy),
        category=draw(category_strategy),
        actions_taken=draw(actions_strategy),
        next_steps=draw(next_steps_strategy)
    )


@st.composite
def mock_complaint_criteria_strategy(draw):
    """Generate random MockComplaintCriteria objects for property testing."""
    return MockComplaintCriteria(
        keywords=draw(keywords_strategy),
        sentiment_indicators=draw(sentiment_indicators_strategy),
        severity_thresholds=draw(severity_thresholds_strategy)
    )


@st.composite
def mock_agent_response_strategy(draw):
    """Generate random MockAgentResponse objects with optional nested models."""
    is_complaint = draw(st.booleans())
    summary = draw(summary_strategy)
    complaint = draw(st.one_of(st.none(), mock_complaint_strategy())) if is_complaint else None
    complaint_response = draw(st.one_of(st.none(), mock_complaint_response_strategy())) if is_complaint else None
    return MockAgentResponse(
        is_complaint=is_complaint,
        summary=summary,
        complaint=complaint,
        complaint_response=complaint_response
    )


class TestSerializationRoundTrip:
    """Property tests for serialization round-trip.

    *For any* valid Model object (Complaint, ComplaintResponse, ComplaintCriteria,
    or AgentResponse), serializing it to JSON and deserializing it back SHALL
    produce an equivalent object with identical field values, including datetime
    fields and nested Model objects.

    **Validates: Requirements 1.3, 1.4, 1.5**
    """

    @settings(max_examples=10)
    @given(complaint=mock_complaint_strategy())
    def test_complaint_round_trip(self, complaint: MockComplaint):
        """Complaint objects serialize and deserialize with identical field values."""
        json_str = complaint.to_json()
        restored = MockComplaint.from_json(json_str)

        assert restored.transcript == complaint.transcript
        assert restored.classification_result == complaint.classification_result
        assert restored.timestamp == complaint.timestamp
        assert restored.matched_criteria == complaint.matched_criteria

    @settings(max_examples=10)
    @given(response=mock_complaint_response_strategy())
    def test_complaint_response_round_trip(self, response: MockComplaintResponse):
        """ComplaintResponse objects serialize and deserialize with identical field values."""
        json_str = response.to_json()
        restored = MockComplaintResponse.from_json(json_str)

        assert restored.severity == response.severity
        assert restored.category == response.category
        assert restored.actions_taken == response.actions_taken
        assert restored.next_steps == response.next_steps

    @settings(max_examples=10)
    @given(criteria=mock_complaint_criteria_strategy())
    def test_complaint_criteria_round_trip(self, criteria: MockComplaintCriteria):
        """ComplaintCriteria objects serialize and deserialize with identical field values."""
        json_str = criteria.to_json()
        restored = MockComplaintCriteria.from_json(json_str)

        assert restored.keywords == criteria.keywords
        assert restored.sentiment_indicators == criteria.sentiment_indicators
        assert restored.severity_thresholds == criteria.severity_thresholds

    @settings(max_examples=10)
    @given(agent_response=mock_agent_response_strategy())
    def test_agent_response_round_trip(self, agent_response: MockAgentResponse):
        """AgentResponse objects with nested models serialize and deserialize correctly."""
        json_str = agent_response.to_json()
        restored = MockAgentResponse.from_json(json_str)

        assert restored.is_complaint == agent_response.is_complaint
        assert restored.summary == agent_response.summary

        if agent_response.complaint is None:
            assert restored.complaint is None
        else:
            assert restored.complaint is not None
            assert restored.complaint.transcript == agent_response.complaint.transcript
            assert restored.complaint.classification_result == agent_response.complaint.classification_result
            assert restored.complaint.timestamp == agent_response.complaint.timestamp
            assert restored.complaint.matched_criteria == agent_response.complaint.matched_criteria

        if agent_response.complaint_response is None:
            assert restored.complaint_response is None
        else:
            assert restored.complaint_response is not None
            assert restored.complaint_response.severity == agent_response.complaint_response.severity
            assert restored.complaint_response.category == agent_response.complaint_response.category
            assert restored.complaint_response.actions_taken == agent_response.complaint_response.actions_taken
            assert restored.complaint_response.next_steps == agent_response.complaint_response.next_steps

    @settings(max_examples=10)
    @given(timestamp=datetime_strategy)
    def test_datetime_preservation(self, timestamp: datetime):
        """Datetime fields are preserved correctly through serialization."""
        complaint = MockComplaint(
            transcript="Test transcript",
            classification_result="complaint",
            timestamp=timestamp,
            matched_criteria=[]
        )

        json_str = complaint.to_json()
        restored = MockComplaint.from_json(json_str)

        assert restored.timestamp == timestamp
        assert restored.timestamp.year == timestamp.year
        assert restored.timestamp.month == timestamp.month
        assert restored.timestamp.day == timestamp.day
        assert restored.timestamp.hour == timestamp.hour
        assert restored.timestamp.minute == timestamp.minute
        assert restored.timestamp.second == timestamp.second

    @settings(max_examples=10)
    @given(
        complaint=mock_complaint_strategy(),
        complaint_response=mock_complaint_response_strategy()
    )
    def test_nested_serializable_preservation(
        self, complaint: MockComplaint, complaint_response: MockComplaintResponse
    ):
        """Nested Serializable objects are preserved correctly through serialization."""
        agent_response = MockAgentResponse(
            is_complaint=True,
            summary="Test summary",
            complaint=complaint,
            complaint_response=complaint_response
        )

        json_str = agent_response.to_json()
        restored = MockAgentResponse.from_json(json_str)

        assert restored.complaint is not None
        assert restored.complaint.transcript == complaint.transcript
        assert restored.complaint.timestamp == complaint.timestamp
        assert restored.complaint.matched_criteria == complaint.matched_criteria

        assert restored.complaint_response is not None
        assert restored.complaint_response.severity == complaint_response.severity
        assert restored.complaint_response.category == complaint_response.category
        assert restored.complaint_response.actions_taken == complaint_response.actions_taken
        assert restored.complaint_response.next_steps == complaint_response.next_steps
