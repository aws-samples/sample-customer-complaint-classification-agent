"""Property-based tests for session state persistence.

Feature: streamlit-web-interface, Property 6: Session State Persistence Round-Trip
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from hypothesis import given, settings, strategies as st

from src.complaints_agent.ui.models import ChatMessage
from src.complaints_agent.ui.session import (
    initialize_session_state,
    get_messages,
    add_message,
    clear_chat_history,
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


chat_message_strategy = st.builds(
    ChatMessage,
    role=st.sampled_from(["user", "assistant"]),
    content=st.text(min_size=1, max_size=500),
    timestamp=st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ),
    agent_response=st.none()
)


class TestSessionStatePersistenceRoundTrip:
    """
    Feature: streamlit-web-interface, Property 6: Session State Persistence Round-Trip
    
    *For any* list of ChatMessage objects stored in session state, after a simulated
    page rerun, retrieving the messages from session state SHALL return an equivalent
    list with the same length and identical message contents.
    
    **Validates: Requirements 7.1, 7.2**
    """

    @settings(max_examples=10)
    @given(
        messages=st.lists(chat_message_strategy, min_size=0, max_size=20)
    )
    def test_messages_persist_across_simulated_reruns(self, messages: list[ChatMessage]):
        """Messages stored in session state persist across simulated page reruns."""
        mock_state = create_mock_session_state()
        
        with patch("src.complaints_agent.ui.session.st") as mock_st:
            mock_st.session_state = mock_state
            
            initialize_session_state()
            
            for msg in messages:
                mock_state.messages.append(msg)
            
            retrieved = get_messages()
            
            assert len(retrieved) == len(messages)
            for original, retrieved_msg in zip(messages, retrieved):
                assert retrieved_msg.role == original.role
                assert retrieved_msg.content == original.content
                assert retrieved_msg.timestamp == original.timestamp
                assert retrieved_msg.agent_response == original.agent_response

    @settings(max_examples=10)
    @given(
        messages=st.lists(chat_message_strategy, min_size=1, max_size=20)
    )
    def test_messages_maintain_order_after_retrieval(self, messages: list[ChatMessage]):
        """Messages maintain their order after retrieval from session state."""
        mock_state = create_mock_session_state()
        
        with patch("src.complaints_agent.ui.session.st") as mock_st:
            mock_st.session_state = mock_state
            
            initialize_session_state()
            mock_state.messages = messages.copy()
            
            retrieved = get_messages()
            
            assert retrieved == messages

    @settings(max_examples=10)
    @given(
        role=st.sampled_from(["user", "assistant"]),
        content=st.text(min_size=1, max_size=500)
    )
    def test_add_message_persists_to_session_state(self, role: str, content: str):
        """Adding a message persists it to session state."""
        mock_state = create_mock_session_state()
        
        with patch("src.complaints_agent.ui.session.st") as mock_st:
            mock_st.session_state = mock_state
            
            initialize_session_state()
            initial_count = len(mock_state.messages)
            
            added = add_message(role=role, content=content)
            
            assert len(mock_state.messages) == initial_count + 1
            assert mock_state.messages[-1] == added
            assert added.role == role
            assert added.content == content

    @settings(max_examples=10)
    @given(
        messages=st.lists(chat_message_strategy, min_size=1, max_size=20)
    )
    def test_clear_history_removes_all_messages(self, messages: list[ChatMessage]):
        """Clearing history removes all messages from session state."""
        mock_state = create_mock_session_state()
        
        with patch("src.complaints_agent.ui.session.st") as mock_st:
            mock_st.session_state = mock_state
            
            initialize_session_state()
            mock_state.messages = messages.copy()
            
            clear_chat_history()
            
            assert len(mock_state.messages) == 0

    def test_initialize_creates_empty_messages_list(self):
        """Initialize creates an empty messages list if none exists."""
        mock_state = create_mock_session_state()
        
        with patch("src.complaints_agent.ui.session.st") as mock_st:
            mock_st.session_state = mock_state
            
            initialize_session_state()
            
            assert "messages" in mock_state
            assert mock_state.messages == []

    def test_initialize_preserves_existing_messages(self):
        """Initialize preserves existing messages if already present."""
        mock_state = create_mock_session_state()
        existing_messages = [
            ChatMessage(role="user", content="test", timestamp=datetime.now())
        ]
        mock_state["messages"] = existing_messages
        
        with patch("src.complaints_agent.ui.session.st") as mock_st:
            mock_st.session_state = mock_state
            
            initialize_session_state()
            
            assert mock_state.messages == existing_messages
