import streamlit as st

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

# Other page details
if "start_complaint_processing" not in st.session_state:
    st.session_state.start_complaint_processing = False

if "reset_demo" not in st.session_state:
    st.session_state.reset_demo = False

with open("artifacts/complaints.txt", "r") as f:
    complaints = f.readlines()

with open("artifacts/complaint_policy.txt", "r") as c:
    complaint_policy = c.read()

def demo_part_1():
    st.write("#### Applying Your Policy")
    st.write("""
Please view the following complaints as well as the sample complaints policy we will use to judge said complaints. In a 
real world scenario, the complaint policy would be more detailed. However, for the purposes of this demonstration, we'll 
keep it simple. Once you're ready, hit the "Process Complaints" button to move on to the next step.

---
""")

    col1, col2 = st.columns(2)
    left, middle, right = st.columns(3)

    with col1:
        st.write("##### Complaint Policy")
        message = st.chat_message("assistant")
        message.write(complaint_policy)

    with col2:
        st.write("##### Example Complaints")

        for complaint in complaints:
            message = st.chat_message("human")
            message.write(complaint)

    if left.button("Process Complaints", type="primary", icon="↪️"):
        st.write("---")
        demo_part_2()


def demo_part_2():
    with st.spinner("Processing...", show_time=True):
        for complaint in complaints:
            analyze_complaint(complaint_policy, complaint)

def analyze_complaint(policy, complaint):

    user_prompt = f"""
    The following complaint is wrapped in <complaint></complaint> tags and the complaint policy to be evaluated against 
    is wrapped in <policy></policy> tags. Use reasoning to determine if the complaint is actionable or non-actionable 
    according to the company complaint policy. If it is actionable, determine which tier of complaint it is and give 
    your reasoning.
    <complaint>
    {complaint}
    </complaint>
    
    <policy>
    {policy}
    </policy>
    """

    system_prompt = """
    You are an analyst for a bank and you are tasked with reading complaints from customers and determining if they are 
    actionable. You are provided a company policy and should only derive your decisions from it. You should think long 
    and hard about how the complaint could apply to the policy provided.
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

        # Parse the response
        ai_response = st.chat_message("assistant")
        ai_response.write(response)

    except Exception as e:
        st.error(f"Error calling Amazon Bedrock: {str(e)}")
        return None

st.title("🖥️ GenAI Powered Complaint Processing")
st.info("⚠️ **NOTE:** The following demonstration is a visualization of the real-world backend process which will be "
         "running inference either in batch or in near realtime, depending on what you choose to support.")

st.write("FSI customers across the board have internal complaints policies which describes what is and is not "
         "categorized as a complaint. For each and every complaint, this policy will be evaluated to determine "
         "whether or not action is needed and if action is needed, what kind of urgency or priority should be placed "
         "on said complaint.")
st.write("The exception to this is complaints which fall into the regulatory domain, such as "
         "with complaints from the Consumer Financial Protections Bureau (\"CFPB\").")

main_left, main_middle, main_right = st.columns(3)

if main_left.button("Let's Get Started", type="primary", icon="🏃‍♂️", use_container_width=True):
    st.session_state.start_complaint_processing = True

if main_middle.button("Reset Demo", type="secondary", icon="♻️", use_container_width=True):
    st.session_state.reset_demo = True

if st.session_state.start_complaint_processing is True:
    demo_part_1()


