"""Property-based tests for non-empty transcript acceptance.

Feature: streamlit-web-interface, Property 2: Non-Empty Transcript Adds Message
"""

from datetime import datetime
from unittest.mock import patch

from hypothesis import given, settings, strategies as st, assume

from src.complaints_agent.ui.validation import is_valid_transcript
from src.complaints_agent.ui.session import (
    initialize_session_state,
    get_messages,
    add_message,
)


def create_mock_session_state():
    """Create a mock session state that behaves like Streamlit's."""
    class MockSessionState(dict):
        def __contains__(self, key):
            return dict.__contains__(self, key)
        
        def __getattr__(self, key):
            if key in self:
                return self[key]
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")
        
        def __setattr__(self, key, value):
            self[key] = value
    
    return MockSessionState()


non_whitespace_text = st.text(min_size=1, max_size=500).filter(
    lambda x: x.strip() != ""
)


class TestNonEmptyTranscriptAddsMessage:
    """
    Feature: streamlit-web-interface, Property 2: Non-Empty Transcript Adds Message
    
    *For any* non-empty, non-whitespace transcript string submitted by a user,
    the session state messages list length SHALL increase by exactly one, and
    the new message SHALL have role "user" and content equal to the submitted
    transcript.
    
    **Validates: Requirements 2.2**
    """

    @settings(max_examples=10)
    @given(transcript=non_whitespace_text)
    def test_valid_transcript_is_accepted(self, transcript: str):
        """Non-empty, non-whitespace transcripts are accepted as valid."""
        result = is_valid_transcript(transcript)
        assert result is True

    @settings(max_examples=10)
    @given(transcript=non_whitespace_text)
    def test_valid_transcript_adds_message_to_session(self, transcript: str):
        """Valid transcript adds exactly one message to session state."""
        mock_state = create_mock_session_state()
        
        with patch("src.complaints_agent.ui.session.st") as mock_st:
            mock_st.session_state = mock_state
            
            initialize_session_state()
            initial_count = len(get_messages())
            
            if is_valid_transcript(transcript):
                add_message(role="user", content=transcript)
            
            final_count = len(get_messages())
            assert final_count == initial_count + 1

    @settings(max_examples=10)
    @given(transcript=non_whitespace_text)
    def test_added_message_has_correct_role_and_content(self, transcript: str):
        """Added message has role 'user' and content equal to transcript."""
        mock_state = create_mock_session_state()
        
        with patch("src.complaints_agent.ui.session.st") as mock_st:
            mock_st.session_state = mock_state
            
            initialize_session_state()
            
            if is_valid_transcript(transcript):
                message = add_message(role="user", content=transcript)
                
                assert message.role == "user"
                assert message.content == transcript

    @settings(max_examples=10)
    @given(
        transcript=st.text(min_size=1, max_size=500).filter(
            lambda x: x.strip() != "" and not x.isspace()
        )
    )
    def test_transcript_with_leading_trailing_whitespace_is_valid(self, transcript: str):
        """Transcripts with leading/trailing whitespace but non-whitespace content are valid."""
        padded = f"  {transcript}  "
        result = is_valid_transcript(padded)
        assert result is True

    def test_single_character_is_valid(self):
        """Single non-whitespace character is valid."""
        assert is_valid_transcript("a") is True

    def test_text_with_embedded_whitespace_is_valid(self):
        """Text with embedded whitespace is valid."""
        assert is_valid_transcript("hello world") is True

    def test_unicode_text_is_valid(self):
        """Unicode text is valid."""
        assert is_valid_transcript("こんにちは") is True
