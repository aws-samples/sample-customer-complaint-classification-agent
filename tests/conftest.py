"""Shared Hypothesis strategies for property-based testing."""

from datetime import datetime
from typing import Dict, List

from hypothesis import strategies as st

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

reasoning_strategy = st.text(
    min_size=1,
    max_size=200
).filter(lambda x: x.strip()).map(lambda s: s.replace('"', '\\"').replace('\\', '\\\\'))


@st.composite
def complaint_response_strategy(draw):
    """Generate ComplaintResponse-like dictionaries."""
    from src.complaints_agent.models.complaint_response import ComplaintResponse
    return ComplaintResponse(
        severity=draw(severity_strategy),
        category=draw(category_strategy),
        actions_taken=draw(actions_strategy),
        next_steps=draw(next_steps_strategy)
    )


@st.composite
def complaint_strategy(draw):
    """Generate Complaint-like dictionaries."""
    from src.complaints_agent.models.complaint import Complaint
    return Complaint(
        transcript=draw(transcript_strategy),
        classification_result=draw(classification_result_strategy),
        timestamp=draw(datetime_strategy),
        matched_criteria=draw(matched_criteria_strategy)
    )


@st.composite
def complaint_criteria_strategy(draw):
    """Generate ComplaintCriteria-like dictionaries."""
    from src.complaints_agent.models.complaint_criteria import ComplaintCriteria
    return ComplaintCriteria(
        keywords=draw(keywords_strategy),
        sentiment_indicators=draw(sentiment_indicators_strategy),
        severity_thresholds=draw(severity_thresholds_strategy)
    )


@st.composite
def agent_response_strategy(draw):
    """Generate AgentResponse-like dictionaries."""
    from src.complaints_agent.models.agent_response import AgentResponse
    is_complaint = draw(st.booleans())
    return AgentResponse(
        is_complaint=is_complaint,
        summary=draw(summary_strategy),
        complaint=draw(complaint_strategy()) if is_complaint else None,
        complaint_response=draw(complaint_response_strategy()) if is_complaint else None
    )


@st.composite
def classification_json_strategy(draw):
    """Generate valid classification JSON objects."""
    return {
        "classification": draw(st.sampled_from(["complaint", "non_complaint"])),
        "reasoning": draw(reasoning_strategy),
        "matched_criteria": draw(matched_criteria_strategy)
    }


@st.composite
def tool_input_json_strategy(draw):
    """Generate tool input JSON objects (transcript + classification_result)."""
    return {
        "transcript": draw(transcript_strategy),
        "classification_result": draw(classification_result_strategy)
    }


@st.composite
def complaint_response_json_strategy(draw):
    """Generate complaint response JSON objects."""
    return {
        "severity": draw(severity_strategy),
        "category": draw(category_strategy),
        "actions_taken": draw(actions_strategy),
        "next_steps": draw(next_steps_strategy)
    }
