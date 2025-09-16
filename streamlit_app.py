import streamlit as st
import requests
import json
from datetime import datetime

# Configure the page
st.set_page_config(
    page_title="Healthcare Communication Bot",
    page_icon="🏥",
    layout="wide"
)

# API base URL
API_BASE = "http://127.0.0.1:8000"

# Initialize session state
if "current_scenario" not in st.session_state:
    st.session_state.current_scenario = None
if "last_evaluation" not in st.session_state:
    st.session_state.last_evaluation = None
if "response_text" not in st.session_state:
    st.session_state.response_text = ""
if "api_loading" not in st.session_state:
    st.session_state.api_loading = False

st.title("🏥 Healthcare Communication Practice Bot")
st.markdown("Practice your healthcare communication skills with AI-generated scenarios")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Settings")
    category = st.selectbox(
        "Category",
        ["general", "emergency", "routine"],
        help="Choose the type of healthcare scenario"
    )
    difficulty = st.selectbox(
        "Difficulty",
        ["beginner", "intermediate"],
        help="Select the complexity level"
    )
    
    st.markdown("---")
    st.markdown("💡 **Tips:**")
    st.markdown("- Start with beginner scenarios")
    st.markdown("- Focus on empathy and clarity")
    st.markdown("- Practice different categories")

# Main interface
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Generate Scenario")
    
    if st.button("🎯 Generate New Scenario", type="primary", use_container_width=True, disabled=st.session_state.api_loading):
        st.session_state.api_loading = True
        with st.spinner("🤖 Generating scenario..."):
            try:
                response = requests.post(
                    f"{API_BASE}/scenarios/generate",
                    json={"category": category, "difficulty": difficulty},
                    timeout=30
                )
                print(response.text)
                if response.status_code == 200:
                    scenario = response.json()
                    st.session_state.current_scenario = scenario
                    st.success("✅ Scenario generated successfully!")
                else:
                    st.error(f"❌ Failed to generate scenario: {response.status_code}")
                    if response.text:
                        st.error(f"Error details: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Cannot connect to API. Make sure the FastAPI server is running on port 8000.")
                st.info("Run: `uvicorn app.main:app --host 127.0.0.1 --port 8000`")
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. Please try again.")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
            finally:
                st.session_state.api_loading = False

    # Display current scenario
    if st.session_state.current_scenario:
        scenario = st.session_state.current_scenario
        st.subheader("🎭 Current Scenario")
        
        # Scenario metadata
        col_meta1, col_meta2, col_meta3 = st.columns(3)
        with col_meta1:
            st.info(f"📂 **Category:** {scenario.get('category', 'N/A').title()}")
        with col_meta2:
            st.info(f"📊 **Difficulty:** {scenario.get('difficulty', 'N/A').title()}")
        with col_meta3:
            scenario_id = scenario.get('id', 'N/A')
            st.info(f"🆔 **ID:** {scenario_id[-8:] if len(scenario_id) > 8 else scenario_id}")
        
        # Full scenario ID in expandable section
        with st.expander("🔍 Full Scenario Details"):
            st.text(f"Full Scenario ID: {scenario.get('id', 'N/A')}")
            if scenario.get('created_at'):
                st.text(f"Created: {scenario.get('created_at')}")
            if scenario.get('updated_at'):
                st.text(f"Updated: {scenario.get('updated_at')}")
        
        # Scenario content
        st.markdown("**📖 Scenario Title:**")
        scenario_title = scenario.get('title', 'No title available')
        st.markdown(f"### {scenario_title}")
        
        st.markdown("**📝 Description:**")
        scenario_description = scenario.get('description', 'No description available')
        st.markdown(f"> {scenario_description}")
    else:
        st.info("👆 Click 'Generate New Scenario' to start practicing!")

