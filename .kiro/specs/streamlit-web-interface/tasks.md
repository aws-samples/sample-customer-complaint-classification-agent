# Implementation Plan: Streamlit Web Interface

## Overview

This implementation plan creates a Streamlit web interface for the complaints agent system. The approach builds incrementally: first the streaming adapter layer, then the UI components, and finally integration with session state management.

## Tasks

- [x] 1. Add Streamlit dependency and create project structure
  - Add `streamlit>=1.28.0` to requirements.txt
  - Create `src/complaints_agent/ui/` directory
  - Create `src/complaints_agent/ui/__init__.py`
  - _Requirements: 1.1, 2.1_

- [x] 2. Implement streaming callback handler
  - [x] 2.1 Create StreamingCallbackHandler class in `src/complaints_agent/ui/streaming.py`
    - Implement `__init__` with on_token callback parameter
    - Implement `__call__` method to process streaming events
    - Handle data, complete, and current_tool_use events
    - _Requirements: 3.1, 3.2_
  
  - [x] 2.2 Write property test for streaming callback token delivery
    - **Property 4: Streaming Callback Token Delivery**
    - **Validates: Requirements 3.1**

- [x] 3. Implement StreamingSupervisorAgent wrapper
  - [x] 3.1 Create StreamingSupervisorAgent class in `src/complaints_agent/ui/streaming.py`
    - Wrap existing SupervisorAgent with streaming capability
    - Create agent with custom callback_handler
    - Implement process_transcript_streaming method
    - _Requirements: 3.1, 4.1, 4.2_
  
  - [x] 3.2 Write property test for complaint response completeness
    - **Property 5: Complaint Response Completeness**
    - **Validates: Requirements 3.3, 5.1, 5.2, 6.1, 6.2, 6.3, 6.4**

- [x] 4. Checkpoint - Verify streaming layer
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement ChatMessage model and session state management
  - [x] 5.1 Create ChatMessage dataclass in `src/complaints_agent/ui/models.py`
    - Define role, content, timestamp, and optional agent_response fields
    - _Requirements: 1.3, 7.1_
  
  - [x] 5.2 Implement session state functions in `src/complaints_agent/ui/session.py`
    - Create initialize_session_state function
    - Create get_messages and add_message functions
    - Create clear_chat_history function
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [x] 5.3 Write property test for session state persistence
    - **Property 6: Session State Persistence Round-Trip**
    - **Validates: Requirements 7.1, 7.2**
  
  - [x] 5.4 Write property test for message chronological ordering
    - **Property 1: Message Chronological Ordering**
    - **Validates: Requirements 1.3**

- [x] 6. Implement input validation
  - [x] 6.1 Create input validation function in `src/complaints_agent/ui/validation.py`
    - Implement is_valid_transcript function
    - Return False for empty or whitespace-only strings
    - _Requirements: 2.3_
  
  - [x] 6.2 Write property test for whitespace input rejection
    - **Property 3: Whitespace Input Rejection**
    - **Validates: Requirements 2.3**
  
  - [x] 6.3 Write property test for non-empty transcript acceptance
    - **Property 2: Non-Empty Transcript Adds Message**
    - **Validates: Requirements 2.2**

- [x] 7. Checkpoint - Verify core components
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement Streamlit UI components
  - [x] 8.1 Create main app file `src/complaints_agent/ui/app.py`
    - Set page config with title and layout
    - Display app title and description
    - Initialize session state on load
    - _Requirements: 1.1, 1.2_
  
  - [x] 8.2 Implement chat history display function
    - Iterate through session state messages
    - Use st.chat_message for user and assistant roles
    - Display messages in chronological order
    - _Requirements: 1.3, 1.4_
  
  - [x] 8.3 Implement complaint details display function
    - Create expandable section for complaint details
    - Display severity with color-coded styling
    - Display category, actions taken, and next steps
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [x] 8.4 Implement agent response display function
    - Display classification result (complaint vs non-complaint)
    - Show matched criteria for complaints
    - Show summary for non-complaints
    - Call complaint details display for complaints
    - _Requirements: 5.1, 5.2, 5.3_

- [x] 9. Implement user input handling with streaming
  - [x] 9.1 Create chat input component
    - Use st.chat_input for transcript entry
    - Validate input before processing
    - _Requirements: 2.1, 2.3_
  
  - [x] 9.2 Implement handle_user_input function
    - Add user message to chat history
    - Initialize StreamingSupervisorAgent with loaded criteria
    - Create streaming placeholder with st.empty()
    - Process transcript with streaming callback
    - Update placeholder with streamed tokens
    - Add final agent response to chat history
    - _Requirements: 2.2, 2.4, 3.1, 3.2, 3.3, 4.1, 4.2, 4.4_
  
  - [x] 9.3 Implement error handling
    - Wrap agent invocation in try-except
    - Display error messages with st.error
    - Handle configuration loading errors
    - _Requirements: 4.3_

- [x] 10. Implement clear history functionality
  - Add sidebar with clear history button
  - Call clear_chat_history on button click
  - Rerun app to refresh display
  - _Requirements: 7.3_

- [x] 11. Create app entry point
  - Create `streamlit_app.py` in project root
  - Import and run the main app function
  - Add run instructions to README or comments
  - _Requirements: 1.1_

- [x] 12. Final checkpoint - End-to-end verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks including tests are required for comprehensive coverage
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The streaming implementation uses Strands Agent callback handlers
- Streamlit session state is used for persistence within a session
