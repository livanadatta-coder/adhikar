"""
agents/forms_agent.py — Phase 2, Week 2
The "Forms & Documents" agent.

Looks up relevant forms from forms_db.json by domain.
LLM is only used for edge cases not covered by the database.

This agent is intentionally simpler than Rights/Actions —
most legal form lookups don't need an LLM, just a good database.

Run directly to test:
    python agents/forms_agent.py
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

# ── Path to forms database ────────────────────────────────────────────────────
FORMS_DB_PATH = Path(__file__).parent.parent / "data" / "forms_db.json"


# ── Output Schema ─────────────────────────────────────────────────────────────

class Form(BaseModel):
    name: str
    purpose: str
    where_to_get: str
    url: Optional[str]
    notes: Optional[str]


class FormsResponse(BaseModel):
    domain: str
    forms: list[Form]   # 0–3 most relevant forms
    disclaimer: str
    sources: list[str]


# ── Database loader ───────────────────────────────────────────────────────────

def load_forms_db() -> dict:
    if not FORMS_DB_PATH.exists():
        raise FileNotFoundError(
            f"forms_db.json not found at {FORMS_DB_PATH}. "
            "Copy it to data/forms_db.json first."
        )
    with open(FORMS_DB_PATH, encoding="utf-8") as f:
        return json.load(f)


# ── LLM fallback prompt (only used when DB has no match) ─────────────────────

FORMS_FALLBACK_PROMPT = """
You are an Indian legal forms expert.

The user has a legal situation in the domain: {domain}
Their specific situation: {query}

List the 1-3 most relevant official forms or documents they need.
Only include real forms that exist in Indian law.

Respond in JSON only:
{{
  "forms": [
    {{
      "name": "exact official name of the form or document",
      "purpose": "what this form is for in one sentence",
      "where_to_get": "exactly where to get this form",
      "url": "official URL if you know it, otherwise null",
      "notes": "one practical tip for filling or submitting, or null"
    }}
  ]
}}
"""


# ── Agent ─────────────────────────────────────────────────────────────────────

def run_forms_agent(query: str, domain: str, state: Optional[str] = None) -> FormsResponse:
    db = load_forms_db()

    # Primary path: database lookup
    domain_forms = db.get(domain, [])

    if domain_forms:
        # Return top 3 most relevant forms for this domain
        # In v2 this could be smarter (query-based ranking)
        # For now, first 3 in the database are already ordered by importance
        selected = domain_forms[:3]
        forms = [Form(**f) for f in selected]
        sources = [f["name"] for f in selected]

        return FormsResponse(
            domain=domain,
            forms=forms,
            disclaimer="This is legal information, not legal advice. For your specific situation, consult a lawyer or contact NALSA helpline at 15100.",
            sources=sources
        )

    # Fallback path: LLM (only if domain not in DB — shouldn't happen in production)
    print(f"  [forms_agent] Domain '{domain}' not in DB — falling back to LLM")
    prompt = FORMS_FALLBACK_PROMPT.format(domain=domain, query=query)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content.strip()
    data = json.loads(raw)

    forms = [Form(**f) for f in data.get("forms", [])]
    return FormsResponse(
        domain=domain,
        forms=forms,
        disclaimer="This is legal information, not legal advice. For your specific situation, consult a lawyer or contact NALSA helpline at 15100.",
        sources=[f.name for f in forms]
    )


def print_response(response: FormsResponse):
    print("\n" + "="*60)
    print("FORMS & DOCUMENTS")
    print("="*60)
    if not response.forms:
        print("\n  No specific forms required for this situation.")
    for i, form in enumerate(response.forms, 1):
        print(f"\n{i}. {form.name}")
        print(f"   What it's for: {form.purpose}")
        print(f"   Where to get it: {form.where_to_get}")
        if form.url:
            print(f"   Link: {form.url}")
        if form.notes:
            print(f"   Tip: {form.notes}")
    print(f"\n⚠  {response.disclaimer}")


# ── Test ──────────────────────────────────────────────────────────────────────

def test():
    test_cases = [
        {"query": "Police are refusing to file my FIR.", "domain": "police_fir"},
        {"query": "My landlord is illegally evicting me.", "domain": "eviction_housing"},
        {"query": "My employer has not paid my salary.", "domain": "workplace_salary"},
        {"query": "I received a fake product online.", "domain": "consumer_fraud"},
        {"query": "I am being abused at home.", "domain": "domestic_violence"},
        {"query": "My neighbour is encroaching on my land.", "domain": "land_property"},
        {"query": "I need to apply for bail.", "domain": "court_bail"},
        {"query": "I am not receiving my PM-KISAN payments.", "domain": "government_schemes"},
    ]

    print("\n=== FORMS AGENT TEST ===\n")
    passed = 0
    for i, tc in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i} [{tc['domain']}]: {tc['query']}")
        try:
            response = run_forms_agent(tc["query"], tc["domain"])
            print_response(response)
            assert len(response.forms) > 0, "No forms returned"
            assert response.disclaimer, "Missing disclaimer"
            print(f"\n✓ Test {i} passed — {len(response.forms)} forms returned (DB lookup, no API call)")
            passed += 1
        except Exception as e:
            print(f"\n✗ Test {i} failed: {e}")

    print(f"\n{'='*60}")
    print(f"RESULT: {passed}/{len(test_cases)} passed")


if __name__ == "__main__":
    test()
