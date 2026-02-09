"""Property-based tests for the Supervisor Agent.

These tests verify that the Supervisor Agent correctly classifies transcripts
and routes complaints to the Complaints Agent tool.
"""

import json

from hypothesis import given, settings, strategies as st

from complaints_agent.agents.supervisor_agent import SupervisorAgent
from complaints_agent.models.complaint_criteria import ComplaintCriteria
from complaints_agent.models.agent_response import AgentResponse


# Default complaint criteria for testing
DEFAULT_KEYWORDS = [
    "complaint", "frustrated", "angry", "disappointed", "terrible",
    "broken", "defective", "refund", "unacceptable", "worst"
]

DEFAULT_SENTIMENT_INDICATORS = [
    "very unhappy", "extremely disappointed", "never again",
    "demand a refund", "speak to manager", "file a complaint"
]

DEFAULT_SEVERITY_THRESHOLDS = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4
}


def create_test_criteria() -> ComplaintCriteria:
    """Create a ComplaintCriteria instance for testing."""
    return ComplaintCriteria(
        keywords=DEFAULT_KEYWORDS,
        sentiment_indicators=DEFAULT_SENTIMENT_INDICATORS,
        severity_thresholds=DEFAULT_SEVERITY_THRESHOLDS
    )


# Strategy for generating arbitrary transcripts
transcript_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S', 'Z')),
    min_size=10,
    max_size=300
).filter(lambda x: x.strip())


