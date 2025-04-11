import streamlit as st

st.title("Architecture Diagram")

st.write("### High-Level Architecture")
st.write("""
Complaints are received from various channels, such as through call center agents or App Store reviews. Once received,
other pipelines will deliver the raw complaint to S3 and an ETL process will standardize complaints. Once standardized,
a scheduled or near-realtime GenAI process will initiate (pictured in orange, see ["GenAI Orchestration Architecture"]() 
section below), processing the complaints using the Financial Institutions ("FI") complaint policy (or corresponding 
regulatory complaint schema like from the CFPB).

These curated complaints are now sent to the correct queue in the customer system or other relevant downstream system.
""")
st.image("artifacts/high_level_architecture.png")

st.write("### GenAI Orchestration Architecture")
st.write("""
As detailed above, once the standardized complaints have landed in S3, a scheduled or event-based process will initiate 
and begin to classify the complaints in accordance with the FI's complaint policy or other regulatory definition of a 
complaint.
""")
st.image("artifacts/genai_orchestration_architecture.png")