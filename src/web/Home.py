import streamlit as st


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