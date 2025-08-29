import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
from youtubesearchpython import VideosSearch
from typing import Dict, Any, List, Optional
import requests
import textwrap
import graphviz
from io import BytesIO
import fitz # PyMuPDF
import base64

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

st.set_page_config(page_title="Career Chat with Function Calling", layout="wide")
st.title("🤖 Personalized Career Mentor with Function Calling")

model = genai.GenerativeModel("gemini-1.5-flash")

if "career_quiz" not in st.session_state:
    st.warning("⚠ Please complete the Career Path Quiz first.")
    st.session_state.career_quiz = {"preferred_career": "data scientist"}
    st.session_state.roadmap_data = None
    st.session_state.article_resources = None

# Prepare quiz context for AI
quiz_context = "User quiz responses:\n"
for key, value in st.session_state.career_quiz.items():
    quiz_context += f"{key}: {value}\n"
quiz_context += "\nProvide personalized career advice."

# Extract preferred career from quiz
preferred_career = st.session_state.career_quiz.get("preferred_career", "").strip().lower()

# Roadmap URLs
roadmap_urls = {
    "frontend developer": "https://roadmap.sh/frontend",
    "backend developer": "https://roadmap.sh/backend",
    "devops engineer": "https://roadmap.sh/devops",
    "data scientist": "https://roadmap.sh/data-science",
    "machine learning engineer": "https://roadmap.sh/machine-learning",
}

# --- FUNCTIONS FROM BOTH CODE BLOCKS ---

def get_career_info(career_name: str, user_skills: Optional[List[str]] = None) -> Dict[str, Any]:
    """Return structured career info. Replace with DB calls in production."""
    user_skills = user_skills or []
    KB = {
        "Data Scientist": {
            "description": "Analyze data, build models, and extract insights for decision making.",
            "required_skills": ["Python", "Statistics", "Machine Learning", "Data Visualization", "SQL"],
            "future_skills": ["MLOps", "Causal ML", "Generative AI for data", "ModelOps"],
            "courses": [
                {"title": "Python for Data Science (Coursera)", "link": "https://www.coursera.org/specializations/data-science-python"},
                {"title": "Machine Learning (Andrew Ng)", "link": "https://www.coursera.org/learn/machine-learning"},
                {"title": "Data Visualization", "link": "https://www.udacity.com/course/data-visualization--nd197"}
            ],
            "portfolio_examples": ["https://github.com/ageron/handson-ml", "https://github.com/benhamner/Machine-Learning-Projects"],
            "mentors": [{"name": "Jane Data", "link": "https://linkedin.com/in/janedata"}],
            "jobs": [{"title": "Data Scientist", "company": "Acme", "link": "https://example.com/apply_ds"}]
        },
        "Software Engineer": {
            "description": "Design and implement software systems, focusing on reliability and scale.",
            "required_skills": ["Programming", "Algorithms", "System Design", "Testing"],
            "future_skills": ["Cloud-native patterns", "Distributed Systems", "AI-assisted coding"],
            "courses": [
                {"title": "CS50", "link": "https://online-learning.harvard.edu/course/cs50-introduction-computer-science"},
                {"title": "System Design Primer", "link": "https://github.com/donnemartin/system-design-primer"}
            ],
            "portfolio_examples": ["https://github.com/trekhleb/javascript-algorithms"],
            "mentors": [{"name": "John Eng", "link": "https://linkedin.com/in/johneng"}],
            "jobs": [{"title": "Backend Engineer", "company": "ScaleX", "link": "https://example.com/apply_be"}]
        },
    }

    base = KB.get(career_name)
    if not base:
        return {
            "career": career_name, "description": "No direct KB entry found.", "required_skills": []
        }

    roadmap = [
        {"phase": "Phase 1: Foundations", "focus": f"Basics: {', '.join(base['required_skills'][:2])}", "resources": base["courses"][:2]},
        {"phase": "Phase 2: Intermediate Skills", "focus": f"Intermediate: {', '.join(base['required_skills'][2:3])}", "resources": base["courses"][1:3]},
        {"phase": "Phase 3: Projects", "focus": "Project & Portfolio: Build 1-2 projects & share on GitHub", "resources": base["portfolio_examples"]}
    ]

    missing_skills = [s for s in base["required_skills"] if s.lower() not in [us.lower() for us in user_skills]]

    return {
        "career": career_name,
        "description": base["description"],
        "required_skills": base["required_skills"],
        "missing_skills": missing_skills,
        "future_skills": base["future_skills"],
        "courses": base["courses"],
        "portfolio_examples": base["portfolio_examples"],
        "mentors": base["mentors"],
        "jobs": base["jobs"],
        "roadmap": roadmap
    }

