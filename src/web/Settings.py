import streamlit as st
from utils.helpers import *

bedrock_runtime_client, bedrock_service_client = bedrock_init()

col1, col2 = st.columns(2)

## Model Settings
if "models" not in st.session_state:
    st.session_state.models = []

if "model_id" not in st.session_state:
    st.session_state.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

if "model_temperature" not in st.session_state:
    st.session_state.model_temperature = 0.0

if "top_p" not in st.session_state:
    st.session_state.top_p = 0.0

st.session_state.models = list_foundation_models(bedrock_service_client)

with col1:
    st.markdown("### 🤖 Model Settings")
    st.session_state.model_id = st.selectbox(
        label="Model",
        placeholder="anthropic.claude-3-5-sonnet-20241022-v2:0",
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
