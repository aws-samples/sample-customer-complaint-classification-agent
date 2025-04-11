import streamlit as st
from utils.helpers import *

bedrock_runtime_client, bedrock_service_client = bedrock_init()

col1, col2 = st.columns(2)

## Model Settings
if "bedrock_runtime_client" not in st.session_state:
    st.session_state.bedrock_runtime_client = bedrock_runtime_client

if "bedrock_service_client" not in st.session_state:
    st.session_state.bedrock_service_client = bedrock_service_client

if "models" not in st.session_state:
    st.session_state.models = []

if "model_id" not in st.session_state:
    st.session_state.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

if "model_temperature" not in st.session_state:
    st.session_state.model_temperature = 0.0

if "top_p" not in st.session_state:
    st.session_state.top_p = 0.0

st.session_state.models = list_foundation_models(bedrock_service_client)

# Header section
st.title("📊 Financial Services Complaint Analysis with AI")
st.markdown("### Transforming Customer Feedback into Actionable Insights")

# Introduction
st.write("""
Welcome to our innovative platform that leverages the power of Generative AI to analyze 
and understand consumer complaints in the financial services industry. Like a skilled 
detective who can spot patterns in seemingly unrelated cases, large language models powered by Amazon Bedrock help 
uncover hidden trends and insights in customer feedback.
""")

# Main features in columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("🎯 Why AI-Powered Complaint Analysis?")
    st.info("""
    Traditional complaint analysis is like trying to find a needle in a haystack - 
    time-consuming and often missing crucial patterns. Our AI approach is more like 
    having a metal detector that can quickly scan the entire haystack and identify 
    all the metallic objects at once.

    Key Benefits:
    • Process thousands of complaints in minutes
    • Identify emerging issues before they become trends
    • Understand customer sentiment across products
    • Generate actionable recommendations automatically
    """)

with col2:
    st.subheader("🔍 How It Works")
    st.success("""
    Our system works like a highly skilled customer service team that never gets tired:

    1. Complaint Ingestion: Automatically processes and categorizes incoming complaints
    2. Pattern Recognition: Identifies common themes and urgent issues
    3. Sentiment Analysis: Understands customer emotions and urgency
    4. Insight Generation: Creates actionable recommendations
    5. Trend Tracking: Monitors changes over time
    """)