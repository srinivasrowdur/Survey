# adaptive_survey_agent.py
# pip install openai-agents pydantic python-dotenv

from __future__ import annotations
from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field, ValidationError, constr
import re
import os
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, enable_verbose_stdout_logging

# Load environment variables from .env file
load_dotenv()

# ---------- Domain models ----------

class Question(BaseModel):
    field_id: str = Field(..., description="Unique field key to populate in answers.")
    prompt: str = Field(..., description="What to ask the user, in UK English.")
    kind: Literal["text", "email", "integer", "choice"] = "text"
    options: Optional[List[str]] = None
    validation_regex: Optional[str] = None
    required: bool = True
    help: Optional[str] = None
    depends_on: Optional[str] = None  # Field this question depends on
    depends_value: Optional[str] = None  # Value that triggers this question

class SurveyGoal(BaseModel):
    name: str
    # Ordered "slots" the agent should fill. The LLM can reorder dynamically if it wishes.
    slots: List[Question]

class SurveyState(BaseModel):
    goal: SurveyGoal
    answers: Dict[str, Any] = {}
    completed: bool = False

    def missing_slots(self) -> List[Question]:
        # Filter questions based on dependencies
        available_questions = []
        for q in self.goal.slots:
            if q.required and q.field_id not in self.answers:
                # Check if this question depends on another answer
                if q.depends_on and q.depends_value:
                    if (q.depends_on in self.answers and 
                        (q.depends_value.lower() == "any" or 
                         str(self.answers[q.depends_on]).lower() == q.depends_value.lower())):
                        available_questions.append(q)
                elif not q.depends_on:
                    available_questions.append(q)
        return available_questions

# ---------- In-memory store (per process demo) ----------
STATE: Dict[str, SurveyState] = {}  # session_id -> SurveyState


# ---------- Tools exposed to the LLM ----------

@function_tool
def get_state_summary(session_id: str) -> dict:
    """
    Return a summary of what's been captured and what's missing.
    """
    s = STATE[session_id]
    return {
        "goal": s.goal.name,
        "captured": list(s.answers.keys()),
        "missing": [q.field_id for q in s.missing_slots()],
    }

@function_tool
def ask_user(session_id: str, question: Question) -> str:
    """
    Present a question to the human and return their input.
    For demo: blocks on stdin. Replace with your chat/IVR/web UI transport in production.
    """
    print("\n" + ("-" * 60))
    print(f"Question ({question.field_id}): {question.prompt}")
    if question.kind == "choice" and question.options:
        print("Options:", ", ".join(question.options))
    if question.help:
        print(f"Help: {question.help}")
    resp = input("> ").strip()
    return resp

@function_tool
def save_answer(session_id: str, field_id: str, raw_value: str, kind: str = "text",
                validation_regex: Optional[str] = None,
                options: Optional[List[str]] = None) -> dict:
    """
    Validate & persist the user's answer against the expected type/options.
    Returns {ok: bool, error?: str, value?: any}.
    """
    s = STATE[session_id]

    # Basic validation by kind
    try:
        if kind == "email":
            # Use a simple regex for email validation instead of EmailStr
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.fullmatch(email_pattern, raw_value):
                raise ValueError("Please enter a valid email address.")
            value = raw_value
        elif kind == "integer":
            if not re.fullmatch(r"[+-]?\d+", raw_value):
                raise ValueError("Please enter a whole number.")
            value = int(raw_value)
        elif kind == "choice":
            if not options:
                raise ValueError("No options were provided to validate against.")
            match = [opt for opt in options if opt.lower() == raw_value.lower()]
            if not match:
                raise ValueError(f"Please choose one of: {', '.join(options)}")
            value = match[0]
        else:
            value = raw_value

        if validation_regex and not re.fullmatch(validation_regex, str(value)):
            raise ValueError("That doesn't match the expected format.")

        s.answers[field_id] = value
        s.completed = len(s.missing_slots()) == 0
        return {"ok": True, "value": value, "completed": s.completed}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@function_tool
def emit_final_payload(session_id: str) -> dict:
    """
    Returns the final JSON payload once all required fields are captured.
    """
    s = STATE[session_id]
    return {
        "goal": s.goal.name,
        "data": s.answers,
        "completed": s.completed
    }

# ---------- Build the agent ----------

def build_agent() -> Agent:
    """
    Creates an agent that:
      1) Plans which question to ask next to satisfy the goal schema.
      2) Calls ask_user() to collect answers.
      3) Calls save_answer() to validate & persist.
      4) Repeats until all required slots are filled, then returns emit_final_payload().
    """
    SYSTEM_INSTRUCTIONS = """
You are an adaptive survey agent for the CCA Industry Council. Your objective is to COMPLETE the user's survey
by capturing all required responses with high data quality.

CRITICAL RULES:
- ALWAYS use the EXACT questions and options defined in the survey schema - do NOT create your own questions
- Always inspect the current state via get_state_summary() at the start
- Follow the survey flow logically - ask main questions first, then follow-up questions based on responses
- Ask the questions exactly as written in the prompt field - do not rephrase or simplify them
- For choice questions: show options exactly as defined - do not add, remove, or modify options
- Immediately validate & persist using save_answer(). If validation fails, politely re-ask
- Once ALL required slots are captured, call emit_final_payload() and STOP

IMPORTANT: You must use the exact field IDs from the survey schema:
- biggest_challenge
- challenge_reason  
- organisational_readiness
- most_challenging_persona
- persona_challenge_factor
- biggest_positive_impact

Do NOT create new field IDs or modify the existing ones.

Survey Flow:
1. Ask about the biggest challenge from the five trends (Return to customer care, The super powered customer, Regulation for good, Rise of the conscious consumer, The agent of the future)
2. Ask follow-up about why (Financial impact, Workforce impact, Skills and capability implications, Organisational strategy implications, Something else)
3. Ask about current organisational readiness (Not at all, Still considering but no actions yet, Being somewhat addressed across parts of the business, It's being fully addressed in the business)
4. Ask about the most challenging persona (Future customer, Future frontline worker, Future leader)
5. Ask follow-up about the biggest factor influencing this (Budgetary constraints, Sourcing and location factors, Technological factors, Not in line with organisational strategy, Skills and capability gaps, Operating model, Organisational culture and leadership, Something else)
6. Ask the open-ended question about biggest positive impact factor

Tone:
- Professional, engaging, and conversational. Use UK English.
- Be empathetic and acknowledge the value of their input for the Industry Council.
- Use the exact wording from the survey questions - do not paraphrase.
"""

    return Agent(
        name="CCA Industry Council Survey Agent",
        instructions=SYSTEM_INSTRUCTIONS,
        tools=[get_state_summary, ask_user, save_answer, emit_final_payload],
        # Optionally pin a model or let the SDK default (Responses API-capable model).
        # model="gpt-5.1"  # example; set to your available model
    )

