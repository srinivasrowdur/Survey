# sector_agent_openai.py
# pip install openai-agents pydantic

from typing import Literal
from pydantic import BaseModel, Field
from agents import Agent, Runner
import dotenv

dotenv.load_dotenv()


# 1) Strict label space for sectors
Sector = Literal[
    "Retail & E-commerce",
    "Financial Services",
    "Telecommunications",
    "Utilities",
    "Public Sector & Government",
    "Healthcare",
    "Travel & Hospitality",
    "Education",
    "Technology & IT",
    "Media & Entertainment",
    "Outsourcing & BPO",
    "Charities & Non-profits",
    "Debt collection",
    "Emergency services",
    "Unknown",
]


# 2) Structured output schema enforced by Structured Outputs
class Classification(BaseModel):
    sector: Sector = Field(..., description="One of the predefined sectors or 'Unknown'.")
    confidence: int = Field(..., ge=0, le=100, description="0–100 confidence score.")
    rationale: str = Field(..., min_length=5, max_length=240, description="Brief reason for the mapping.")


# 3) System instructions with your sector keywords (UK English)
SYSTEM_INSTRUCTIONS = """
You are a classification assistant. Map a user's free-text description of where they work to ONE sector from the list.
If multiple could apply, pick the single best match. If none apply, return "Unknown".
Use the indicative keywords as clues, but apply common sense (e.g., "Tesco returns" → Retail & E-commerce).
Respond ONLY via the defined structured JSON schema.

Sectors and indicative keywords:

1. Retail & E-commerce — retail, order support, bookings, returns, product enquiries, loyalty programmes, online orders
2. Financial Services — banking, banking queries, fraud, fraud detection, loans, applications, insurance, claims, mortgages, investments, building societies
3. Telecommunications — telecoms, billing, billing queries, technical support, service upgrades, mobiles, services, broadband, internet
4. Utilities — account management, outage reporting, billing, payments, water, gas, electricity, domestic, oil, hardship
5. Public Sector & Government — benefits, benefit support, tax, tax enquiries, local council services, NHS helplines, NHS 111, housing, housing associations
6. Healthcare — appointment booking, prescription queries, patient support, private medical insurance, care homes, elderly care
7. Travel & Hospitality — travel bookings, travel cancellations, loyalty programmes, airline, hotels, accommodation, trains, bus operators, highways agencies, waterways
8. Education — new admissions, universities, student support, alumni services, schools, primary, secondary, clearing
9. Technology & IT — software, hardware, PC, IT support, technical support, service desk, licence management, subscription management
10. Media & Entertainment — subscription services, content access issues, films, sport, cinema, theatre, booking, pay per view, games, gaming
11. Outsourcing & BPO — offshore, 3rd party, onshore
12. Charities & Non-profits — donation support, volunteer co-ordination, helpline services
13. Debt collection — payment reminders, account resolution, financial support, distress, hardship
14. Emergency services — police, fire service, ambulance service, motoring service, coastguard
"""


def build_agent(model_id: str = "gpt-4o-mini"):
    """
    Creates an OpenAI Agent with Structured Outputs.
    The Agents SDK will keep looping until it gets a valid Classification object. 
    """
    return Agent(
        name="SectorClassifier",
        model=model_id,                 # any Responses API model ID works here               # deterministic classification
        instructions=SYSTEM_INSTRUCTIONS.strip(),
        output_type=Classification,     # <- Structured Outputs enforced
    )


def classify_where_they_work(user_text: str, model_id: str = "gpt-4o-mini") -> Classification:
    agent = build_agent(model_id=model_id)
    result = Runner.run_sync(agent, input=user_text)
    # final_output is already a parsed Pydantic object when output_type is set
    return result.final_output


# ------------------------------ Challenge Agent ------------------------------

# Strict label space for challenge categories
ChallengeCategory = Literal[
    "Economic volatility",
    "Technology acceleration",
    "Regulatory priorities",
    "Sustainability agenda",
    "Shifting workplace realities",
    "Unknown",
]


class ChallengeClassification(BaseModel):
    category: ChallengeCategory = Field(..., description="One of the predefined challenge categories or 'Unknown'.")
    confidence: int = Field(..., ge=0, le=100, description="0–100 confidence score.")
    rationale: str = Field(..., min_length=5, max_length=240, description="Brief reason for the mapping.")


CHALLENGE_SYSTEM_INSTRUCTIONS = """
You are a classification assistant. Map a user's free-text description of their key challenge to ONE category from the list.
If multiple could apply, pick the single best match. If none apply, return "Unknown".
Respond ONLY via the defined structured JSON schema.

Challenge categories and indicative keywords:

1. Economic volatility — ageing population, economy, uncertainty, financial support, distress, hardship, assistance
2. Technology acceleration — self-service, human supported tech, skilled, skilling, complex conversations, cost
3. Regulatory priorities — positive regulation, driving better customer outcomes, reduce customer harm, evidence, audit, auditing, payment process, regulation for good
4. Sustainability agenda — reduce energy costs, reduce carbon emissions, environmental impact, customer environmental buying choices, society
5. Shifting workplace realities — multi-generational workplaces, geographically diverse skill bases, recruitment challenges, pay expectations, automation, recruitment, training and development, talent retention, agents
""".strip()


def build_challenge_agent(model_id: str = "gpt-4o-mini"):
    return Agent(
        name="ChallengeClassifier",
        model=model_id,
        instructions=CHALLENGE_SYSTEM_INSTRUCTIONS,
        output_type=ChallengeClassification,
    )


def classify_challenge(user_text: str, model_id: str = "gpt-4o-mini") -> ChallengeClassification:
    agent = build_challenge_agent(model_id=model_id)
    result = Runner.run_sync(agent, input=user_text)
    return result.final_output


# CLI demo
if __name__ == "__main__":
    examples = [
        "I work at Tesco in the customer returns team.",
        "Mortgage applications at a building society.",
        "I handle outage reporting for a gas & electricity provider.",
        "Fire and rescue service dispatcher.",
        "We run a SaaS service desk doing licence management for PCs.",
        "I am a primary school teacher",
        "No idea what this maps to."
    ]
    for txt in examples:
        out = classify_where_they_work(txt)
        print(f"\nInput: {txt}\nSector: {out.sector}\nConfidence: {out.confidence}\nRationale: {out.rationale}")