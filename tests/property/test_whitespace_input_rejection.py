"""Property-based tests for whitespace input rejection.

Feature: streamlit-web-interface, Property 3: Whitespace Input Rejection
"""

from hypothesis import given, settings, strategies as st

from src.complaints_agent.ui.validation import is_valid_transcript


class TestWhitespaceInputRejection:
    """
    Feature: streamlit-web-interface, Property 3: Whitespace Input Rejection
    
    *For any* string composed entirely of whitespace characters (including empty
    string), submitting it SHALL NOT change the session state messages list length.
    
    **Validates: Requirements 2.3**
    """

    @settings(max_examples=10)
    @given(
        whitespace=st.text(
            alphabet=" \t\n\r\f\v",
            min_size=0,
            max_size=100
        )
    )
    def test_whitespace_only_strings_are_invalid(self, whitespace: str):
        """Whitespace-only strings are rejected as invalid transcripts."""
        result = is_valid_transcript(whitespace)
        assert result is False

    def test_empty_string_is_invalid(self):
        """Empty string is rejected as invalid transcript."""
        assert is_valid_transcript("") is False

    def test_single_space_is_invalid(self):
        """Single space is rejected as invalid transcript."""
        assert is_valid_transcript(" ") is False

    def test_multiple_spaces_is_invalid(self):
        """Multiple spaces are rejected as invalid transcript."""
        assert is_valid_transcript("     ") is False

    def test_tab_is_invalid(self):
        """Tab character is rejected as invalid transcript."""
        assert is_valid_transcript("\t") is False

    def test_newline_is_invalid(self):
        """Newline character is rejected as invalid transcript."""
        assert is_valid_transcript("\n") is False

    def test_mixed_whitespace_is_invalid(self):
        """Mixed whitespace characters are rejected as invalid transcript."""
        assert is_valid_transcript(" \t\n\r ") is False
