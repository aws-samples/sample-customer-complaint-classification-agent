"""Property-based tests for streaming callback token delivery.

Feature: streamlit-web-interface, Property 4: Streaming Callback Token Delivery
"""

from hypothesis import given, settings, strategies as st

from src.complaints_agent.ui.streaming import StreamingCallbackHandler


class TestStreamingCallbackTokenDelivery:
    """
    Feature: streamlit-web-interface, Property 4: Streaming Callback Token Delivery
    
    *For any* non-empty string data passed to the StreamingCallbackHandler,
    the on_token callback function SHALL be invoked with that exact data.
    
    **Validates: Requirements 3.1**
    """

    @settings(max_examples=10)
    @given(
        token=st.text(min_size=1, max_size=500)
    )
    def test_non_empty_data_invokes_callback(self, token: str):
        """Non-empty data events invoke the on_token callback with the data."""
        received_tokens = []
        
        def capture_token(t: str) -> None:
            received_tokens.append(t)
        
        handler = StreamingCallbackHandler(on_token=capture_token)
        handler(data=token)
        
        assert len(received_tokens) == 1
        assert received_tokens[0] == token

    @settings(max_examples=10)
    @given(
        tokens=st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=20)
    )
    def test_multiple_data_events_invoke_callback_for_each(self, tokens: list[str]):
        """Multiple data events invoke the callback for each token in order."""
        received_tokens = []
        
        def capture_token(t: str) -> None:
            received_tokens.append(t)
        
        handler = StreamingCallbackHandler(on_token=capture_token)
        
        for token in tokens:
            handler(data=token)
        
        assert received_tokens == tokens

    @settings(max_examples=10)
    @given(
        empty_or_none=st.one_of(
            st.just(""),
            st.just(None)
        )
    )
    def test_empty_or_none_data_does_not_invoke_callback(self, empty_or_none):
        """Empty string or None data does not invoke the callback."""
        received_tokens = []
        
        def capture_token(t: str) -> None:
            received_tokens.append(t)
        
        handler = StreamingCallbackHandler(on_token=capture_token)
        handler(data=empty_or_none)
        
        assert len(received_tokens) == 0

    @settings(max_examples=10)
    @given(
        tool_uses=st.lists(
            st.dictionaries(
                keys=st.text(min_size=1, max_size=20),
                values=st.text(min_size=1, max_size=50),
                min_size=1,
                max_size=3
            ),
            min_size=1,
            max_size=10
        )
    )
    def test_tool_use_tracking_counts_unique_tools(self, tool_uses: list[dict]):
        """Handler tracks unique tool uses correctly."""
        handler = StreamingCallbackHandler(on_token=lambda t: None)
        
        for tool_use in tool_uses:
            handler(current_tool_use=tool_use)
        
        unique_tools = []
        prev = None
        for tool in tool_uses:
            if tool != prev:
                unique_tools.append(tool)
                prev = tool
        
        assert handler.tool_count == len(unique_tools)

    def test_complete_event_does_not_raise(self):
        """Complete event is handled without raising exceptions."""
        handler = StreamingCallbackHandler(on_token=lambda t: None)
        handler(complete=True)

    @settings(max_examples=10)
    @given(
        token=st.text(min_size=1, max_size=100),
        tool_use=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.text(min_size=1, max_size=50),
            min_size=1,
            max_size=3
        )
    )
    def test_combined_events_process_correctly(self, token: str, tool_use: dict):
        """Combined data and tool_use events process correctly."""
        received_tokens = []
        
        def capture_token(t: str) -> None:
            received_tokens.append(t)
        
        handler = StreamingCallbackHandler(on_token=capture_token)
        handler(data=token, current_tool_use=tool_use, complete=False)
        
        assert len(received_tokens) == 1
        assert received_tokens[0] == token
        assert handler.tool_count == 1
        assert handler.previous_tool_use == tool_use
