"""Input validation for the Streamlit UI."""


def is_valid_transcript(transcript: str) -> bool:
    """Validate that a transcript is non-empty and contains non-whitespace content.
    
    Args:
        transcript: The transcript string to validate
        
    Returns:
        True if the transcript is valid (non-empty and not whitespace-only),
        False otherwise
    """
    if not isinstance(transcript, str):
        return False
    return bool(transcript.strip())