with col2:
    st.header("💬 Your Response")
    
    if st.session_state.current_scenario:
        st.markdown("**How would you respond to this patient?**")
        
        # Initialize response text in session state if not exists
        if "response_text" not in st.session_state:
            st.session_state.response_text = ""
        
        response_text = st.text_area(
            "Your response:",
            value=st.session_state.response_text,
            height=200,
            placeholder="Type your compassionate and professional response here...",
            help="Consider the patient's emotional state, use clear language, and show empathy. Minimum 10 characters required.",
            label_visibility="collapsed",
            key="response_input"
        )
        
        # Update session state when text changes
        st.session_state.response_text = response_text
        
        # Character counter with validation feedback
        char_count = len(response_text.strip())
        if char_count == 0:
            st.caption("💭 Start typing your response...")
        elif char_count < 10:
            st.caption(f"⚠️ {char_count}/10 characters minimum - {10 - char_count} more needed")
        else:
            st.caption(f"✅ {char_count} characters - Ready to submit!")
        
        col_submit, col_clear = st.columns([3, 1])
        
        with col_submit:
            submit_button = st.button("📤 Submit Response", type="secondary", use_container_width=True)
        
        with col_clear:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.response_text = ""
        
        if submit_button:
            # Validate response length before submission
            if not response_text.strip():
                st.warning("⚠️ Please enter a response before submitting!")
            elif len(response_text.strip()) < 10:
                st.warning("⚠️ Your response is too short. Please provide at least 10 characters to give a meaningful response.")
                st.info("💡 Try to include more details about how you would communicate with the patient.")
            else:
                st.session_state.api_loading = True
                with st.spinner("🔍 Evaluating your response..."):
                    try:
                        response = requests.post(
                            f"{API_BASE}/responses",
                            json={
                                "scenario_id": st.session_state.current_scenario["id"],
                                "response_text": response_text
                            },
                            timeout=30
                        )
                        if response.status_code == 200:
                            evaluation = response.json()
                            st.session_state.last_evaluation = evaluation
                            st.session_state.response_text = ""  # Clear the text after successful submission
                            st.success("✅ Response submitted and evaluated!")
                        elif response.status_code == 422:
                            # Handle validation errors from the API
                            try:
                                error_data = response.json()
                                if "detail" in error_data:
                                    if isinstance(error_data["detail"], list):
                                        # Pydantic validation errors
                                        error_messages = []
                                        for error in error_data["detail"]:
                                            if "response must be at least 10 characters" in str(error.get("msg", "")).lower():
                                                error_messages.append("Response is too short (minimum 10 characters)")
                                            elif "response_text" in str(error.get("loc", [])):
                                                error_messages.append(f"Response validation error: {error.get('msg', 'Invalid response format')}")
                                            else:
                                                error_messages.append(f"Validation error: {error.get('msg', 'Unknown error')}")
                                        
                                        for msg in error_messages:
                                            st.error(f"❌ {msg}")
                                    else:
                                        # Simple string error
                                        st.error(f"❌ Validation error: {error_data['detail']}")
                                else:
                                    st.error(f"❌ Validation error: Please check your response format")
                            except json.JSONDecodeError:
                                st.error("❌ Response validation failed. Please ensure your response is at least 10 characters long.")
                        else:
                            st.error(f"❌ Failed to submit response: {response.status_code}")
                            if response.text:
                                try:
                                    error_data = response.json()
                                    if "detail" in error_data:
                                        st.error(f"Error details: {error_data['detail']}")
                                    else:
                                        st.error(f"Error details: {response.text}")
                                except json.JSONDecodeError:
                                    st.error(f"Error details: {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("🔌 Cannot connect to API. Make sure the FastAPI server is running.")
                    except requests.exceptions.Timeout:
                        st.error("⏱️ Request timed out. Please try again.")
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {str(e)}")
                    finally:
                        st.session_state.api_loading = False
    else:
        st.info("👈 Generate a scenario first to practice your response")

# Display evaluation results
if st.session_state.last_evaluation:
    st.markdown("---")
    st.header("📊 Evaluation Results")
    eval_data = st.session_state.last_evaluation
    
    # Score and metadata in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score = eval_data.get("score", 0)
        if score:
            st.metric("🎯 Score", f"{score}/10")
        else:
            st.metric("🎯 Score", "Pending...")
    
    with col2:
        if st.session_state.current_scenario:
            scenario_id = st.session_state.current_scenario.get("id", "N/A")
        else:
            scenario_id = eval_data.get("scenario_id", "N/A")
        st.metric("🆔 Scenario ID", scenario_id)
    
    with col3:
        timestamp = eval_data.get("submitted_at", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%H:%M")
                st.metric("🕐 Time", time_str)
            except:
                st.metric("🕐 Time", "N/A")
        else:
            st.metric("🕐 Time", "Just now")
    
    # Feedback section
    st.subheader("💬 AI Feedback")
    feedback = eval_data.get("feedback", "Evaluation in progress... Please wait for AI feedback.")
    if feedback:
        st.markdown(feedback)
    else:
        st.info("🤖 AI is evaluating your response. This may take a moment...")
    
    # Show response history in expandable section
    with st.expander("📝 View Your Response"):
        response_content = eval_data.get("response_text", "No response text available")
        st.markdown(f"> {response_content}")

    # Action buttons
    col_new, col_retry = st.columns(2)
    with col_new:
        if st.button("🔄 Try New Scenario", use_container_width=True):
            st.session_state.current_scenario = None
            st.session_state.last_evaluation = None
    
    with col_retry:
        if st.button("🎯 Retry Same Scenario", use_container_width=True):
            st.session_state.last_evaluation = None

st.markdown("---")

with st.expander("🐛 Debug Information"):
    st.subheader("Session State")
    if st.session_state.current_scenario:
        st.json(st.session_state.current_scenario)
    else:
        st.write("No current scenario")
    
    if st.session_state.last_evaluation:
        st.subheader("Last Evaluation")
        st.json(st.session_state.last_evaluation)
    
    st.subheader("API Connection Test")
    if st.button("🔍 Test API Connection"):
        try:
            response = requests.get(f"{API_BASE}/health", timeout=5)
            st.success(f"✅ API Response: {response.status_code}")
            st.json(response.json())
        except Exception as e:
            st.error(f"❌ API Error: {str(e)}")

st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>💡 <strong>Practice Tips:</strong> Focus on empathy, clarity, and professional communication</p>
    <p>🚀 Built with Streamlit • Powered by AI</p>
</div>
""", unsafe_allow_html=True)

# Health check in sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("🔧 System Status")
    
    try:
        health_response = requests.get(f"{API_BASE}/health", timeout=5)
        if health_response.status_code == 200:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Error")
    except:
        st.error("❌ API Offline")
        st.markdown("Start the API with:")
        st.code("uvicorn app.main:app --host 127.0.0.1 --port 8000")