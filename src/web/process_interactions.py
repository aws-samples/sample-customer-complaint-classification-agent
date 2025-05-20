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

# Session state for interaction tracking
if "start_processing" not in st.session_state:
    st.session_state.start_processing = False

if "reset_demo" not in st.session_state:
    st.session_state.reset_demo = False

if "processed_interactions" not in st.session_state:
    st.session_state.processed_interactions = []

if "current_interaction_index" not in st.session_state:
    st.session_state.current_interaction_index = 0

# Load example interactions and guidelines
with open("artifacts/customer_interactions.txt", "r") as f:
    interactions = [x.strip() for x in f.read().split("\n\n") if x.strip()]

with open("artifacts/interaction_guidelines.txt", "r") as g:
    guidelines = g.read()

def show_interaction_dashboard():
    st.write("### Customer Interaction Classification Dashboard")
    
    # Display metrics
    if st.session_state.processed_interactions:
        col1, col2, col3, col4 = st.columns(4)
        
        # Count interactions by type
        interaction_counts = {
            "Complaints": len([x for x in st.session_state.processed_interactions if x["category"] == "Complaints"]),
            "Feedback": len([x for x in st.session_state.processed_interactions if x["category"] == "Feedback"]),
            "Service Requests": len([x for x in st.session_state.processed_interactions if x["category"] == "Service Requests"]),
            "Urgent Issues": len([x for x in st.session_state.processed_interactions if x["category"] == "Urgent Issues"])
        }
        
        col1.metric("Complaints", interaction_counts["Complaints"])
        col2.metric("Feedback", interaction_counts["Feedback"])
        col3.metric("Service Requests", interaction_counts["Service Requests"])
        col4.metric("Urgent Issues", interaction_counts["Urgent Issues"])
        
        st.write("---")

def demo_part_1():
    st.write("#### Customer Interaction Classification")
    st.write("""
Review each customer interaction and see how AI analyzes and classifies it based on the guidelines.
Each interaction will be processed automatically and you can navigate through them using the buttons below.

---
""")

    with st.expander("Classification Guidelines"):
        st.write(guidelines)

    st.write("##### Current Interaction")

    # Create two columns for guidelines and interaction
    col1, col2 = st.columns([1, 1])

    with col1:
        if 0 <= st.session_state.current_interaction_index < len(interactions):
            current_interaction = interactions[st.session_state.current_interaction_index]
            message = st.chat_message("human")
            message.write(current_interaction)

    with col2:
            # Process and show classification for current interaction
            result = classify_interaction(guidelines, current_interaction)
            if result:
                if len(st.session_state.processed_interactions) <= st.session_state.current_interaction_index:
                    st.session_state.processed_interactions.append(result)
                elif st.session_state.processed_interactions[st.session_state.current_interaction_index] != result:
                    st.session_state.processed_interactions[st.session_state.current_interaction_index] = result

    # Navigation buttons
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    
    with nav_col1:
        if st.button("Previous", disabled=st.session_state.current_interaction_index <= 0):
            st.session_state.current_interaction_index -= 1
            st.rerun()
    
    with nav_col2:
        st.write(f"Interaction {st.session_state.current_interaction_index + 1} of {len(interactions)}")
    
    with nav_col3:
        if st.button("Next", disabled=st.session_state.current_interaction_index >= len(interactions) - 1):
            st.session_state.current_interaction_index += 1
            st.rerun()

    # Show metrics dashboard after processing
    if st.session_state.processed_interactions:
        st.write("---")
        show_interaction_dashboard()


def reset_demo():
    st.session_state.processed_interactions = []
    st.session_state.start_processing = False
    st.session_state.current_interaction_index = 0

def classify_interaction(guidelines, interaction):
    user_prompt = f"""
    The following customer interaction is wrapped in <interaction></interaction> tags and the classification guidelines
    are wrapped in <guidelines></guidelines> tags. Analyze the interaction to determine its category and appropriate routing.

    <interaction>
    {interaction}
    </interaction>
    
    <guidelines>
    {guidelines}
    </guidelines>
    
    Think carefully about:
    1. The nature of the interaction (complaint, feedback, service request, or urgent issue)
    2. The key elements that determine its classification
    3. The appropriate team for handling this interaction
    4. Any immediate actions or priority level needed
    
    Provide your analysis in the following JSON structure:
    {{
        "category": "Complaints|Feedback|Service Requests|Urgent Issues",
        "summary": "Brief summary of the interaction",
        "routing": "Name of team to handle this",
        "priority": "High|Medium|Low",
        "rationale": "Your reasoning for this classification"
    }}
    """

    system_prompt = """
    You are a customer interaction analyst for a bank. Your role is to accurately classify incoming customer interactions
    and ensure they are routed to the appropriate teams for handling. Follow the guidelines strictly and ensure your
    response is in valid JSON format.
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
        # Call Bedrock
        response = converse(prompts, model_settings, st.session_state.bedrock_runtime_client)
        
        # Parse the JSON response
        result = json.loads(response)
        
        # Display the classification result
        message = st.chat_message("assistant")
        message.write(f"**Category:** {result['category']}")
        message.write(f"**Summary:** {result['summary']}")
        message.write(f"**Routing:** {result['routing']}")
        message.write(f"**Priority:** {result['priority']}")
        message.write(f"**Rationale:** {result['rationale']}")
        
        return result

    except Exception as e:
        st.error(f"Error processing interaction: {str(e)}")
        return None

st.title("🎯 Customer Interaction Reasoning & Routing")
st.info("""
⚠️ **NOTE:** This demonstration shows how AI can be used to intelligently classify and route customer interactions
to the appropriate teams, improving response times and customer satisfaction.
""")

st.write("""
Financial institutions receive various types of customer interactions daily - from complaints and feedback to
service requests and urgent issues. Proper classification and routing of these interactions is crucial for:

1. Ensuring timely responses
2. Meeting regulatory requirements
3. Improving customer satisfaction
4. Identifying trends and areas for improvement

This demo shows how GenAI can help automate this process while maintaining accuracy and consistency.
""")

main_left, main_middle, main_right = st.columns(3)

if main_left.button("Start Demo", type="primary", icon="🏃‍♂️", use_container_width=True):
    st.session_state.start_processing = True

if main_middle.button("Reset Demo", type="secondary", icon="♻️", use_container_width=True):
    reset_demo()

if st.session_state.start_processing:
    demo_part_1()
