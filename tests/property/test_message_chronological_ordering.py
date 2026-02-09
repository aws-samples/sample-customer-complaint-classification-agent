"""Property-based tests for message chronological ordering.

Feature: streamlit-web-interface, Property 1: Message Chronological Ordering
"""

from datetime import datetime
from unittest.mock import patch

from hypothesis import given, settings, strategies as st

from src.complaints_agent.ui.models import ChatMessage


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


class TestMessageChronologicalOrdering:
    """
    Feature: streamlit-web-interface, Property 1: Message Chronological Ordering
    
    *For any* list of ChatMessage objects in session state, when displayed in the
    chat interface, the messages SHALL appear in chronological order based on their
    timestamp field.
    
    **Validates: Requirements 1.3**
    """

    @settings(max_examples=10)
    @given(
        messages=st.lists(chat_message_strategy, min_size=2, max_size=20)
    )
    def test_messages_sorted_by_timestamp_maintain_order(self, messages: list[ChatMessage]):
        """Messages sorted by timestamp maintain chronological order when retrieved."""
        sorted_messages = sorted(messages, key=lambda m: m.timestamp)
        
        mock_state = create_mock_session_state()
        mock_state["messages"] = sorted_messages
        
        with patch("src.complaints_agent.ui.session.st") as mock_st:
            mock_st.session_state = mock_state
            
            from src.complaints_agent.ui.session import get_messages
            retrieved = get_messages()
            
            for i in range(len(retrieved) - 1):
                assert retrieved[i].timestamp <= retrieved[i + 1].timestamp

    @settings(max_examples=10)
    @given(
        messages=st.lists(chat_message_strategy, min_size=1, max_size=20)
    )
    def test_chronologically_ordered_messages_display_in_order(self, messages: list[ChatMessage]):
        """Messages added in chronological order display in that same order."""
        sorted_messages = sorted(messages, key=lambda m: m.timestamp)
        
        mock_state = create_mock_session_state()
        mock_state["messages"] = []
        
        with patch("src.complaints_agent.ui.session.st") as mock_st:
            mock_st.session_state = mock_state
            
            for msg in sorted_messages:
                mock_state.messages.append(msg)
            
            from src.complaints_agent.ui.session import get_messages
            retrieved = get_messages()
            
            assert len(retrieved) == len(sorted_messages)
            for original, retrieved_msg in zip(sorted_messages, retrieved):
                assert retrieved_msg.timestamp == original.timestamp

    @settings(max_examples=10)
    @given(
        timestamps=st.lists(
            st.datetimes(
                min_value=datetime(2020, 1, 1),
                max_value=datetime(2030, 12, 31)
            ),
            min_size=2,
            max_size=20,
            unique=True
        )
    )
    def test_unique_timestamps_preserve_strict_ordering(self, timestamps: list[datetime]):
        """Messages with unique timestamps preserve strict chronological ordering."""
        messages = [
            ChatMessage(role="user", content=f"msg_{i}", timestamp=ts)
            for i, ts in enumerate(timestamps)
        ]
        sorted_messages = sorted(messages, key=lambda m: m.timestamp)
        
        mock_state = create_mock_session_state()
        mock_state["messages"] = sorted_messages
        
        with patch("src.complaints_agent.ui.session.st") as mock_st:
            mock_st.session_state = mock_state
            
            from src.complaints_agent.ui.session import get_messages
            retrieved = get_messages()
            
            for i in range(len(retrieved) - 1):
                assert retrieved[i].timestamp < retrieved[i + 1].timestamp

    def test_empty_message_list_returns_empty(self):
        """Empty message list returns empty list."""
        mock_state = create_mock_session_state()
        mock_state["messages"] = []
        
        with patch("src.complaints_agent.ui.session.st") as mock_st:
            mock_st.session_state = mock_state
            
            from src.complaints_agent.ui.session import get_messages
            retrieved = get_messages()
            
            assert retrieved == []

    def test_single_message_returns_single_message(self):
        """Single message returns that message."""
        msg = ChatMessage(role="user", content="test", timestamp=datetime.now())
        mock_state = create_mock_session_state()
        mock_state["messages"] = [msg]
        
        with patch("src.complaints_agent.ui.session.st") as mock_st:
            mock_st.session_state = mock_state
            
            from src.complaints_agent.ui.session import get_messages
            retrieved = get_messages()
            
            assert len(retrieved) == 1
            assert retrieved[0] == msg