def get_youtube_videos(career: str) -> List[Dict[str, str]] | str:
    try:
        videosSearch = VideosSearch(f"{career} roadmap skills", limit=3)
        results = videosSearch.result().get('result', [])
        videos = []
        for video in results:
            videos.append({
                "title": video['title'],
                "link": video['link'],
                "channel": video['channel']['name'],
                "duration": video['duration']
            })
        return videos
    except Exception as e:
        return f"Error fetching YouTube videos: {e}"

def web_scrape_linkedin_profile(query: str) -> str:
    # Placeholder for real scraping function
    return f"Simulated scraped data for LinkedIn profile query: {query}"


# --- FUNCTION DEFINITIONS FOR GEMINI (COMBINED) ---

function_definitions = [
    {
        "name": "get_career_info",
        "description": "Fetch structured career information, roadmap, resources, mentors and jobs for a given career.",
        "parameters": {
            "type": "object",
            "properties": {
                "career_name": {"type": "string", "description": "Name of the career (e.g., Data Scientist)."},
                "user_skills": {"type": "array", "items": {"type": "string"}, "description": "List of user's existing skills."}
            },
            "required": ["career_name"]
        }
    },
    {
        "name": "get_youtube_videos",
        "description": "Fetches top YouTube learning videos related to the career.",
        "parameters": {
            "type": "object",
            "properties": {
                "career": {
                    "type": "string",
                    "description": "Career name to search videos for."
                }
            },
            "required": ["career"]
        }
    },
    {
        "name": "web_scrape_linkedin_profile",
        "description": "Scrapes LinkedIn or other profiles for relevant career insights.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for LinkedIn profiles."
                }
            },
            "required": ["query"]
        }
    }
]

# --- HELPER TO HANDLE FUNCTION CALLS (COMBINED) ---

def handle_function_call(function_call: Dict[str, Any]) -> str:
    fname = function_call.get("name")
    fargs = function_call.get("args", {})

    if fname == "get_career_info":
        career_name = fargs.get("career_name", "")
        user_skills = fargs.get("user_skills", [])
        
        func_result = get_career_info(career_name, user_skills)
        if func_result:
            st.session_state["career_info"] = func_result
            # Display detailed info in the main chat window
            st.markdown(f"### 🎯 Career: {func_result['career']}")
            st.write(func_result["description"])
            st.markdown("**Required Skills**: " + ", ".join(func_result["required_skills"]))

            dot = graphviz.Digraph()
            for i, step in enumerate(func_result["roadmap"]):
                label = textwrap.shorten(f"{step['phase']}\n{step['focus']}", width=80)
                dot.node(str(i), label)
                if i > 0:
                    dot.edge(str(i-1), str(i))
            st.graphviz_chart(dot)
            return f"Provided detailed information and roadmap for {career_name}."
        else:
            return f"Could not find information for {career_name}."
    
    if fname == "get_youtube_videos":
        career = fargs.get("career", "")
        videos = get_youtube_videos(career)
        if isinstance(videos, str):
            return videos
        result_text = ""
        for v in videos:
            result_text += f"- [{v['title']}]({v['link']}) by {v['channel']} ({v['duration']})\n"
        return result_text if result_text else "No videos found."

    if fname == "web_scrape_linkedin_profile":
        query = fargs.get("query", "")
        scraped_data = web_scrape_linkedin_profile(query)
        return scraped_data

    return "Function not recognized."


# --- STREAMLIT UI ---

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown(f"### 📊 Quiz Result")
    st.write(f"**Preferred Career**: **{preferred_career.title()}**")
    st.info("Ask the mentor for a roadmap or skills to get started!")

    if "career_info" in st.session_state:
        st.markdown("---")
        st.markdown("### Resources")
        info = st.session_state["career_info"]
        if info.get("courses"):
            st.markdown("**Courses**")
            for c in info["courses"]:
                st.write(f"- [{c['title']}]({c['link']})")
        
        if info.get("mentors"):
            st.markdown("**Mentors**")
            for m in info["mentors"]:
                st.write(f"- [{m['name']}]({m['link']})")

with col2:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User prompt input
    prompt = st.chat_input("Ask about your career, skills, roadmap, or resources...")

    if prompt:
        full_prompt = quiz_context + f"\nUser question: {prompt}\n"
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            response = model.generate_content(
                contents=[{"role": "user", "parts": [{"text": full_prompt}]}],
                tools=function_definitions,
                tool_config={"mode": "AUTO"}
            )
            
            bot_reply = ""
            try:
                function_call = response.candidates[0].content.parts[0].function_call
                function_response = handle_function_call(function_call)
                bot_reply = function_response
            except (AttributeError, IndexError):
                # If no function call, get the text response
                bot_reply = response.text
                
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            with st.chat_message("assistant"):
                st.markdown(bot_reply)

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")