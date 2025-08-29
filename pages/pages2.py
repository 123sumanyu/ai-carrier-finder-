import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import re
from google.generativeai.types import Tool, FunctionDeclaration
from streamlit_mermaid import st_mermaid
import time

# --- 1. SETUP AND CONFIGURATION ---
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

st.set_page_config(
    page_title="Career Mentor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Check for Quiz Data ---
if "career_quiz" not in st.session_state:
    st.warning("Please complete the '🎯 Career Path Quiz' first to personalize your experience.")
    st.page_link("pages/quiz.py", label="Take the Quiz", icon="🎯")
    st.stop()

# Configure the Generative AI model
if not API_KEY:
    st.error("Google API Key not found. Please set the GOOGLE_API_KEY environment variable.")
    st.stop()
try:
    genai.configure(api_key=API_KEY)
except Exception as e:
    st.error(f"Failed to configure Google AI. Is your API Key correct? Error: {e}")
    st.stop()

# --- 2. FUNCTION CALLING & TOOLS ---

def get_career_roadmap(career: str):
    """
    Placeholder function for the AI to call. It returns the career name identified by the AI.
    The app then generates the detailed roadmap based on this name.
    """
    return career

get_career_roadmap_func = FunctionDeclaration(
    name="get_career_roadmap",
    description="Provides a detailed career roadmap, skills, and resources for a specific career path like 'data science' or 'software engineer'. Use this when the user asks for a roadmap or expresses interest in a specific career.",
    parameters={
        "type": "object",
        "properties": {
            "career": {
                "type": "string",
                "description": "The name of the career path, e.g., 'Software Engineer'."
            }
        },
        "required": ["career"]
    },
)

# --- 3. HELPER FUNCTIONS ---

@st.cache_data
def generate_roadmap_details(career: str):
    """Generates the detailed content for the career roadmap using a separate, non-tooled model call."""
    time.sleep(1)  # A small delay to respect API rate limits
    
    prompt = f"""
    You are a world-class career mentor providing a detailed guide for an aspiring '{career}'.
    Your response must be encouraging, clear, and structured.
    Generate the following sections in well-formatted Markdown:

    ### 🎯 Key Skills to Master
    List and briefly describe the most crucial technical and soft skills.

    ### 🗺 Career Roadmap Summary
    Provide a step-by-step summary of the career path from beginner to advanced.

    ### 📄 Resume Keywords
    Suggest powerful keywords to include in a resume for this career.
    
    ### 📚 Recommended Learning Resources
    Provide a bulleted list of 3-5 high-quality learning resources. Include a mix of online courses (like on Coursera or Udemy), essential books, and popular YouTube channels or blogs.

    ### 🧠 Career Roadmap Visualization
    Create a *Mermaid.js flowchart* using modern Mermaid v10 syntax. 
    - Use the graph TD direction for a top-down flowchart.
    - *Crucially, ensure all node text is enclosed in double quotes within the brackets.*
    - For example: A["Step 1: Learn Python"] --> B["Step 2: Master SQL"];
    - Start the code block with mermaid.
    """
    detail_model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
    response = detail_model.generate_content(prompt)
    return response.text

# --- 4. SESSION STATE & CHAT INITIALIZATION ---

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat" not in st.session_state:
    quiz_summary = "The user has completed a quiz. Here are their answers:\n"
    for key, value in st.session_state.career_quiz.items():
        quiz_summary += f"- {key.replace('_', ' ').title()}: {value}\n"

    # --- THIS IS THE UPDATED INSTRUCTION BLOCK ---
    system_instruction = (
        "You are a friendly and encouraging AI career mentor. Your goal is to help the user explore career paths "
        "based on their quiz results and answer their career-related questions. Your primary tool is 'get_career_roadmap'."
        "\n\n"
        "When a user *specifically asks for a detailed 'roadmap'* for a career, you should use this tool to provide a "
        "comprehensive guide. For more general questions about careers (e.g., 'What do data scientists do?') or "
        "other topics, you should answer them directly in a conversational manner."
    )

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest",
        tools=[get_career_roadmap_func],
        system_instruction=system_instruction
    )
    
    st.session_state.chat = model.start_chat(history=[
        {'role': 'user', 'parts': [quiz_summary]},
        {'role': 'model', 'parts': ["Hello! Thanks for completing the quiz. Based on your answers, a career in **Data Science** or **Software Engineering** could be a great fit for you. You can ask me for a detailed roadmap for these careers, or feel free to ask any other questions you might have!"]}
    ])

# --- 5. GUI & CHAT INTERFACE ---

# --- Sidebar ---
with st.sidebar:
    st.image("animation.gif")
    st.title("Your Quiz Profile")
    st.markdown("Here's a summary of your quiz answers:")
    
    for key, value in st.session_state.career_quiz.items():
        label = f"**{key.replace('_', ' ').title()}**"
        if isinstance(value, list) and value:
            st.markdown(label)
            st.markdown("".join([f"- {v}\n" for v in value]))
        elif not isinstance(value, list):
            st.markdown(f"{label}: {value}")
    
    st.markdown("---")
    if st.button("🔄 Restart Chat"):
        for key in ["chat", "messages"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# --- Main Chat Area ---
st.title("🤖 Personalized Career Mentor")
st.markdown("Ask me to create a roadmap for a career you're interested in!")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        mermaid_code = re.search(r"mermaid(.*?)", message["content"], re.DOTALL)
        if mermaid_code:
            st_mermaid(mermaid_code.group(1).strip())

if prompt := st.chat_input("What career path can I help you with today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                response = st.session_state.chat.send_message(prompt)
            
            function_call = None
            if response.parts:
                for part in response.parts:
                    if part.function_call:
                        function_call = part.function_call
                        break
            
            if function_call and function_call.name == "get_career_roadmap":
                args = function_call.args
                career_name = get_career_roadmap(career=args["career"])
                
                st.info(f"Great choice! Generating a detailed roadmap for **{career_name.title()}**...")
                
                with st.spinner(f"Curating resources for {career_name}..."):
                    roadmap_content = generate_roadmap_details(career_name)
                    st.markdown(roadmap_content)
                    st.session_state.messages.append({"role": "assistant", "content": roadmap_content})
                    
                    mermaid_code = re.search(r"mermaid(.*?)```", roadmap_content, re.DOTALL)
                    if mermaid_code:
                        st_mermaid(mermaid_code.group(1).strip())

            else:
                text_response = response.text
                st.markdown(text_response)
                st.session_state.messages.append({"role": "assistant", "content": text_response})

        except Exception as e:
            if "ResourceExhausted" in str(e):
                st.error("🚫 API rate limit exceeded. Please wait a minute before sending another message.")
            else:
                st.error(f"An error occurred: {e}")