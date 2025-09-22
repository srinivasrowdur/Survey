import streamlit as st
import json
from typing import Dict, Any, List, Optional, Tuple
import re
from difflib import get_close_matches
import openai
import os
import time
import streamlit.components.v1 as components
import asyncio
from agent import classify_where_they_work as agent_classify_where_they_work
from agent import classify_challenge as agent_classify_challenge
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Bot configuration
BOT_NAME = "ConferenceBot"

# Initialize session state
if "conference_messages" not in st.session_state:
    st.session_state.conference_messages = []

if "conference_data" not in st.session_state:
    st.session_state.conference_data = {}

if "conference_step" not in st.session_state:
    st.session_state.conference_step = "welcome"

if "conference_completed" not in st.session_state:
    st.session_state.conference_completed = False

# Pacing state for assistant messages
if "bot_queue" not in st.session_state:
    st.session_state.bot_queue = []
if "bot_delay" not in st.session_state:
    st.session_state.bot_delay = 1.5
if "bot_last_sent" not in st.session_state:
    st.session_state.bot_last_sent = 0.0
if "welcome_enqueued" not in st.session_state:
    st.session_state.welcome_enqueued = False
if "bot_stream_delay" not in st.session_state:
    st.session_state.bot_stream_delay = 0.02

# Initialize welcome messages (paced) if this is the first time
if (
    not st.session_state.conference_messages
    and st.session_state.conference_step == "welcome"
    and not st.session_state.welcome_enqueued
):
    welcome_messages = [
        f"Hello! Welcome to the Conference Preparation Bot. My name is {BOT_NAME}.",
        "I'm here to help us understand your sector, challenges, and planning status to make our upcoming conference as relevant and valuable as possible for you.",
        "This conversation will be completely confidential - none of what you tell me will be attributable to you personally.",
        "However, the collective feedback will provide valuable insights for all conference attendees.",
        "To get started, could you please tell me your name?"
    ]
    st.session_state.bot_queue.append("\n\n".join(welcome_messages))
    st.session_state.welcome_enqueued = True
    st.session_state.bot_last_sent = 0.0

# Sector definitions with keywords
SECTORS = {
    "Retail & E-commerce": {
        "keywords": ["retail", "order support", "bookings", "retail returns", "product enquiries", 
                    "loyalty programs", "online orders", "e-commerce", "ecommerce", "shopping"]
    },
    "Financial Services": {
        "keywords": ["banking", "banking queries", "fraud", "fraud detection", "loans", "applications", 
                    "insurance", "claims", "mortgages", "investments", "building societies", "finance", "financial",
                    "bank", "banks", "credit", "debit", "payment", "payments", "money", "cash", "currency",
                    "account", "accounts", "customer service", "customer support", "financial services", "fintech"]
    },
    "Telecommunications": {
        "keywords": ["telecoms", "billing", "billing queries", "technical support", "service upgrades", 
                    "mobiles", "services", "broadband", "internet", "telecom", "telecommunications"]
    },
    "Utilities": {
        "keywords": ["account management", "outage reporting", "billing", "payments", "water", "gas", 
                    "electricity", "domestic", "oil", "hardship", "utility", "utilities"]
    },
    "Public Sector & Government": {
        "keywords": ["benefits", "benefit support", "tax", "tax enquiries", "local council services", 
                    "NHS helplines", "NHS 111", "housing", "housing associations", "government", "public sector"]
    },
    "Healthcare": {
        "keywords": ["appointment booking", "prescription queries", "patient support", "private medical insurance", 
                    "care homes", "elderly care", "healthcare", "medical", "health", "hospital"]
    },
    "Travel & Hospitality": {
        "keywords": ["travel bookings", "travel cancellations", "loyalty programmes", "airline", "hotels", 
                    "accommodation", "trains", "bus operators", "highways agencies", "waterways", "travel", "hospitality"]
    },
    "Education": {
        "keywords": [
                    "new admissions", "universities", "student support", "alumni services", "schools",
                    "primary", "secondary", "clearing", "education", "educational", "university", "school",
                    "teacher", "teachers", "teaching", "tutor", "tutoring", "lecturer", "professor",
                    "faculty", "classroom", "college", "academy", "pe", "physical education"
        ]
    },
    "Technology & IT": {
        "keywords": ["software", "hardware", "PC", "IT support", "technical support", "service desk", 
                    "licence management", "subscription management", "technology", "IT", "tech"]
    },
    "Media & Entertainment": {
        "keywords": ["subscription services", "content access issues", "films", "sport", "cinema", "theatre", 
                    "booking", "pay per view", "games", "gaming", "media", "entertainment"]
    },
    "Outsourcing & BPO": {
        "keywords": ["offshore", "3rd party", "onshore", "outsourcing", "BPO", "business process"]
    },
    "Charities & non profits": {
        "keywords": ["donation support", "volunteer co-ordination", "helpline services", "charities", 
                    "non profit", "nonprofit", "charity", "voluntary", "donation"]
    },
    "Debt collection": {
        "keywords": ["payment reminders", "account resolution", "financial support", "distress", 
                    "hardship", "debt collection", "debt", "collections"]
    },
    "Emergency services": {
        "keywords": ["police", "fire service", "ambulance service", "motoring service", "coastguard", 
                    "emergency services", "emergency", "police", "fire", "ambulance"]
    }
}


