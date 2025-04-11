import streamlit as st
import plotly.express as px

# Header section
st.title("Consumer Complaint Analysis Dashboard")

# Create two columns for the main content
left_col, right_col = st.columns([2, 1])

with left_col:
    # Complaint Details Section
    st.header("Complaint Details")
    with st.expander("Customer Information", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Customer ID", "CUS123456")
        with col2:
            st.metric("Loyalty Status", "Gold")
        with col3:
            st.metric("Previous Complaints", "2")

    # Complaint text and classification
    st.subheader("Complaint Description")
    complaint_text = st.text_area(
        "Complaint",
        value="Product arrived damaged and customer service was unresponsive...",
        height=100,
        label_visibility="collapsed"
    )

    # Analysis Results
    st.subheader("Analysis Results")
    tabs = st.tabs(["Sentiment Analysis", "Category Classification", "Priority Score"])

    with tabs[0]:
        sentiment_chart = px.pie(
            values=[0.7, 0.3],
            names=["Negative", "Neutral"],
            title="Sentiment Distribution"
        )
        st.plotly_chart(sentiment_chart)

    with tabs[1]:
        st.markdown("**Primary Category:** Product Quality")
        st.markdown("**Sub-category:** Damaged on Arrival")

    with tabs[2]:
        st.metric("Priority Score", "8.5/10", delta="High Priority")

with right_col:
    # Next Best Action Section
    st.header("Next Best Actions")

    # Priority indicator
    st.warning("⚠️ High Priority Case - Immediate Action Required")

    # Action recommendations
    with st.container():
        st.subheader("Recommended Actions")
        actions = [
            "1. Contact customer within 2 hours",
            "2. Offer immediate replacement product",
            "3. Provide shipping label for return",
            "4. Add compensation discount"
        ]
        for action in actions:
            st.checkbox(action, key=action)

    # Response Template
    st.subheader("Response Template")
    template = st.text_area(
        "Suggested Response",
        value="Dear [Customer Name],\n\nWe sincerely apologize for the damaged product and the unresponsive customer service...",
        height=200
    )

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        st.button("Send Response", type="primary")
    with col2:
        st.button("Escalate Case")

    # Case History
    with st.expander("Case History"):
        st.markdown("""
        - **2024-02-08 09:00** - Case created
        - **2024-02-08 09:15** - Initial analysis completed
        - **2024-02-08 09:30** - Escalated to priority queue
        """)
