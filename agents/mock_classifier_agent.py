"""
agents/mock_classifier_agent.py — Week 2 Dev Tool
Bypasses Gemini. Uses keyword matching to simulate classification.

Run:
    python agents/mock_classifier_agent.py
"""

from pydantic import BaseModel
from typing import Optional


# ── Output Schema (identical to classifier_agent.py) ──────────────────────────

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


# ── Keyword rules (simulate what the LLM does) ────────────────────────────────

DOMAIN_KEYWORDS = {
    "police_fir": [
        "police", "arrest", "fir", "warrant", "custody", "detained",
        "station", "officer", "magistrate", "bail", "cognisable"
    ],
    "eviction_housing": [
        "evict", "landlord", "tenant", "rent", "house", "locked out",
        "notice", "accommodation", "flat", "room"
    ],
    "workplace_salary": [
        "salary", "employer", "wage", "fired", "terminated", "job",
        "workplace", "boss", "payslip", "pf", "provident"
    ],
    "consumer_fraud": [
        "product", "fake", "fraud", "online", "refund", "complaint",
        "defective", "ecommerce", "amazon", "flipkart", "cheated"
    ],
    "domestic_violence": [
        "husband", "wife", "abuse", "beats", "violence", "protection order",
        "shelter", "domestic", "family member", "partner"
    ],
    "land_property": [
        "land", "property", "neighbour", "encroach", "boundary", "wall",
        "plot", "ownership", "inheritance", "registry"
    ],
    "court_bail": [
        "court", "hearing", "bail", "jail", "prison", "advocate",
        "judge", "trial", "acquit", "charge sheet"
    ],
    "government_schemes": [
        "scheme", "aadhaar", "ration", "kisan", "mgnrega", "pension",
        "subsidy", "benefit", "welfare", "pds", "government"
    ],
}


def run_mock_classifier_agent(query: str) -> ClassifierResponse:
    """
    Keyword-based classifier. Same signature as run_classifier_agent().
    Not as smart as the LLM version but good enough to test the pipeline.
    """
    q = query.lower()
    scores = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in q)
        scores[domain] = score

    best_domain = max(scores, key=scores.get)
    best_score = scores[best_domain]
    second_scores = sorted(scores.values(), reverse=True)

    # Confidence: based on keyword hits and gap from second place
    if best_score == 0:
        confidence = 0.3  # nothing matched
    elif len(second_scores) > 1 and second_scores[1] == best_score:
        confidence = 0.5  # tie — ambiguous
    else:
        confidence = min(0.6 + (best_score * 0.1), 0.95)

    clarification_needed = confidence < 0.6
    clarification_question = None

    if clarification_needed:
        # Find the two top domains for a specific question
        top_two = sorted(scores, key=scores.get, reverse=True)[:2]
        clarification_question = (
            f"Could you tell me more — is this mainly about "
            f"{top_two[0].replace('_', ' ')} or {top_two[1].replace('_', ' ')}?"
        )

    return ClassifierResponse(
        domain=best_domain,
        confidence=round(confidence, 2),
        clarification_needed=clarification_needed,
        clarification_question=clarification_question,
    )


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
        ("I have a problem with my house.", None),  # ambiguous
    ]

    print("\n=== MOCK CLASSIFIER TEST ===")
    print("NOTE: Using keyword matching — no API calls made\n")

    passed = 0
    for query, expected_domain in test_cases:
        try:
            response = run_mock_classifier_agent(query)
            print_response(query, response)

            if expected_domain:
                if response.domain == expected_domain:
                    print(f"  ✓ Correct")
                    passed += 1
                else:
                    print(f"  ✗ Expected: {expected_domain} — keyword matching isn't perfect, LLM will do better")
            else:
                if response.clarification_needed:
                    print(f"  ✓ Correctly flagged as ambiguous")
                    passed += 1
                else:
                    print(f"  ~ Didn't ask for clarification (acceptable for mock)")
                    passed += 1

        except Exception as e:
            print(f"\n  ✗ Failed: {e}")

    print(f"\n{'='*50}")
    print(f"MOCK RESULT: {passed}/{len(test_cases)} passed")
    print("Note: mock uses keywords, real classifier uses LLM — expect better accuracy on real agent.")


if __name__ == "__main__":
    test()
