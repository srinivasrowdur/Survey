import streamlit as st
import json
from typing import Dict, Any, List
import os
from dotenv import load_dotenv
from difflib import get_close_matches
import re

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
        "help": "Please select the trend that poses the biggest challenge for your organisation.",
        "keywords": {
            "Return to customer care": ["return", "customer care", "customer service", "care", "service"],
            "The super powered customer": ["super powered", "superpowered", "powered customer", "empowered", "customer power"],
            "Regulation for good": ["regulation", "regulatory", "compliance", "rules", "governance"],
            "Rise of the conscious consumer": ["conscious consumer", "conscious", "consumer awareness", "ethical", "sustainability"],
            "The agent of the future": ["agent", "future agent", "ai agent", "automation", "future"]
        }
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
        "help": "Please select the primary reason why this trend poses the biggest challenge.",
        "keywords": {
            "Financial impact": ["financial", "money", "cost", "budget", "economic", "funding"],
            "Workforce impact": ["workforce", "staff", "employees", "people", "team", "personnel"],
            "Skills and capability implications": ["skills", "capability", "training", "competency", "expertise", "knowledge"],
            "Organisational strategy implications": ["strategy", "organisational", "organizational", "planning", "direction", "approach"],
            "Something else": ["other", "else", "different", "not listed", "none of above"]
        }
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
        "help": "Please indicate your organisation's current level of readiness to address this challenge.",
        "keywords": {
            "Not at all": ["not at all", "not started", "nothing", "no progress", "haven't started"],
            "Still considering, but no actions yet": ["considering", "thinking", "planning", "no actions", "not yet"],
            "Being somewhat addressed across parts of the business": ["somewhat", "partially", "some parts", "in progress", "addressing"],
            "It's being fully addressed in the business": ["fully", "completely", "fully addressed", "implemented", "done"]
        }
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
        "help": "Please select the persona that poses the biggest challenge for your organisation.",
        "keywords": {
            "Future customer": ["customer", "client", "user", "consumer"],
            "Future frontline worker": ["frontline", "worker", "employee", "staff", "agent"],
            "Future leader": ["leader", "leadership", "management", "executive"]
        }
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
        "help": "Please select the primary factor that makes this persona challenging to satisfy.",
        "keywords": {
            "Budgetary constraints": ["budget", "money", "cost", "financial", "funding"],
            "Sourcing and location factors": ["sourcing", "location", "geographic", "recruitment", "hiring"],
            "Technological factors": ["technology", "tech", "digital", "systems", "platforms"],
            "Not in line with organisational strategy": ["strategy", "organisational", "organizational", "alignment", "direction"],
            "Skills and capability gaps": ["skills", "capability", "gaps", "training", "competency"],
            "Operating model": ["operating", "model", "processes", "operations"],
            "Organisational culture and leadership": ["culture", "leadership", "organisational", "organizational"],
            "Something else": ["other", "else", "different", "not listed"]
        }
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

We have three questions we'd like to get your input on. Please respond to each question as it appears.

💡 **Tip**: You can type your response naturally - I'll understand what you mean!"""
    
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
        
        content += "\n💡 **You can type naturally** - just describe your choice in your own words!"
    
    if question.get("help"):
        content += f"\n\n💡 **Help**: {question['help']}"
    
    return content

def intelligent_parse_answer(question, user_input):
    """Intelligently parse user input to match options"""
    if question["type"] == "text":
        return user_input.strip() if user_input.strip() else None
    
    user_input_lower = user_input.lower().strip()
    
    # First, try exact match (case insensitive)
    for option in question["options"]:
        if option.lower() == user_input_lower:
            return option
    
    # Try number input (1, 2, 3, etc.)
    try:
        num = int(user_input_lower)
        if 1 <= num <= len(question["options"]):
            return question["options"][num - 1]
    except ValueError:
        pass
    
    # Try fuzzy matching with keywords
    if "keywords" in question:
        best_match = None
        best_score = 0
        
        for option, keywords in question["keywords"].items():
            # Check if any keyword appears in user input
            for keyword in keywords:
                if keyword.lower() in user_input_lower:
                    # Calculate a simple score based on keyword match
                    score = len(keyword) / len(user_input_lower)
                    if score > best_score:
                        best_score = score
                        best_match = option
        
        if best_score > 0.3:  # Threshold for accepting a match
            return best_match
    
    # Try fuzzy string matching as fallback
    try:
        matches = get_close_matches(user_input_lower, [opt.lower() for opt in question["options"]], n=1, cutoff=0.6)
        if matches:
            # Find the original case version
            for option in question["options"]:
                if option.lower() == matches[0]:
                    return option
    except:
        pass
    
    return None

def validate_answer(question, answer):
    """Validate the user's answer using intelligent parsing"""
    parsed_answer = intelligent_parse_answer(question, answer)
    
    if parsed_answer is None:
        # Provide helpful suggestions
        if question["type"] == "choice":
            suggestions = []
            for i, option in enumerate(question["options"], 1):
                suggestions.append(f"• {i} or '{option}'")
            
            return None, f"I didn't quite understand that. You can:\n" + "\n".join(suggestions[:3]) + "\n\nOr just describe your choice in your own words!"
        else:
            return None, "Please provide a text response."
    
    return parsed_answer, None

def process_user_input(user_input):
    """Process the user's input and move to next question"""
    current_idx, current_question = get_next_question()
    
    if current_question is None:
        return
    
    # Validate the answer
    validated_answer, error_msg = validate_answer(current_question, user_input)
    
    if validated_answer is None:
        # Invalid answer, ask again with helpful suggestions
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        return
    
    # Save the answer
    st.session_state.survey_answers[current_question["id"]] = validated_answer
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Add confirmation message
    if current_question["type"] == "choice":
        confirmation = f"✅ I understood: **{validated_answer}**"
        st.session_state.messages.append({"role": "assistant", "content": confirmation})
    
    # Check if survey is complete
    next_idx, next_question = get_next_question()
    
    if next_question is None:
        # Survey completed
        st.session_state.survey_completed = True
        completion_message = """🎉 Thank you for completing the CCA Industry Council survey! Your input is invaluable to us.

Here's a summary of your responses:

"""
        for question in SURVEY_QUESTIONS:
            answer = st.session_state.survey_answers.get(question["id"])
            if answer:
                # Extract the main question text (before the first newline or emoji)
                question_text = question['question'].split('\n')[0].split('🔮')[0].split('👥')[0].split('🧠')[0]
                completion_message += f"**{question_text}** {answer}\n\n"
        
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
