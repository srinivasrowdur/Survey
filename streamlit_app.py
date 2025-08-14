import streamlit as st
import json
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "survey_answers" not in st.session_state:
    st.session_state.survey_answers = {}

if "current_question" not in st.session_state:
    st.session_state.current_question = 0

if "survey_completed" not in st.session_state:
    st.session_state.survey_completed = False

# Survey questions definition
SURVEY_QUESTIONS = [
    {
        "id": "biggest_challenge",
        "question": "We have identified five key trends and their implications for the customer contact sector over the next five years. Which do you see as posing the biggest challenges for your organisation?",
        "options": [
            "Return to customer care",
            "The super powered customer", 
            "Regulation for good",
            "Rise of the conscious consumer",
            "The agent of the future"
        ],
        "type": "choice",
        "help": "Please select the trend that poses the biggest challenge for your organisation."
    },
    {
        "id": "challenge_reason",
        "question": "Why is that the biggest challenge for your organisation?",
        "options": [
            "Financial impact",
            "Workforce impact", 
            "Skills and capability implications",
            "Organisational strategy implications",
            "Something else"
        ],
        "type": "choice",
        "help": "Please select the primary reason why this trend poses the biggest challenge."
    },
    {
        "id": "organisational_readiness",
        "question": "To what extent is your organisation already looking into addressing this challenge?",
        "options": [
            "Not at all",
            "Still considering, but no actions yet",
            "Being somewhat addressed across parts of the business",
            "It's being fully addressed in the business"
        ],
        "type": "choice",
        "help": "Please indicate your organisation's current level of readiness to address this challenge."
    },
    {
        "id": "most_challenging_persona",
        "question": """With Industry Council input, we have defined three personas: Future Customer, Future Frontline Worker, and Future Leader.

🔮 **Future Customer**: Empowered, digitally fluent individuals seeking personalised, empathetic and ethical experiences across channels.

👥 **Future Frontline Worker**: Tech-savvy, emotionally intelligent professionals thriving in flexible, inclusive, and purpose-driven environments.

🧠 **Future Leader**: Emotionally intelligent change-makers who lead with purpose, adaptability, and a people-first mindset.

Which of these personas do you see as being most challenging to satisfy within your organisation?""",
        "options": [
            "Future customer",
            "Future frontline worker", 
            "Future leader"
        ],
        "type": "choice",
        "help": "Please select the persona that poses the biggest challenge for your organisation."
    },
    {
        "id": "persona_challenge_factor",
        "question": "What is the biggest factor influencing this challenge?",
        "options": [
            "Budgetary constraints",
            "Sourcing and location factors",
            "Technological factors", 
            "Not in line with organisational strategy",
            "Skills and capability gaps",
            "Operating model",
            "Organisational culture and leadership",
            "Something else"
        ],
        "type": "choice",
        "help": "Please select the primary factor that makes this persona challenging to satisfy."
    },
    {
        "id": "biggest_positive_impact",
        "question": "Please tell us what you see as the factor that would have the biggest positive impact on your organisation's ability to respond effectively to the future customer/employee needs set out here?",
        "type": "text",
        "help": "Please provide your thoughts on what would have the biggest positive impact."
    }
]

def display_welcome_message():
    """Display the welcome message for the survey"""
    welcome_message = """Thank you for providing your thoughts prior to the CCA Industry Council on October 4th. This will really help us ensure you can get most out of the workshop session we have planned in the afternoon.

We have three questions we'd like to get your input on. Please respond to each question as it appears."""
    
    st.session_state.messages.append({"role": "assistant", "content": welcome_message})

def get_next_question():
    """Get the next unanswered question"""
    for i, question in enumerate(SURVEY_QUESTIONS):
        if question["id"] not in st.session_state.survey_answers:
            return i, question
    return None, None

def format_question(question):
    """Format the question for display"""
    content = question["question"]
    
    if question["type"] == "choice":
        content += "\n\n**Options:**\n"
        for i, option in enumerate(question["options"], 1):
            content += f"{i}. {option}\n"
    
    if question.get("help"):
        content += f"\n\n💡 **Help**: {question['help']}"
    
    return content