# Challenge (Headwind) definitions with keywords
CHALLENGES = {
    "Economic volatility": {
        "keywords": ["ageing population", "economy", "uncertainty", "financial support", "distress", 
                    "hardship", "assistance", "economic", "volatility", "financial"]
    },
    "Technology acceleration": {
        "keywords": ["self-service", "human supported tech", "skilled", "skilling", "complex conversations", 
                    "cost", "technology", "acceleration", "tech", "digital", "automation"]
    },
    "Regulatory priorities": {
        "keywords": ["positive regulation", "driving better customer outcomes", "reduce customer harm", 
                    "evidence", "audit", "auditing", "payment process", "regulation for good", "regulatory", "compliance"]
    },
    "Sustainability agenda": {
        "keywords": ["reduce energy costs", "reduce carbon emissions", "environmental impact", 
                    "customer environmental buying choices", "society", "sustainability", "environmental", "carbon", "green"]
    },
    "Shifting workplace realities": {
        "keywords": ["multi-generational workplaces", "geographically diverse skill bases", "recruitment challenges", 
                    "pay expectations", "automation", "recruitment", "training and development", "talent retention", 
                    "agents", "workplace", "workforce", "skills"]
    }
}

def ai_match_sector(user_input: str) -> Tuple[Optional[str], List[str]]:
    """Use the project's agent (agent.py) to classify the user's sector."""
    try:
        # Ensure an event loop exists in Streamlit thread for agent runner
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        classification = agent_classify_where_they_work(user_input)
        # classification is a Pydantic object from agent.py
        if getattr(classification, "sector", None) == "Unknown":
            return None, []
        return getattr(classification, "sector", None), []
                
    except Exception as e:
        st.error(f"AI matching error: {str(e)}")
        return None, []

def find_sector_match(user_input: str) -> Tuple[Optional[str], List[str]]:
    """AI-only sector match. Requires OPENAI_API_KEY; no keyword fallback."""
    if not openai.api_key:
        st.error("AI agent not configured. Please set OPENAI_API_KEY.")
        return None, []
    return ai_match_sector(user_input)

def ai_match_challenge(user_input: str) -> Tuple[Optional[str], List[str]]:
    """Use the project's challenge agent to classify the user's challenge."""
    try:
        # Ensure an event loop exists in Streamlit thread for agent runner
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        classification = agent_classify_challenge(user_input)
        # Log and return
        category = getattr(classification, "category", None)
        if category == "Unknown":
            return None, []
        return category, []
    except Exception as e:
        st.error(f"AI matching error: {str(e)}")
        return None, []

def find_challenge_match(user_input: str) -> Tuple[Optional[str], List[str]]:
    """AI-only challenge match. Requires OPENAI_API_KEY; no keyword fallback."""
    if not openai.api_key:
        st.error("AI agent not configured. Please set OPENAI_API_KEY.")
        return None, []
    return ai_match_challenge(user_input)

