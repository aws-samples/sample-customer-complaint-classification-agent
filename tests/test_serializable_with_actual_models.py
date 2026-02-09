import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional

from src.complaints_agent.models.base import Serializable


@dataclass
class MockComplaint(Serializable):
    transcript: str
    classification_result: str
    timestamp: datetime
    matched_criteria: List[str] = field(default_factory=list)


@dataclass
class MockComplaintResponse(Serializable):
    severity: str
    category: str
    actions_taken: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)


@dataclass
class MockComplaintCriteria(Serializable):
    keywords: List[str] = field(default_factory=list)
    sentiment_indicators: List[str] = field(default_factory=list)
    severity_thresholds: Dict[str, int] = field(default_factory=dict)


@dataclass
class MockAgentResponse(Serializable):
    is_complaint: bool
    summary: str
    complaint: Optional[MockComplaint] = None
    complaint_response: Optional[MockComplaintResponse] = None


class TestComplaintModelSerialization:
    def test_complaint_round_trip(self):
        original = MockComplaint(
            transcript="Customer called about billing issue",
            classification_result="complaint",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            matched_criteria=["billing", "frustrated"]
        )
        json_str = original.to_json()
        restored = MockComplaint.from_json(json_str)

        assert restored.transcript == original.transcript
        assert restored.classification_result == original.classification_result
        assert restored.timestamp == original.timestamp
        assert restored.matched_criteria == original.matched_criteria


class TestComplaintResponseModelSerialization:
    def test_complaint_response_round_trip(self):
        original = MockComplaintResponse(
            severity="high",
            category="billing",
            actions_taken=["Reviewed account", "Applied credit"],
            next_steps=["Follow up in 24 hours"]
        )
        json_str = original.to_json()
        restored = MockComplaintResponse.from_json(json_str)

        assert restored.severity == original.severity
        assert restored.category == original.category
        assert restored.actions_taken == original.actions_taken
        assert restored.next_steps == original.next_steps


class TestComplaintCriteriaModelSerialization:
    def test_complaint_criteria_round_trip(self):
        original = MockComplaintCriteria(
            keywords=["complaint", "issue", "problem"],
            sentiment_indicators=["frustrated", "angry", "disappointed"],
            severity_thresholds={"low": 1, "medium": 3, "high": 5}
        )
        json_str = original.to_json()
        restored = MockComplaintCriteria.from_json(json_str)

        assert restored.keywords == original.keywords
        assert restored.sentiment_indicators == original.sentiment_indicators
        assert restored.severity_thresholds == original.severity_thresholds


class TestAgentResponseModelSerialization:
    def test_agent_response_with_nested_models(self):
        complaint = MockComplaint(
            transcript="Customer called about billing issue",
            classification_result="complaint",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            matched_criteria=["billing"]
        )
        complaint_response = MockComplaintResponse(
            severity="high",
            category="billing",
            actions_taken=["Reviewed account"],
            next_steps=["Follow up"]
        )
        original = MockAgentResponse(
            is_complaint=True,
            summary="Billing complaint processed",
            complaint=complaint,
            complaint_response=complaint_response
        )
        json_str = original.to_json()
        restored = MockAgentResponse.from_json(json_str)

        assert restored.is_complaint == original.is_complaint
        assert restored.summary == original.summary
        assert restored.complaint is not None
        assert restored.complaint.transcript == complaint.transcript
        assert restored.complaint.timestamp == complaint.timestamp
        assert restored.complaint_response is not None
        assert restored.complaint_response.severity == complaint_response.severity
        assert restored.complaint_response.actions_taken == complaint_response.actions_taken

    def test_agent_response_without_nested_models(self):
        original = MockAgentResponse(
            is_complaint=False,
            summary="Not a complaint",
            complaint=None,
            complaint_response=None
        )
        json_str = original.to_json()
        restored = MockAgentResponse.from_json(json_str)

        assert restored.is_complaint == original.is_complaint
        assert restored.summary == original.summary
        assert restored.complaint is None
        assert restored.complaint_response is None

    def test_json_structure_matches_original_implementation(self):
        complaint = MockComplaint(
            transcript="Test",
            classification_result="complaint",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            matched_criteria=[]
        )
        complaint_response = MockComplaintResponse(
            severity="low",
            category="test",
            actions_taken=[],
            next_steps=[]
        )
        model = MockAgentResponse(
            is_complaint=True,
            summary="Test summary",
            complaint=complaint,
            complaint_response=complaint_response
        )
        json_str = model.to_json()
        data = json.loads(json_str)

        assert "is_complaint" in data
        assert "summary" in data
        assert "complaint" in data
        assert "complaint_response" in data
        assert isinstance(data["complaint"], dict)
        assert data["complaint"]["timestamp"] == "2024-01-15T10:30:00"
