"""
agents/mock_rights_agent.py — Week 2 Dev Tool
Bypasses Gemini entirely. Uses a hardcoded realistic response to let you:
  - Validate your Pydantic schema works
  - Test print_response() output formatting
  - Build and test the full pipeline without burning API quota

Drop this next to rights_agent.py and run:
    python agents/mock_rights_agent.py

When Gemini quota resets (or you switch to Claude API), go back to rights_agent.py.
The real agent and this mock are interchangeable — same input/output contract.
"""

import json
import sys
from pathlib import Path
from pydantic import BaseModel

# ── Output Schema (identical to rights_agent.py) ──────────────────────────────

class Right(BaseModel):
    right: str
    source_act: str
    source_section: str
    plain_language: str

class RightsResponse(BaseModel):
    domain: str
    rights: list[Right]
    disclaimer: str
    sources: list[str]


# ── Mock responses keyed by scenario ─────────────────────────────────────────
# These are realistic outputs — what the real agent SHOULD return.
# When you eventually run the real agent, compare its output to these.

MOCK_RESPONSES = {
    "arrest_no_warrant": {
        "domain": "police_fir",
        "rights": [
            {
                "right": "Right to know why you are being arrested",
                "source_act": "Code of Criminal Procedure",
                "source_section": "Section 50",
                "plain_language": "Police must immediately tell you the exact reason for your arrest. If they refuse, the arrest can be challenged in court."
            },
            {
                "right": "Police cannot arrest without warrant unless specific conditions are met",
                "source_act": "Code of Criminal Procedure",
                "source_section": "Section 41",
                "plain_language": "Police can only arrest you without a warrant if they have a specific reason — like catching you committing a crime. They must write down that reason before arresting you."
            },
            {
                "right": "Right to inform a family member of your arrest",
                "source_act": "D.K. Basu Guidelines",
                "source_section": "Supreme Court Guidelines (1997)",
                "plain_language": "As soon as you are arrested, police must let you tell one family member or friend where you are being taken. They cannot stop you from making this communication."
            },
            {
                "right": "Right to be produced before a magistrate within 24 hours",
                "source_act": "Constitution of India",
                "source_section": "Article 22(2)",
                "plain_language": "Police cannot hold you for more than 24 hours without taking you to a magistrate. After 24 hours, holding you without a magistrate's order is illegal."
            }
        ],
        "disclaimer": "This is legal information, not legal advice. For your specific situation, consult a lawyer or contact NALSA helpline at 15100.",
        "sources": ["CrPC Section 50", "CrPC Section 41", "D.K. Basu v. State of West Bengal AIR 1997 SC 610", "Constitution of India Article 22(2)"]
    },
    "held_30_hours": {
        "domain": "police_fir",
        "rights": [
            {
                "right": "Right to be produced before a magistrate within 24 hours",
                "source_act": "Constitution of India",
                "source_section": "Article 22(2)",
                "plain_language": "Holding you for 30 hours without a magistrate's order is a constitutional violation. You can challenge this immediately in the High Court via a habeas corpus petition."
            },
            {
                "right": "Right to consult a lawyer immediately",
                "source_act": "Constitution of India",
                "source_section": "Article 22(1)",
                "plain_language": "You have the right to call and speak with a lawyer of your choice immediately after arrest. Police cannot deny you this right."
            },
            {
                "right": "Arrest memo must be prepared and witnessed",
                "source_act": "D.K. Basu Guidelines",
                "source_section": "Supreme Court Guidelines (1997)",
                "plain_language": "When you were arrested, police were required to prepare a written arrest memo in front of a family member or local witness. If they did not do this, the arrest procedure was illegal."
            }
        ],
        "disclaimer": "This is legal information, not legal advice. For your specific situation, consult a lawyer or contact NALSA helpline at 15100.",
        "sources": ["Constitution of India Article 22(1)", "Constitution of India Article 22(2)", "D.K. Basu v. State of West Bengal AIR 1997 SC 610"]
    },
    "fir_refused": {
        "domain": "police_fir",
        "rights": [
            {
                "right": "Right to have your FIR registered for any cognisable offence",
                "source_act": "Code of Criminal Procedure",
                "source_section": "Section 154",
                "plain_language": "Police cannot refuse to register an FIR for a cognisable offence (serious crime). If they refuse, they are breaking the law."
            },
            {
                "right": "Right to escalate FIR refusal to the Superintendent of Police",
                "source_act": "Code of Criminal Procedure",
                "source_section": "Section 154(3)",
                "plain_language": "If police refuse your FIR, write down your complaint and send it by post to the Superintendent of Police. The SP is legally required to investigate or order an investigation."
            },
            {
                "right": "Right to approach a magistrate directly",
                "source_act": "Code of Criminal Procedure",
                "source_section": "Section 156(3)",
                "plain_language": "You can go directly to a magistrate's court with your complaint. The magistrate can order police to register your FIR. You do not need a lawyer to do this."
            }
        ],
        "disclaimer": "This is legal information, not legal advice. For your specific situation, consult a lawyer or contact NALSA helpline at 15100.",
        "sources": ["CrPC Section 154", "CrPC Section 154(3)", "CrPC Section 156(3)"]
    }
}