class TestSupervisorAgentClassification:
    """Property-based tests for Supervisor Agent classification."""

    @settings(max_examples=5, deadline=180000)  # 3 minute deadline for LLM calls
    @given(transcript=transcript_strategy)
    def test_classification_produces_result_for_any_transcript(self, transcript: str):
        """
        **Feature: complaints-agent, Property 1: Classification produces result for any transcript**
        
        *For any* transcript string and valid complaint criteria, the Supervisor Agent 
        SHALL produce a classification result that is either "complaint" or "non_complaint".
        
        **Validates: Requirements 1.1**
        """
        criteria = create_test_criteria()
        agent = SupervisorAgent(criteria)
        
        # Process the transcript
        response = agent.process_transcript(transcript)
        
        # Verify response is an AgentResponse
        assert isinstance(response, AgentResponse), \
            f"Expected AgentResponse, got {type(response)}"
        
        # Verify is_complaint is a boolean (represents complaint or non_complaint)
        assert isinstance(response.is_complaint, bool), \
            f"is_complaint should be boolean, got {type(response.is_complaint)}"
        
        # Verify summary is present
        assert response.summary is not None, "Response should have a summary"
        assert isinstance(response.summary, str), "Summary should be a string"
        
        # Verify the response structure is consistent
        if response.is_complaint:
            # Complaint should have complaint object
            assert response.complaint is not None, \
                "Complaint classification should include complaint object"
            assert response.complaint.classification_result == "complaint", \
                "Complaint object should have classification_result='complaint'"
        else:
            # Non-complaint should not have complaint object
            assert response.complaint is None, \
                "Non-complaint classification should not have complaint object"
            assert response.complaint_response is None, \
                "Non-complaint classification should not have complaint_response"

    @settings(max_examples=5, deadline=180000)  # 3 minute deadline for LLM calls
    @given(
        keyword=st.sampled_from(DEFAULT_KEYWORDS),
        prefix=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "),
            min_size=10,
            max_size=50
        ).filter(lambda x: x.strip() and not any(kw in x.lower() for kw in DEFAULT_KEYWORDS)),
        suffix=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "),
            min_size=10,
            max_size=50
        ).filter(lambda x: x.strip() and not any(kw in x.lower() for kw in DEFAULT_KEYWORDS))
    )
    def test_complaint_indicators_lead_to_complaint_classification(
        self, keyword: str, prefix: str, suffix: str
    ):
        """
        **Feature: complaints-agent, Property 2: Complaint indicators lead to complaint classification**
        
        *For any* transcript containing at least one keyword from the complaint criteria 
        keywords list, the Supervisor Agent SHALL classify the interaction as a complaint.
        
        **Validates: Requirements 1.2, 2.2**
        """
        # Construct a transcript that contains the complaint keyword
        transcript = f"{prefix} I am {keyword} about this situation. {suffix}"
        
        criteria = create_test_criteria()
        agent = SupervisorAgent(criteria)
        
        # Process the transcript
        response = agent.process_transcript(transcript)
        
        # Verify response is an AgentResponse
        assert isinstance(response, AgentResponse), \
            f"Expected AgentResponse, got {type(response)}"
        
        # Verify the transcript with complaint keyword is classified as complaint
        assert response.is_complaint is True, \
            f"Transcript containing keyword '{keyword}' should be classified as complaint. " \
            f"Transcript: '{transcript}', Summary: '{response.summary}'"
        
        # Verify complaint object is present
        assert response.complaint is not None, \
            "Complaint classification should include complaint object"
        
        # Verify classification result
        assert response.complaint.classification_result == "complaint", \
            "Complaint object should have classification_result='complaint'"

    @settings(max_examples=5, deadline=180000)  # 3 minute deadline for LLM calls
    @given(
        words=st.lists(
            st.text(
                alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz"),
                min_size=3,
                max_size=8
            ),
            min_size=5,
            max_size=15
        )
    )
    def test_clean_transcripts_lead_to_non_complaint_classification(self, words: list[str]):
        """
        **Feature: complaints-agent, Property 3: Clean transcripts lead to non-complaint classification**
        
        *For any* transcript that contains no keywords from the complaint criteria 
        and no negative sentiment indicators, the Supervisor Agent SHALL classify 
        the interaction as a non-complaint.
        
        **Validates: Requirements 1.3**
        """
        # Filter out any words that might accidentally match complaint keywords or sentiment indicators
        all_complaint_terms = [kw.lower() for kw in DEFAULT_KEYWORDS + DEFAULT_SENTIMENT_INDICATORS]
        
        # Build a clean transcript from words that don't contain complaint terms
        clean_words = []
        for word in words:
            word_lower = word.lower()
            # Check if this word is or contains any complaint term
            is_clean = True
            for term in all_complaint_terms:
                if term in word_lower or word_lower in term:
                    is_clean = False
                    break
            if is_clean and word.strip():
                clean_words.append(word)
        
        # Ensure we have enough words for a valid transcript
        if len(clean_words) < 3:
            clean_words = ["hello", "thank", "you", "for", "calling", "today"]
        
        # Construct a neutral transcript
        transcript = f"Customer: {' '.join(clean_words[:len(clean_words)//2])}. Agent: {' '.join(clean_words[len(clean_words)//2:])}."
        
        # Double-check the transcript doesn't contain any complaint indicators
        transcript_lower = transcript.lower()
        for term in all_complaint_terms:
            if term in transcript_lower:
                # Skip this test case if we accidentally included a complaint term
                return
        
        criteria = create_test_criteria()
        agent = SupervisorAgent(criteria)
        
        # Process the transcript
        response = agent.process_transcript(transcript)
        
        # Verify response is an AgentResponse
        assert isinstance(response, AgentResponse), \
            f"Expected AgentResponse, got {type(response)}"
        
        # Verify the clean transcript is classified as non-complaint
        assert response.is_complaint is False, \
            f"Clean transcript without complaint indicators should be classified as non-complaint. " \
            f"Transcript: '{transcript}', Summary: '{response.summary}'"
        
        # Verify complaint object is not present
        assert response.complaint is None, \
            "Non-complaint classification should not have complaint object"
        
        # Verify complaint_response is not present
        assert response.complaint_response is None, \
            "Non-complaint classification should not have complaint_response"

    @settings(max_examples=5, deadline=180000)
    @given(
        words=st.lists(
            st.text(
                alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz"),
                min_size=3,
                max_size=8
            ),
            min_size=5,
            max_size=15
        )
    )
    def test_non_complaint_returns_appropriate_response(self, words: list[str]):
        """
        **Feature: complaints-agent, Property 8: Non-complaint returns appropriate response**
        
        *For any* transcript classified as non-complaint, the Supervisor Agent SHALL 
        return an AgentResponse with is_complaint=False and complaint_response=None.
        
        **Validates: Requirements 4.4**
        """
        all_complaint_terms = [kw.lower() for kw in DEFAULT_KEYWORDS + DEFAULT_SENTIMENT_INDICATORS]
        
        clean_words = []
        for word in words:
            word_lower = word.lower()
            is_clean = True
            for term in all_complaint_terms:
                if term in word_lower or word_lower in term:
                    is_clean = False
                    break
            if is_clean and word.strip():
                clean_words.append(word)
        
        if len(clean_words) < 3:
            clean_words = ["hello", "thank", "you", "for", "calling", "today"]
        
        transcript = f"Customer: {' '.join(clean_words[:len(clean_words)//2])}. Agent: {' '.join(clean_words[len(clean_words)//2:])}."
        
        transcript_lower = transcript.lower()
        for term in all_complaint_terms:
            if term in transcript_lower:
                return
        
        criteria = create_test_criteria()
        agent = SupervisorAgent(criteria)
        
        response = agent.process_transcript(transcript)
        
        assert isinstance(response, AgentResponse), \
            f"Expected AgentResponse, got {type(response)}"
        
        assert response.is_complaint is False, \
            f"Clean transcript should be classified as non-complaint. " \
            f"Transcript: '{transcript}', Summary: '{response.summary}'"
        
        assert response.complaint_response is None, \
            f"Non-complaint response should have complaint_response=None. " \
            f"Got: {response.complaint_response}"
        
        assert response.complaint is None, \
            f"Non-complaint response should have complaint=None. " \
            f"Got: {response.complaint}"
        
        assert response.summary is not None, \
            "Non-complaint response should have a summary"
        assert isinstance(response.summary, str), \
            f"Summary should be a string, got {type(response.summary)}"
        assert len(response.summary) > 0, \
            "Summary should not be empty"

    @settings(max_examples=5, deadline=180000)
    @given(
        keyword=st.sampled_from(DEFAULT_KEYWORDS),
        context=st.text(
            alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "),
            min_size=20,
            max_size=100
        ).filter(lambda x: x.strip() and not any(kw in x.lower() for kw in DEFAULT_KEYWORDS))
    )
    def test_supervisor_agent_captures_complete_complaints_agent_response(
        self, keyword: str, context: str
    ):
        """
        **Feature: complaints-agent, Property 7: Supervisor Agent captures complete Complaints Agent response**
        
        *For any* complaint that is processed by the Complaints Agent, the Supervisor Agent 
        final output SHALL contain the complete actions_taken and next_steps from the 
        Complaints Agent response.
        
        **Validates: Requirements 4.1, 4.2, 4.3**
        """
        transcript = f"Customer: I am very {keyword} with your service. {context}. This is unacceptable."
        
        criteria = create_test_criteria()
        agent = SupervisorAgent(criteria)
        
        response = agent.process_transcript(transcript)
        
        assert isinstance(response, AgentResponse), \
            f"Expected AgentResponse, got {type(response)}"
        
        assert response.is_complaint is True, \
            f"Transcript with keyword '{keyword}' should be classified as complaint. " \
            f"Transcript: '{transcript}', Summary: '{response.summary}'"
        
        assert response.complaint_response is not None, \
            f"Complaint response should be captured from Complaints Agent. " \
            f"Transcript: '{transcript}', Summary: '{response.summary}'"
        
        assert response.complaint_response.actions_taken is not None, \
            "actions_taken should be present in complaint_response"
        assert isinstance(response.complaint_response.actions_taken, list), \
            f"actions_taken should be a list, got {type(response.complaint_response.actions_taken)}"
        assert len(response.complaint_response.actions_taken) > 0, \
            "actions_taken should contain at least one action"
        
        assert response.complaint_response.next_steps is not None, \
            "next_steps should be present in complaint_response"
        assert isinstance(response.complaint_response.next_steps, list), \
            f"next_steps should be a list, got {type(response.complaint_response.next_steps)}"
        assert len(response.complaint_response.next_steps) > 0, \
            "next_steps should contain at least one step"
        
        assert response.complaint_response.severity is not None, \
            "severity should be present in complaint_response"
        assert response.complaint_response.severity in ["low", "medium", "high", "critical"], \
            f"severity should be one of low/medium/high/critical, got {response.complaint_response.severity}"
        
        assert response.complaint_response.category is not None, \
            "category should be present in complaint_response"
        assert isinstance(response.complaint_response.category, str), \
            f"category should be a string, got {type(response.complaint_response.category)}"
        assert len(response.complaint_response.category) > 0, \
            "category should not be empty"
