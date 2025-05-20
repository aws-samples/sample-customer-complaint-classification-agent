import streamlit as st
import json
from utils.helpers import *

# Initialize Model Settings
if "bedrock_runtime_client" not in st.session_state:
    bedrock_runtime_client, bedrock_service_client = bedrock_init()
    st.session_state.bedrock_runtime_client = bedrock_runtime_client
    st.session_state.bedrock_service_client = bedrock_service_client

if "model_id" not in st.session_state:
    st.session_state.model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

if "model_temperature" not in st.session_state:
    st.session_state.model_temperature = 0.0

if "top_p" not in st.session_state:
    st.session_state.top_p = 0.0

if "max_tokens" not in st.session_state:
    st.session_state.max_tokens = 2000

# Session state for complaint tracking
if "start_processing" not in st.session_state:
    st.session_state.start_processing = False

if "reset_demo" not in st.session_state:
    st.session_state.reset_demo = False

if "processed_complaints" not in st.session_state:
    st.session_state.processed_complaints = []

if "current_complaint_index" not in st.session_state:
    st.session_state.current_complaint_index = 0

with open("artifacts/complaint_policy.txt", "r") as f:
    complaint_policy = f.read()

with open("artifacts/complaints.txt", "r") as f:
    complaints = [x.strip() for x in f.read().split("\n\n") if x.strip()]

def classify_interaction_type(interaction):
    """Quick classification to identify if an interaction is a complaint"""
    user_prompt = f"""
    Analyze this customer interaction and determine if it's a complaint:
    
    {interaction}
    
    Provide your analysis in JSON format with just category and reason:
    {{
        "category": "Complaints|Other",
        "reason": "Brief explanation of why"
    }}
    """
    
    system_prompt = "You are a customer interaction classifier. Determine if the interaction is a complaint or not."
    
    model_settings = ModelSettings(
        temperature=0.0,
        top_p=0.0,
        model_id=st.session_state.model_id,
        max_tokens=500
    )
    
    prompts = Prompts(
        user_prompt=user_prompt,
        system_prompt=system_prompt
    )
    
    try:
        response = converse(prompts, model_settings, st.session_state.bedrock_runtime_client)
        return json.loads(response)
    except:
        return None

def process_complaint(complaint_text, policy):
    """Detailed complaint analysis based on policy guidelines"""
    user_prompt = f"""
    Analyze this customer complaint according to our complaint handling policy.
    
    <complaint>
    {complaint_text}
    </complaint>
    
    <policy>
    {policy}
    </policy>
    
    Provide a detailed analysis in the following JSON structure:
    {{
        "category": "Product/Service Quality|Customer Service|Technical|Billing/Financial|Policy/Procedure|Privacy/Security",
        "priority": "High|Medium|Low",
        "summary": "Brief description of the complaint",
        "required_response_time": "Time frame based on priority",
        "recommended_actions": [
            "List of specific steps to take"
        ],
        "escalation_level": "Initial escalation level (1-4)",
        "immediate_response": "Suggested initial response to customer",
        "investigation_needs": [
            "List of information/documents needed"
        ],
        "potential_resolution": "Proposed solution",
        "follow_up_required": true/false,
        "rationale": "Explanation of this analysis"
    }}
    """
    
    system_prompt = """
    You are a complaint handling specialist. Analyze complaints according to policy guidelines and provide 
    actionable recommendations. Be empathetic to customer concerns while ensuring compliance with procedures.
    """
    
    model_settings = ModelSettings(
        temperature=st.session_state.model_temperature,
        top_p=st.session_state.top_p,
        model_id=st.session_state.model_id,
        max_tokens=st.session_state.max_tokens
    )
    
    prompts = Prompts(
        user_prompt=user_prompt,
        system_prompt=system_prompt
    )
    
    try:
        response = converse(prompts, model_settings, st.session_state.bedrock_runtime_client)
        return json.loads(response)
    except Exception as e:
        st.error(f"Error processing complaint: {str(e)}")
        return None