# ---------- Demo harness ----------

def main():
    enable_verbose_stdout_logging()  # optional: see the loop & tool calls in the console

    # Define the CCA Industry Council survey
    goal = SurveyGoal(
        name="CCA Industry Council Pre-Workshop Survey",
        slots=[
            # Question 1: Biggest challenge from five trends
            Question(
                field_id="biggest_challenge",
                prompt="We have identified five key trends and their implications for the customer contact sector over the next five years. Which do you see as posing the biggest challenges for your organisation?\n\n1. Return to customer care\n2. The super powered customer\n3. Regulation for good\n4. Rise of the conscious consumer\n5. The agent of the future",
                kind="choice",
                options=["Return to customer care", "The super powered customer", "Regulation for good", "Rise of the conscious consumer", "The agent of the future"],
                help="Please select the trend that poses the biggest challenge for your organisation."
            ),
            
            # Question 1a: Why is that? (depends on biggest_challenge being answered)
            Question(
                field_id="challenge_reason",
                prompt="Why is that the biggest challenge for your organisation?",
                kind="choice",
                options=["Financial impact", "Workforce impact", "Skills and capability implications", "Organisational strategy implications", "Something else"],
                help="Please select the primary reason why this trend poses the biggest challenge.",
                depends_on="biggest_challenge",
                depends_value="any"  # Will be answered regardless of the choice
            ),
            
            # Question 1b: Current organisational readiness
            Question(
                field_id="organisational_readiness",
                prompt="To what extent is your organisation already looking into addressing this challenge?",
                kind="choice",
                options=["Not at all", "Still considering, but no actions yet", "Being somewhat addressed across parts of the business", "It's being fully addressed in the business"],
                help="Please indicate your organisation's current level of readiness to address this challenge."
            ),
            
            # Question 2: Most challenging persona
            Question(
                field_id="most_challenging_persona",
                prompt="With Industry Council input, we have defined three personas: Future Customer, Future Frontline Worker, and Future Leader.\n\n🔮 Future Customer: Empowered, digitally fluent individuals seeking personalised, empathetic and ethical experiences across channels.\n\n👥 Future Frontline Worker: Tech-savvy, emotionally intelligent professionals thriving in flexible, inclusive, and purpose-driven environments.\n\n🧠 Future Leader: Emotionally intelligent change-makers who lead with purpose, adaptability, and a people-first mindset.\n\nWhich of these personas do you see as being most challenging to satisfy within your organisation?",
                kind="choice",
                options=["Future customer", "Future frontline worker", "Future leader"],
                help="Please select the persona that poses the biggest challenge for your organisation."
            ),
            
            # Question 2a: Biggest factor influencing this (depends on most_challenging_persona being answered)
            Question(
                field_id="persona_challenge_factor",
                prompt="What is the biggest factor influencing this challenge?",
                kind="choice",
                options=["Budgetary constraints", "Sourcing and location factors", "Technological factors", "Not in line with organisational strategy", "Skills and capability gaps", "Operating model", "Organisational culture and leadership", "Something else"],
                help="Please select the primary factor that makes this persona challenging to satisfy.",
                depends_on="most_challenging_persona",
                depends_value="any"  # Will be answered regardless of the choice
            ),
            
            # Question 3: Open-ended question
            Question(
                field_id="biggest_positive_impact",
                prompt="Please tell us what you see as the factor that would have the biggest positive impact on your organisation's ability to respond effectively to the future customer/employee needs set out here?",
                kind="text",
                help="Please provide your thoughts on what would have the biggest positive impact."
            ),
        ]
    )

    # Start state for a (simulated) session:
    session_id = "cca-council-session-001"
    STATE[session_id] = SurveyState(goal=goal)

    agent = build_agent()

    # Kick off the run with a short instruction. The agent will do the rest by calling tools.
    result = Runner.run_sync(
        agent,
        f"Session ID is '{session_id}'. Please begin the CCA Industry Council survey and finish when the goal is complete.",
        max_turns=20  # Increase max turns to allow completion
    )

    print("\n" + "=" * 60)
    print("FINAL OUTPUT:")
    print(result.final_output)  # The model's final message (should reflect completion)
    # Also fetch the structured payload via the tool:
    print("\nSTRUCTURED PAYLOAD:")
    # Get the final payload directly from the state
    s = STATE[session_id]
    final_payload = {
        "goal": s.goal.name,
        "data": s.answers,
        "completed": s.completed
    }
    print(final_payload)

if __name__ == "__main__":
    # Ensure your API key is set: export OPENAI_API_KEY=sk-...
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Please set OPENAI_API_KEY environment variable.")
    main()
