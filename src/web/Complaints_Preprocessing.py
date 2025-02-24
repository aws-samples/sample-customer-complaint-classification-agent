import streamlit as st
import json
from io import StringIO
from utils.helpers import *

# Initialize the Bedrock client
bedrock_runtime_client, bedrock_service_client = bedrock_init()

# Initialize Model Settings
if "model_id" not in st.session_state:
    st.session_state.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

if "model_temperature" not in st.session_state:
    st.session_state.model_temperature = 0.0

if "top_p" not in st.session_state:
    st.session_state.top_p = 0.0


def analyze_complaint(complaint_text):
    """Use Amazon Bedrock (Claude model) to analyze a complaint"""
    prompt = f"""Analyze this consumer complaint and provide:
    1. Main issue category
    2. Severity level (Low/Medium/High)
    3. Key points summary
    4. Recommended next steps

    Complaint: {complaint_text}"""

    # Create the request body for Bedrock
    body = json.dumps({
        "modelId": "anthropic.claude-v2",  # or your preferred model
        "contentType": "application/json",
        "accept": "*/*",
        "body": {
            "prompt": "\n\nHuman: " + prompt + "\n\nAssistant:",
            "max_tokens_to_sample": 1000,
            "temperature": st.session_state.model_temperature,
            "top_p": st.session_state.top_p
        }
    })

    try:
        # Call Bedrock
        response = bedrock.invoke_model(
            body=body,
            modelId="anthropic.claude-v2",  # or your preferred model
            accept="application/json",
            contentType="application/json"
        )

        # Parse the response
        response_body = json.loads(response.get('body').read())
        return response_body.get('completion', '')

    except Exception as e:
        st.error(f"Error calling Amazon Bedrock: {str(e)}")
        return None

st.title("🖥️ Complaint Preprocessing")

# File upload
uploaded_file = st.file_uploader("Upload complaint data (.txt)", type="txt")

if uploaded_file:

    complaint_stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    # AI Analysis Section
    st.header("AI-Powered Complaint Analysis")

    if st.button("Analyze Complaint"):
        with st.spinner("Analyzing complaint..."):
            analysis = analyze_complaint(complaint_stringio.read())
            if analysis:
                st.markdown(analysis)