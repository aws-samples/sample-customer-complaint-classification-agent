import streamlit as st

col1, col2 = st.columns(2)

## Model Settings
with col1:
    st.markdown("### 🤖 Model Settings")
    st.session_state.model_id = st.selectbox(
        label="Model",
        placeholder="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        options=st.session_state.models,
        index=None
    )

    st.slider(
        label="Model Temperature",
        min_value=0.0,
        max_value=1.0,
        step=0.1,
        value=st.session_state.model_temperature
    )

    st.slider(
        label="Top P",
        min_value=0.0,
        max_value=1.0,
        step=0.1,
        value=st.session_state.top_p
    )


## Prompt Settings
default_system_prompt = ""

if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = default_system_prompt