def show_complaint_dashboard():
    st.write("### Complaint Processing Dashboard")
    
    if st.session_state.processed_complaints:
        # Create metrics
        col1, col2, col3 = st.columns(3)
        
        # Count complaints by priority
        priority_counts = {
            "High": len([x for x in st.session_state.processed_complaints if x["analysis"]["priority"] == "High"]),
            "Medium": len([x for x in st.session_state.processed_complaints if x["analysis"]["priority"] == "Medium"]),
            "Low": len([x for x in st.session_state.processed_complaints if x["analysis"]["priority"] == "Low"])
        }
        
        col1.metric("High Priority", priority_counts["High"])
        col2.metric("Medium Priority", priority_counts["Medium"])
        col3.metric("Low Priority", priority_counts["Low"])
        
        # Category distribution
        st.write("#### Complaint Categories")
        categories = {}
        for complaint in st.session_state.processed_complaints:
            cat = complaint["analysis"]["category"]
            categories[cat] = categories.get(cat, 0) + 1
        
        st.bar_chart(categories)
        
        st.write("---")

def display_complaint_analysis(complaint_text, analysis):
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.write("##### Customer Complaint")
        message = st.chat_message("human")
        message.write(complaint_text)
    
    with col2:
        st.write("##### Analysis & Recommendations")
        message = st.chat_message("assistant")
        message.write(f"**Category:** {analysis['category']}")
        message.write(f"**Priority:** {analysis['priority']}")
        message.write(f"**Response Required By:** {analysis['required_response_time']}")
        message.write(f"**Escalation Level:** {analysis['escalation_level']}")
        
        with st.expander("Detailed Analysis"):
            st.write("**Summary:**")
            st.write(analysis['summary'])
            st.write("**Recommended Actions:**")
            for action in analysis['recommended_actions']:
                st.write(f"- {action}")
            st.write("**Suggested Initial Response:**")
            st.write(analysis['immediate_response'])
            if analysis['follow_up_required']:
                st.write("**⚠️ Follow-up Required**")

def demo_complaint_processing():
    st.write("#### Complaint Analysis & Resolution Planning")
    st.write("""
    Review each complaint and see how AI analyzes it according to our complaint handling policy.
    The system will provide detailed recommendations for resolution and handling.
    
    ---
    """)
    
    with st.expander("Complaint Handling Policy"):
        st.write(complaint_policy)
    
    st.write("##### Current Complaint")
    
    if complaints:
        current_complaint = complaints[st.session_state.current_complaint_index]
        
        # Process complaint if not already processed
        if len(st.session_state.processed_complaints) <= st.session_state.current_complaint_index:
            analysis = process_complaint(current_complaint, complaint_policy)
            if analysis:
                st.session_state.processed_complaints.append({
                    "text": current_complaint,
                    "analysis": analysis
                })
        
        # Display current complaint and its analysis
        if st.session_state.processed_complaints:
            current_analysis = st.session_state.processed_complaints[st.session_state.current_complaint_index]
            display_complaint_analysis(current_analysis["text"], current_analysis["analysis"])
        
        # Navigation
        nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
        
        with nav_col1:
            if st.button("Previous", disabled=st.session_state.current_complaint_index <= 0):
                st.session_state.current_complaint_index -= 1
                st.rerun()
        
        with nav_col2:
            st.write(f"Complaint {st.session_state.current_complaint_index + 1} of {len(complaints)}")
        
        with nav_col3:
            if st.button("Next", disabled=st.session_state.current_complaint_index >= len(complaints) - 1):
                st.session_state.current_complaint_index += 1
                st.rerun()
        
        # Show dashboard after processing
        if st.session_state.processed_complaints:
            st.write("---")
            show_complaint_dashboard()
    else:
        st.warning("No complaints found in the current dataset.")

def reset_demo():
    st.session_state.processed_complaints = []
    st.session_state.start_processing = False
    st.session_state.current_complaint_index = 0

st.title("🔦 Complaint Analysis & Resolution Planning")
st.info("""
⚠️ **NOTE:** This demonstration shows how AI can help analyze customer complaints and provide 
structured recommendations for resolution based on established policies.
""")

st.write("""
Effective complaint handling is crucial for:

1. Maintaining customer satisfaction and loyalty
2. Meeting regulatory requirements
3. Identifying systemic issues
4. Improving products and services
5. Preventing escalations

This demo shows how GenAI can help streamline the complaint handling process while ensuring 
policy compliance and consistent handling.
""")

main_left, main_middle, main_right = st.columns(3)

if main_left.button("Start Demo", type="primary", icon="🏃‍♂️", use_container_width=True):
    st.session_state.start_processing = True

if main_middle.button("Reset Demo", type="secondary", icon="♻️", use_container_width=True):
    reset_demo()

if st.session_state.start_processing:
    demo_complaint_processing()