def validate_answer(question, answer):
    """Validate the user's answer"""
    if question["type"] == "choice":
        if answer.lower() in [opt.lower() for opt in question["options"]]:
            # Find the exact case match
            for option in question["options"]:
                if option.lower() == answer.lower():
                    return option
        else:
            return None
    elif question["type"] == "text":
        if answer.strip():
            return answer.strip()
    return None

def process_user_input(user_input):
    """Process the user's input and move to next question"""
    current_idx, current_question = get_next_question()
    
    if current_question is None:
        return
    
    # Validate the answer
    validated_answer = validate_answer(current_question, user_input)
    
    if validated_answer is None:
        # Invalid answer, ask again
        error_msg = f"I didn't understand that response. "
        if current_question["type"] == "choice":
            error_msg += f"Please select one of the options: {', '.join(current_question['options'])}"
        else:
            error_msg += "Please provide a text response."
        
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        return
    
    # Save the answer
    st.session_state.survey_answers[current_question["id"]] = validated_answer
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Check if survey is complete
    next_idx, next_question = get_next_question()
    
    if next_question is None:
        # Survey completed
        st.session_state.survey_completed = True
        completion_message = """Thank you for completing the CCA Industry Council survey! Your input is invaluable to us.

Here's a summary of your responses:

"""
        for question in SURVEY_QUESTIONS:
            answer = st.session_state.survey_answers.get(question["id"])
            if answer:
                completion_message += f"**{question['question'].split('?')[0]}?** {answer}\n\n"
        
        completion_message += "Your responses will help us ensure the workshop session is tailored to address the key challenges and opportunities facing the customer contact sector."
        
        st.session_state.messages.append({"role": "assistant", "content": completion_message})
    else:
        # Ask next question
        next_question_formatted = format_question(next_question)
        st.session_state.messages.append({"role": "assistant", "content": next_question_formatted})

def main():
    st.set_page_config(
        page_title="CCA Industry Council Survey",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 CCA Industry Council Pre-Workshop Survey")
    st.markdown("---")
    
    # Initialize welcome message if this is the first time
    if not st.session_state.messages:
        display_welcome_message()
        current_idx, current_question = get_next_question()
        if current_question:
            first_question = format_question(current_question)
            st.session_state.messages.append({"role": "assistant", "content": first_question})
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if not st.session_state.survey_completed:
        if prompt := st.chat_input("Type your response here..."):
            process_user_input(prompt)
            st.rerun()
    else:
        st.success("✅ Survey completed! Thank you for your participation.")
        
        # Display results in a nice format
        st.subheader("📋 Your Survey Responses")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Question 1: Biggest Challenge**")
            st.info(f"**Trend:** {st.session_state.survey_answers.get('biggest_challenge', 'Not answered')}")
            st.info(f"**Reason:** {st.session_state.survey_answers.get('challenge_reason', 'Not answered')}")
            st.info(f"**Readiness:** {st.session_state.survey_answers.get('organisational_readiness', 'Not answered')}")
        
        with col2:
            st.markdown("**Question 2: Most Challenging Persona**")
            st.info(f"**Persona:** {st.session_state.survey_answers.get('most_challenging_persona', 'Not answered')}")
            st.info(f"**Factor:** {st.session_state.survey_answers.get('persona_challenge_factor', 'Not answered')}")
        
        st.markdown("**Question 3: Biggest Positive Impact**")
        st.info(f"**Response:** {st.session_state.survey_answers.get('biggest_positive_impact', 'Not answered')}")
        
        # Export functionality
        st.subheader("📤 Export Results")
        
        # JSON export
        survey_data = {
            "goal": "CCA Industry Council Pre-Workshop Survey",
            "data": st.session_state.survey_answers,
            "completed": True
        }
        
        json_str = json.dumps(survey_data, indent=2)
        st.download_button(
            label="📥 Download JSON Results",
            data=json_str,
            file_name="cca_survey_results.json",
            mime="application/json"
        )
        
        # Reset button
        if st.button("🔄 Start New Survey"):
            st.session_state.messages = []
            st.session_state.survey_answers = {}
            st.session_state.current_question = 0
            st.session_state.survey_completed = False
            st.rerun()

if __name__ == "__main__":
    main()