# ── Mock agent function ───────────────────────────────────────────────────────

def run_mock_rights_agent(query: str, domain: str, chunks: list) -> RightsResponse:
    """
    Same signature as run_rights_agent() in rights_agent.py.
    Returns a hardcoded but realistic RightsResponse.
    Picks the mock response based on keywords in the query.
    """
    q = query.lower()
    if "warrant" in q or "arrest me" in q:
        data = MOCK_RESPONSES["arrest_no_warrant"]
    elif "30 hours" in q or "magistrate" in q or "held" in q:
        data = MOCK_RESPONSES["held_30_hours"]
    elif "fir" in q or "refusing" in q or "file" in q:
        data = MOCK_RESPONSES["fir_refused"]
    else:
        # Default fallback
        data = MOCK_RESPONSES["arrest_no_warrant"]

    return RightsResponse(**data)


def print_response(response: RightsResponse):
    print("\n" + "="*60)
    print("YOUR RIGHTS")
    print("="*60)
    for i, right in enumerate(response.rights, 1):
        print(f"\n{i}. {right.right}")
        print(f"   Law: {right.source_act}, {right.source_section}")
        print(f"   What this means: {right.plain_language}")
    print(f"\n--- Sources: {', '.join(response.sources)}")
    print(f"\n⚠  {response.disclaimer}")


# ── Test ──────────────────────────────────────────────────────────────────────

def test():
    sys.path.append(str(Path(__file__).parent.parent))

    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma

    print("Loading vector store...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    vectorstore = Chroma(
        persist_directory="./db",
        embedding_function=embeddings,
        collection_name="legal_corpus",
    )
    print("✓ Vector store loaded\n")
    print("NOTE: Using MOCK responses — no API calls made\n")

    test_cases = [
        {
            "query": "Police came to my house at night and want to arrest me without showing a warrant.",
            "domain": "police_fir"
        },
        {
            "query": "I was arrested and held for 30 hours without being taken to a magistrate.",
            "domain": "police_fir"
        },
        {
            "query": "Police are refusing to file my FIR. What can I do?",
            "domain": "police_fir"
        },
    ]

    passed = 0
    for i, tc in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {tc['query']}")

        chunks = vectorstore.similarity_search(
            tc["query"], k=4, filter={"domain": tc["domain"]}
        )
        print(f"Retrieved {len(chunks)} chunks from database")

        try:
            response = run_mock_rights_agent(tc["query"], tc["domain"], chunks)

            # Validate schema
            assert len(response.rights) >= 2, "Too few rights returned"
            assert all(r.source_section for r in response.rights), "Missing source sections"
            assert response.disclaimer, "Missing disclaimer"

            print_response(response)
            print(f"\n✓ Test {i} passed — {len(response.rights)} rights, schema valid")
            passed += 1
        except Exception as e:
            print(f"\n✗ Test {i} failed: {e}")

    print(f"\n{'='*60}")
    print(f"MOCK TEST RESULT: {passed}/{len(test_cases)} passed")
    if passed == len(test_cases):
        print("✓ Schema, parsing, and output formatting all working.")
        print("  When API quota resets, swap mock_rights_agent → rights_agent.")
    print("="*60)


if __name__ == "__main__":
    test()
