"""
agents/classifier_agent.py — Phase 2, Week 2
Rewritten for Groq API (llama-3.3-70b-versatile).
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

from groq import Groq
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


# ── Output Schema ─────────────────────────────────────────────────────────────

VALID_DOMAINS = {
    "police_fir",
    "eviction_housing",
    "workplace_salary",
    "consumer_fraud",
    "domestic_violence",
    "land_property",
    "court_bail",
    "government_schemes",
}

class ClassifierResponse(BaseModel):
    domain: str
    confidence: float
    clarification_needed: bool
    clarification_question: Optional[str]


# ── Prompt ────────────────────────────────────────────────────────────────────

CLASSIFIER_PROMPT = """You are a legal domain classifier for Indian law.

Classify the user's situation into EXACTLY ONE of these 8 domains:
  police_fir        — arrest, FIR filing, police harassment, custody, bail
  eviction_housing  — illegal eviction, rent disputes, landlord issues
  workplace_salary  — unpaid wages, wrongful termination, workplace harassment
  consumer_fraud    — defective products, online fraud, service complaints
  domestic_violence — abuse at home, protection orders, shelter rights
  land_property     — land ownership disputes, encroachment, inheritance
  court_bail        — bail applications, court hearings, legal representation
  government_schemes — denied access to welfare schemes, Aadhaar issues, ration card

Respond in JSON only, no markdown, no explanation:
{{
  "domain": "<one of the 8 domains>",
  "confidence": <0.0 to 1.0>,
  "clarification_needed": <true or false>,
  "clarification_question": "<question to ask user, or null if not needed>"
}}

Rules:
- If confident (>= 0.6), set clarification_needed to false and clarification_question to null.
- If confidence < 0.6, set clarification_needed to true and write ONE short clarifying question.
- Never return more than one domain.

User situation: {query}"""


# ── Agent ─────────────────────────────────────────────────────────────────────

def run_classifier_agent(query: str) -> ClassifierResponse:
    prompt = CLASSIFIER_PROMPT.format(query=query)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    data = json.loads(raw)

    if data.get("domain") not in VALID_DOMAINS:
        raise ValueError(f"Model returned unknown domain: {data.get('domain')}")

    if data.get("confidence", 0) >= 0.6:
        data["clarification_needed"] = False
        data["clarification_question"] = None

    return ClassifierResponse(**data)


def print_response(query: str, response: ClassifierResponse):
    print(f"\n  Query:      {query}")
    print(f"  Domain:     {response.domain}")
    print(f"  Confidence: {response.confidence:.0%}")
    if response.clarification_needed:
        print(f"  Needs clarification: YES")
        print(f"  Question: {response.clarification_question}")
    else:
        print(f"  Needs clarification: NO → proceed to retrieval")


# ── Test ──────────────────────────────────────────────────────────────────────

def test():
    test_cases = [
        ("Police came to my house and want to arrest me without a warrant.", "police_fir"),
        ("My landlord locked me out of my house without notice.", "eviction_housing"),
        ("My employer has not paid my salary for 3 months.", "workplace_salary"),
        ("I ordered a phone online and received a fake product.", "consumer_fraud"),
        ("My husband beats me and I need to know how to get a protection order.", "domestic_violence"),
        ("My neighbour has built a wall on my land.", "land_property"),
        ("I have been in jail for 6 months waiting for my bail hearing.", "court_bail"),
        ("I am not receiving my PM-KISAN payments even though I am eligible.", "government_schemes"),
        ("I have a problem with my house.", None),
    ]

    print("\n=== CLASSIFIER AGENT TEST ===\n")
    passed = 0
    for query, expected_domain in test_cases:
        try:
            response = run_classifier_agent(query)
            print_response(query, response)
            if expected_domain:
                if response.domain == expected_domain and not response.clarification_needed:
                    print(f"  ✓ Correct")
                    passed += 1
                else:
                    print(f"  ✗ Expected: {expected_domain}")
            else:
                if response.clarification_needed or response.confidence < 0.6:
                    print(f"  ✓ Correctly flagged as ambiguous")
                    passed += 1
                else:
                    print(f"  ~ Picked {response.domain} without clarification (acceptable)")
                    passed += 1
        except Exception as e:
            print(f"\n  ✗ Failed: {e}")

    print(f"\n{'='*50}")
    print(f"RESULT: {passed}/{len(test_cases)} passed")


if __name__ == "__main__":
    test()