def ai_validate_planning_scale(user_input: str) -> Optional[int]:
    """Use AI to intelligently parse planning scale input"""
    try:
        prompt = f"""You are helping to parse a user's response about their planning status on a scale of 0-10.

User input: "{user_input}"

Instructions:
- 0-4 means "preparation and planning" (not started, thinking about it, early planning)
- 5-10 means "execution" (implementing, in progress, nearly complete, finished)

Examples:
- "We're just starting to think about it" → 2
- "We're in the planning phase" → 3
- "We've started implementing" → 6
- "We're almost done" → 8
- "We haven't started" → 0
- "We're fully implemented" → 10

Return only a number from 0-10, or "INVALID" if you can't determine a clear number:"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        if result == "INVALID":
            return None
        
        # Try to extract number
        numbers = re.findall(r'\d+', result)
        if numbers:
            num = int(numbers[0])
            if 0 <= num <= 10:
                return num
        
        return None
                
    except Exception as e:
        st.error(f"AI parsing error: {str(e)}")
        return None

def validate_planning_scale(user_input: str) -> Optional[int]:
    """Validate and parse the planning scale input using AI"""
    # First try AI parsing
    ai_result = ai_validate_planning_scale(user_input)
    if ai_result is not None:
        return ai_result
    
    # Fallback to simple number extraction
    try:
        numbers = re.findall(r'\d+', user_input)
        if numbers:
            num = int(numbers[0])
            if 0 <= num <= 10:
                return num
    except ValueError:
        pass
    
    return None

def get_welcome_message() -> str:
    """Generate the initial welcome message"""
    return f"""Hello! Welcome to the Conference Preparation Bot. My name is {BOT_NAME}.

I'm here to help us understand your sector, challenges, and planning status to make our upcoming conference as relevant and valuable as possible for you.

This conversation will be completely confidential - none of what you tell me will be attributable to you personally. However, the collective feedback will provide valuable insights for all conference attendees.

