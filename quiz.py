import streamlit as st


st.set_page_config(
    page_title="Career Path Quiz",
    page_icon="🎯",
    layout="wide"
)


quiz_questions = [
    {"key": "age_range", "question": "What is your age range?",
     "options": ["Below 15", "15-18", "19-22", "23-30", "31-40", "41+"],
     "multi": False},
    {"key": "gender", "question": "What is your gender?",
     "options": ["Male", "Female", "Non-binary/Third gender", "Prefer not to say"],
     "multi": False},
    {"key": "education", "question": "What is your highest level of education?",
     "options": ["School (Up to Class 10)", "Higher Secondary (Class 12)", "Diploma", "Undergraduate Degree", "Postgraduate Degree", "Doctorate (PhD)", "Other/None"],
     "multi": False},
    {"key": "subjects", "question": "Which subjects do you find most interesting?",
     "options": ["Math & Science", "Art & Design", "English & Literature", "History & Social Studies", "Technology & Computers", "Physical Education"],
     "multi": True},
    {"key": "programming_language_known", "question": "Which programming languages do you know?",
     "options": ["Python", "C++", "JavaScript", "Ruby", "C", "Java", "None"],
     "multi": True},
    {"key": "problem_solving", "question": "How do you prefer to solve problems?",
     "options": ["With a logical and analytical approach", "Through creative brainstorming", "By experimenting with trial and error", "By collaborating and asking for help"],
     "multi": False},
    {"key": "communication_skills", "question": "How confident are you in your communication skills?",
     "options": ["Very confident", "Somewhat confident", "Not very confident"],
     "multi": False},
]


if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}


def next_question():
    """Save the answer and move to the next question."""
    q_key = quiz_questions[st.session_state.current_q]["key"]
    
    st.session_state.answers[q_key] = st.session_state[f"widget_{q_key}"]
    st.session_state.current_q += 1

def prev_question():
    """Go back to the previous question."""
    if st.session_state.current_q > 0:
        st.session_state.current_q -= 1

def restart_quiz():
    """Reset the quiz to the beginning."""
    st.session_state.current_q = 0
    st.session_state.answers = {}


def render_question():
    """Renders the current question, input widget, and navigation buttons."""
    q_data = quiz_questions[st.session_state.current_q]
    q_key = q_data["key"]
    
   
    stored_answer = st.session_state.answers.get(q_key, [] if q_data["multi"] else None)

    with st.container(border=True):
        
        progress_value = (st.session_state.current_q) / len(quiz_questions)
        st.progress(progress_value, text=f"Question {st.session_state.current_q + 1} of {len(quiz_questions)}")
        
        
        st.subheader(q_data["question"])

        
        if q_data["multi"]:
            st.multiselect(
                "Select all that apply:",
                q_data["options"],
                default=stored_answer,
                key=f"widget_{q_key}", 
                label_visibility="collapsed"
            )
        else:
           
            default_index = q_data["options"].index(stored_answer) if stored_answer in q_data["options"] else None
            st.radio(
                "Choose one:",
                q_data["options"],
                index=default_index,
                key=f"widget_{q_key}", 
                label_visibility="collapsed"
            )

        
        col1, col2, col3 = st.columns([2, 4, 2])
        with col1:
            st.button("⬅\nBack", on_click=prev_question, disabled=(st.session_state.current_q == 0))
        with col3:
            st.button("Next\n➡", on_click=next_question)

def render_results_summary():
    """Renders the final results and submission options."""
    st.success("✅ Quiz Complete!")
    st.balloons()
    
    st.header("Your Quiz Summary")

    for q_data in quiz_questions:
        q_key = q_data["key"]
        answer = st.session_state.answers.get(q_key)

        with st.expander(f"{q_data['question']}"):
            if answer:
               
                if isinstance(answer, list):
                    st.write(" &rarr; ".join(answer))
                else:
                    st.write(f"&rarr; {answer}")
            else:
                st.write("Not answered")

    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit and Find Your Career Path", type="primary", use_container_width=True):
            st.session_state["career_quiz"] = st.session_state.answers
            st.success("Results saved! Taking you to the Career Mentor...")
            
            st.switch_page("pages/pages2.py") 

    with col2:
        st.button("Restart Quiz 🔄", on_click=restart_quiz, use_container_width=True)



st.title("🎯 Career Path Quiz")
st.markdown("Answer these questions to help us understand you better and recommend a suitable career path.")


_, main_col, _ = st.columns([1, 2, 1])

with main_col:
    
    if st.session_state.current_q >= len(quiz_questions):
        render_results_summary()
    else:
        render_question()