To get started, could you please tell me your name?"""

def get_greeting_messages(name: str) -> List[str]:
    """Generate multiple personalized greeting messages for natural conversation flow"""
    return [
        f"Hi {name.upper()}, it's a pleasure to meet you!",
        "There are significant technology and socio-economic challenges ahead that we're all facing.",
        "You need to prepare and plan to address these challenges, but I recognise you may have already started on this journey.",
        f"We want to make the conference real and relevant to you {name.upper()}, and our conversation today will help us to establish where you are on the road.",
        "I would love to understand which challenges are most relevant to you and what you are focusing on now and for the future.",
        f"Don't worry {name.upper()}, none of what you tell me will be attributable, but collective feedback will give you insights to take away and help shape the conference.",
        f"Let's start! {name.upper()} can you tell me which sector you work in?"
    ]

def get_sector_confirmation_message(sector: str, name: str) -> str:
    """Generate sector confirmation message"""
    return f"""Thanks, so you work in {sector}, correct?"""

def get_sector_success_messages(name: str) -> List[str]:
    """Generate multiple messages after successful sector identification"""
    return [
        "Wow, tough gig! Thank you for updating me on the sector you work in.",
        "Now let's explore some of the challenges that lie ahead.",
        f"Ok thanks {name.upper()}, let's now talk more about the challenges ahead.",
        "Please can you describe the key challenge you face, we call these headwinds."
    ]

def get_challenge_confirmation_message(challenge: str, name: str) -> str:
    """Generate challenge confirmation message"""
    return f"""Thanks, so {challenge.lower()} is the key challenge you face. Please confirm: Yes or No."""

def get_challenge_success_messages(name: str) -> List[str]:
    """Generate multiple messages after successful challenge identification"""
    challenge = st.session_state.conference_data.get('challenge', 'this challenge')
    return [
        f"Thank you for telling me that your key challenge is {challenge}.",
        f"{name.upper()} let's now talk about how advanced you are in planning for the forecast headwind.",
        "It may be useful for me to update you on the detailed areas within your chosen technology and socio-economic headwind.",
        "I would now like to ask you how far down the road are you with planning and implementing a solution to the headwinds identified?",
        "On a scale of 0-10 where 0-4 is preparation and planning, and 5-10 is execution, where are you on your journey?"
    ]

def get_planning_followup_message(scale: int, name: str) -> str:
    """Generate follow-up message based on planning scale"""
    if scale <= 4:
        return f"""Thank you, {name.upper()} can you describe your challenge in more detail (up to 500 characters)"""
    else:
        return f"""Thank you, {name.upper()} Can you describe your challenge and your resolution plan in detail (up to 500 characters), including end to end how long will it take to resolve."""

def get_final_insights_message(name: str) -> str:
    """Generate message asking for additional insights"""
    return f"""Thank you very much for talking with me, just whilst we have been talking, is there anything else you have thought which you think may be relevant (don't be shy!)"""

def get_closing_message(name: str) -> str:
    """Generate the closing message"""
    return f"""Thank you very much {name.upper()} again for your time and we look forward to welcoming you at the conference"""

def add_bot_messages_with_delay(messages: List[str], delay: float = 1.5, combine: bool = True):
    """Queue bot messages with optional combination into a single streamed message.

    - delay: gap between messages (only applies when combine=False)
    - combine: when True, join messages into one block for a smoother UX
    """
    st.session_state.bot_delay = delay
    if combine:
        st.session_state.bot_queue.append("\n\n".join(messages))
    else:
        st.session_state.bot_queue.extend(messages)

def _token_stream(text: str):
    """Yield text progressively to simulate typing."""
    step = st.session_state.get("bot_stream_delay", 0.02)
    for ch in text:
        yield ch
        time.sleep(step)

def _tick_bot_delivery():
    """Deliver one queued bot message with typing stream and pacing, then rerun."""
    if st.session_state.bot_queue:
        delay = st.session_state.get("bot_delay", 1.5)
        last = st.session_state.get("bot_last_sent", 0.0)
        now = time.time()
        if last != 0.0:
            elapsed = now - last
            if elapsed < delay:
                time.sleep(delay - elapsed)
        next_message = st.session_state.bot_queue.pop(0)
        # Stream the assistant message live
        with st.chat_message("assistant", avatar="🤖"):
            st.write_stream(_token_stream(next_message))
        # Persist to history for next rerun
        st.session_state.conference_messages.append({"role": "assistant", "content": next_message})
        st.session_state.bot_last_sent = time.time()
        _scroll_to_bottom()
        st.rerun()

def _scroll_to_bottom():
    """Ensure the chat view scrolls to the latest message."""
    components.html(
        """
        <script>
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
        </script>
        """,
        height=0,
    )

def process_user_input(user_input: str):
    """Process user input based on current conversation step"""
    current_step = st.session_state.conference_step
    
    if current_step == "welcome":
        # Store the name and move to personalized greeting
        st.session_state.conference_data["name"] = user_input.strip()
        st.session_state.conference_messages.append({"role": "user", "content": user_input})
        
        # Add multiple greeting messages with natural flow
        greeting_messages = get_greeting_messages(st.session_state.conference_data["name"])
        add_bot_messages_with_delay(greeting_messages)
        st.session_state.conference_step = "sector_identification"
        
    elif current_step == "sector_identification":
        st.session_state.conference_messages.append({"role": "user", "content": user_input})
        
        # Try to find sector match
        sector_match, multiple_matches = find_sector_match(user_input)
        
        if sector_match:
            # AI returned a single sector; accept it and proceed without confirmation
            st.session_state.conference_data["sector"] = sector_match
            success_messages = get_sector_success_messages(st.session_state.conference_data["name"])
            add_bot_messages_with_delay(success_messages, combine=True)
            st.session_state.conference_step = "challenge_identification"
            
        elif multiple_matches:
            # Multiple matches found (kept for compatibility, though AI now returns one)
            matches_text = ", ".join(multiple_matches)
            suggestion = f"{st.session_state.conference_data['name'].upper()} could that be {matches_text}"
            st.session_state.conference_messages.append({"role": "assistant", "content": suggestion})
            st.session_state.conference_step = "sector_clarification"
            st.session_state.conference_data["pending_sector_options"] = multiple_matches
            
        else:
            # No match found, ask for clarification with examples
            clarification = f"I'm not sure I understand which sector you work in. Here are some examples of sectors I recognise:\n\n• **Financial Services** (banking, insurance, loans)\n• **Retail & E-commerce** (shopping, online orders)\n• **Healthcare** (hospitals, medical, patient care)\n• **Technology & IT** (software, technical support)\n• **Education** (schools, universities)\n• **Travel & Hospitality** (hotels, airlines, tourism)\n\nCould you tell me which sector you work in?"
            st.session_state.conference_messages.append({"role": "assistant", "content": clarification})
            
    elif current_step == "sector_confirmation":
        st.session_state.conference_messages.append({"role": "user", "content": user_input})
        
        if user_input.lower().strip() in ["yes", "y", "correct", "that's right", "right"]:
            # Confirm sector and move to challenge identification
            st.session_state.conference_data["sector"] = st.session_state.conference_data["pending_sector"]
            del st.session_state.conference_data["pending_sector"]
            
            success_messages = get_sector_success_messages(st.session_state.conference_data["name"])
            add_bot_messages_with_delay(success_messages, combine=True)
            st.session_state.conference_step = "challenge_identification"
        else:
            # Ask for sector again
            retry_message = f"Let me ask again - {st.session_state.conference_data['name'].upper()} can you tell me which sector you work in?"
            st.session_state.conference_messages.append({"role": "assistant", "content": retry_message})
            st.session_state.conference_step = "sector_identification"
            
    elif current_step == "sector_clarification":
        st.session_state.conference_messages.append({"role": "user", "content": user_input})
        
        # Try to match against the suggested options
        user_input_lower = user_input.lower().strip()
        matched_sector = None
        
        for sector in st.session_state.conference_data["pending_sector_options"]:
            if sector.lower() == user_input_lower or any(keyword.lower() in user_input_lower for keyword in SECTORS[sector]["keywords"]):
                matched_sector = sector
                break
        
        if matched_sector:
            st.session_state.conference_data["sector"] = matched_sector
            del st.session_state.conference_data["pending_sector_options"]
            
            success_messages = get_sector_success_messages(st.session_state.conference_data["name"])
            add_bot_messages_with_delay(success_messages, combine=True)
            st.session_state.conference_step = "challenge_identification"
        else:
            # Ask for sector again
            retry_message = f"Let me ask again - {st.session_state.conference_data['name'].upper()} can you tell me which sector you work in?"
            st.session_state.conference_messages.append({"role": "assistant", "content": retry_message})
            st.session_state.conference_step = "sector_identification"
            
    elif current_step == "challenge_identification":
        st.session_state.conference_messages.append({"role": "user", "content": user_input})
        
        # Try to find challenge match
        challenge_match, multiple_matches = find_challenge_match(user_input)
        
        if challenge_match:
            # Single match found
            confirmation = get_challenge_confirmation_message(challenge_match, st.session_state.conference_data["name"])
            st.session_state.conference_messages.append({"role": "assistant", "content": confirmation})
            st.session_state.conference_step = "challenge_confirmation"
            st.session_state.conference_data["pending_challenge"] = challenge_match
            
        elif multiple_matches:
            # Multiple matches found
            matches_text = " or ".join(multiple_matches)
            suggestion = f"{st.session_state.conference_data['name'].upper()} could that be {matches_text}"
            st.session_state.conference_messages.append({"role": "assistant", "content": suggestion})
            st.session_state.conference_step = "challenge_clarification"
            st.session_state.conference_data["pending_challenge_options"] = multiple_matches
            
        else:
            # No match found, ask for clarification
            clarification = "I'm not sure I understand which challenge you're referring to. Could you describe it in different words or mention specific aspects like technology, regulation, workforce, etc.?"
            st.session_state.conference_messages.append({"role": "assistant", "content": clarification})
            
    elif current_step == "challenge_confirmation":
        st.session_state.conference_messages.append({"role": "user", "content": user_input})
        
        if user_input.lower().strip() in ["yes", "y", "correct", "that's right", "right"]:
            # Confirm challenge and move to planning assessment
            st.session_state.conference_data["challenge"] = st.session_state.conference_data["pending_challenge"]
            del st.session_state.conference_data["pending_challenge"]
            
            success_messages = get_challenge_success_messages(st.session_state.conference_data["name"])
            add_bot_messages_with_delay(success_messages, combine=True)
            st.session_state.conference_step = "planning_assessment"
        else:
            # Ask for challenge again
            retry_message = "Please can you describe the key challenge you face, we call these headwinds"
            st.session_state.conference_messages.append({"role": "assistant", "content": retry_message})
            st.session_state.conference_step = "challenge_identification"
            
    elif current_step == "challenge_clarification":
        st.session_state.conference_messages.append({"role": "user", "content": user_input})
        
        # Try to match against the suggested options
        user_input_lower = user_input.lower().strip()
        matched_challenge = None
        
        for challenge in st.session_state.conference_data["pending_challenge_options"]:
            if challenge.lower() == user_input_lower or any(keyword.lower() in user_input_lower for keyword in CHALLENGES[challenge]["keywords"]):
                matched_challenge = challenge
                break
        
        if matched_challenge:
            st.session_state.conference_data["challenge"] = matched_challenge
            del st.session_state.conference_data["pending_challenge_options"]
            
            success_messages = get_challenge_success_messages(st.session_state.conference_data["name"])
            add_bot_messages_with_delay(success_messages, combine=True)
            st.session_state.conference_step = "planning_assessment"
        else:
            # Ask for challenge again
            retry_message = "Please can you describe the key challenge you face, we call these headwinds"
            st.session_state.conference_messages.append({"role": "assistant", "content": retry_message})
            st.session_state.conference_step = "challenge_identification"
            
    elif current_step == "planning_assessment":
        st.session_state.conference_messages.append({"role": "user", "content": user_input})
        
        # Validate planning scale
        scale = validate_planning_scale(user_input)
        
        if scale is not None:
            st.session_state.conference_data["planning_scale"] = scale
            followup_message = get_planning_followup_message(scale, st.session_state.conference_data["name"])
            st.session_state.conference_messages.append({"role": "assistant", "content": followup_message})
            st.session_state.conference_step = "planning_details"
        else:
            # Invalid input, ask again
            retry_message = "Please provide a number between 0 and 10, where 0-4 is preparation and planning, and 5-10 is execution."
            st.session_state.conference_messages.append({"role": "assistant", "content": retry_message})
            
    elif current_step == "planning_details":
        st.session_state.conference_messages.append({"role": "user", "content": user_input})
        
        # Store the planning details
        if len(user_input) > 500:
            user_input = user_input[:500] + "..."
        
        st.session_state.conference_data["planning_details"] = user_input
        
        # Move to final insights
        insights_message = get_final_insights_message(st.session_state.conference_data["name"])
        st.session_state.conference_messages.append({"role": "assistant", "content": insights_message})
        st.session_state.conference_step = "final_insights"
        
    elif current_step == "final_insights":
        st.session_state.conference_messages.append({"role": "user", "content": user_input})
        
        # Store final insights
        if len(user_input) > 500:
            user_input = user_input[:500] + "..."
        
        st.session_state.conference_data["final_insights"] = user_input
        
        # Complete the conversation
        closing_message = get_closing_message(st.session_state.conference_data["name"])
        st.session_state.conference_messages.append({"role": "assistant", "content": closing_message})
        st.session_state.conference_completed = True

def main():
    st.set_page_config(
        page_title="Conference Bot",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 Conference Preparation Bot")
    st.markdown("---")
    # Keep chat input fixed at the bottom and reserve space to avoid overlap
    st.markdown(
        """
        <style>
        section.main > div.block-container { padding-bottom: 120px; }
        div[data-testid="stChatInput"] {
            position: fixed;
            left: 0; right: 0; bottom: 0;
            padding: 0.5rem 1rem;
            background: inherit;
            backdrop-filter: blur(6px);
            border-top: 1px solid rgba(250,250,250,0.12);
            z-index: 1000;
        }
        .typing-bar {
            position: fixed;
            left: 0; right: 0; bottom: 0;
            display: flex; align-items: center; gap: 8px;
            padding: 0.75rem 1rem;
            background: inherit;
            backdrop-filter: blur(6px);
            border-top: 1px solid rgba(250,250,250,0.12);
            z-index: 1000;
            font-weight: 500;
        }
        .typing-dot {
            width: 8px; height: 8px; border-radius: 50%;
            background: currentColor; opacity: 0.6;
            animation: blink 1.4s infinite both;
        }
        .typing-dot:nth-child(2) { animation-delay: .2s; }
        .typing-dot:nth-child(3) { animation-delay: .4s; }
        @keyframes blink {
            0% { opacity: 0.2; }
            20% { opacity: 1; }
            100% { opacity: 0.2; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    # Display chat messages using Streamlit's chat UI with avatars
    for message in st.session_state.conference_messages:
        role = message["role"]
        avatar = "🤖" if role == "assistant" else "🙋"
        with st.chat_message(role, avatar=avatar):
            st.markdown(message["content"])
    
    # Auto-scroll to latest after rendering
    _scroll_to_bottom()

    # Production: hide debug UI

    # If there are queued bot messages, deliver them progressively after rendering
    if st.session_state.bot_queue and not st.session_state.conference_completed:
        st.markdown(
            """
            <div class="typing-bar">
                Assistant is typing…
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        _tick_bot_delivery()
        return
    
    
    # Chat input
    if not st.session_state.conference_completed:
        # Only allow input when the bot is not mid-delivery
        if st.session_state.bot_queue:
            # Replace input with typing bar at bottom
            st.markdown(
                """
                <div class=\"typing-bar\"> 
                    Assistant is typing…
                    <span class=\"typing-dot\"></span>
                    <span class=\"typing-dot\"></span>
                    <span class=\"typing-dot\"></span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            return
        if st.session_state.conference_step == "welcome":
            prompt = st.chat_input("Please type in your name...")
        else:
            prompt = st.chat_input("Type your response here...")
        
        if prompt:
            process_user_input(prompt)
            st.rerun()
    else:
        st.success("✅ Conference preparation conversation completed! Thank you for your participation.")
        
        # Display results summary
        st.subheader("📋 Your Conference Preparation Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Participant Information**")
            st.info(f"**Name:** {st.session_state.conference_data.get('name', 'Not provided')}")
            st.info(f"**Sector:** {st.session_state.conference_data.get('sector', 'Not provided')}")
            st.info(f"**Key Challenge:** {st.session_state.conference_data.get('challenge', 'Not provided')}")
        
        with col2:
            st.markdown("**Planning Status**")
            planning_scale = st.session_state.conference_data.get('planning_scale', 'Not provided')
            if isinstance(planning_scale, int):
                if planning_scale <= 4:
                    status = "Preparation and Planning"
                else:
                    status = "Execution"
                st.info(f"**Scale:** {planning_scale}/10 ({status})")
            else:
                st.info(f"**Scale:** {planning_scale}")
        
        st.markdown("**Planning Details**")
        st.info(f"**Response:** {st.session_state.conference_data.get('planning_details', 'Not provided')}")
        
        st.markdown("**Additional Insights**")
        st.info(f"**Response:** {st.session_state.conference_data.get('final_insights', 'Not provided')}")
        
        # Export functionality
        st.subheader("📤 Export Results")
        
        # JSON export
        conference_data = {
            "goal": "Conference Preparation Survey",
            "data": st.session_state.conference_data,
            "completed": True
        }
        
        json_str = json.dumps(conference_data, indent=2)
        st.download_button(
            label="📥 Download JSON Results",
            data=json_str,
            file_name="conference_preparation_results.json",
            mime="application/json"
        )
        
        # Reset button
        if st.button("🔄 Start New Conversation"):
            st.session_state.conference_messages = []
            st.session_state.conference_data = {}
            st.session_state.conference_step = "welcome"
            st.session_state.conference_completed = False
            st.rerun()

if __name__ == "__main__":
    main()

