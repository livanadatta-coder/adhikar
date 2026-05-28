"""
agents/mock_actions_agent.py — Week 2 Dev Tool
Bypasses Gemini entirely. Same pattern as mock_rights_agent.py.

Run:
    python agents/mock_actions_agent.py
"""

import sys
from pathlib import Path
from pydantic import BaseModel


# ── Output Schema (identical to actions_agent.py) ─────────────────────────────

class Action(BaseModel):
    action: str
    what_to_do: str
    priority: int
    requires_lawyer: bool


class ActionsResponse(BaseModel):
    domain: str
    actions: list[Action]
    disclaimer: str
    sources: list[str]


# ── Mock responses ────────────────────────────────────────────────────────────

MOCK_RESPONSES = {
    "arrest_no_warrant": {
        "domain": "police_fir",
        "actions": [
            {
                "action": "Ask the officer to show their warrant",
                "what_to_do": "Calmly ask the officer: 'Please show me your arrest warrant.' You have the legal right to see it before they take you anywhere.",
                "priority": 1,
                "requires_lawyer": False
            },
            {
                "action": "Ask the officer to state their name and designation",
                "what_to_do": "Ask the officer for their name, badge number, and police station. Under D.K. Basu guidelines they must identify themselves — note this information down or have someone else note it.",
                "priority": 2,
                "requires_lawyer": False
            },
            {
                "action": "Call a family member and tell them your location",
                "what_to_do": "Police must allow you to inform one family member or friend of your arrest and where you are being taken. Insist on this right before leaving your home.",
                "priority": 3,
                "requires_lawyer": False
            },
            {
                "action": "Contact a lawyer as soon as possible",
                "what_to_do": "You have the right to speak with a lawyer immediately after arrest. If you cannot afford one, call the NALSA free legal aid helpline at 15100.",
                "priority": 4,
                "requires_lawyer": True
            }
        ],
        "disclaimer": "This is legal information, not legal advice. For your specific situation, consult a lawyer or contact NALSA helpline at 15100.",
        "sources": ["CrPC Section 41", "CrPC Section 50", "D.K. Basu Guidelines (1997)", "Constitution of India Article 22"]
    },
    "held_30_hours": {
        "domain": "police_fir",
        "actions": [
            {
                "action": "Contact a lawyer immediately to file a habeas corpus petition",
                "what_to_do": "Being held for 30 hours without a magistrate's order is illegal. A lawyer can file a habeas corpus petition in the High Court to get you released — this can happen within hours.",
                "priority": 1,
                "requires_lawyer": True
            },
            {
                "action": "Have a family member contact the NALSA helpline",
                "what_to_do": "Ask your family to call NALSA (National Legal Services Authority) at 15100 for free legal help. They can arrange a duty lawyer to assist you.",
                "priority": 2,
                "requires_lawyer": False
            },
            {
                "action": "Note down the names of all officers involved",
                "what_to_do": "Write down the name, badge number, and rank of every officer who has been involved in your detention — this will be needed for any complaint or court action.",
                "priority": 3,
                "requires_lawyer": False
            }
        ],
        "disclaimer": "This is legal information, not legal advice. For your specific situation, consult a lawyer or contact NALSA helpline at 15100.",
        "sources": ["Constitution of India Article 22(2)", "CrPC Section 167", "D.K. Basu Guidelines (1997)"]
    },
    "fir_refused": {
        "domain": "police_fir",
        "actions": [
            {
                "action": "Write your complaint and send it by post to the Superintendent of Police",
                "what_to_do": "Write down exactly what happened, sign it, and send it by registered post to the Superintendent of Police for your district. Under Section 154(3) CrPC, the SP must investigate or order an investigation.",
                "priority": 1,
                "requires_lawyer": False
            },
            {
                "action": "Go to the magistrate's court and file a complaint directly",
                "what_to_do": "Visit your nearest magistrate's court, write out your complaint at the filing counter, and submit it. The magistrate can legally order police to register your FIR. You do not need a lawyer for this.",
                "priority": 2,
                "requires_lawyer": False
            },
            {
                "action": "Note the name and badge number of the officer who refused",
                "what_to_do": "Write down the full name, rank, and badge number of the officer who refused your FIR — you will need this for your complaint to the SP and the magistrate.",
                "priority": 3,
                "requires_lawyer": False
            }
        ],
        "disclaimer": "This is legal information, not legal advice. For your specific situation, consult a lawyer or contact NALSA helpline at 15100.",
        "sources": ["CrPC Section 154", "CrPC Section 154(3)", "CrPC Section 156(3)"]
    }
}


# ── Mock agent function ───────────────────────────────────────────────────────

def run_mock_actions_agent(query: str, domain: str, chunks: list) -> ActionsResponse:
    """Same signature as run_actions_agent() in actions_agent.py."""
    q = query.lower()
    if "warrant" in q or "arrest me" in q:
        data = MOCK_RESPONSES["arrest_no_warrant"]
    elif "30 hours" in q or "magistrate" in q or "held" in q:
        data = MOCK_RESPONSES["held_30_hours"]
    elif "fir" in q or "refusing" in q or "file" in q:
        data = MOCK_RESPONSES["fir_refused"]
    else:
        data = MOCK_RESPONSES["arrest_no_warrant"]

    return ActionsResponse(**data)


def print_response(response: ActionsResponse):
    print("\n" + "="*60)
    print("DO THIS NOW")
    print("="*60)
    for action in response.actions:
        lawyer_tag = " [needs lawyer]" if action.requires_lawyer else ""
        print(f"\n{action.priority}. {action.action}{lawyer_tag}")
        print(f"   {action.what_to_do}")
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
            response = run_mock_actions_agent(tc["query"], tc["domain"], chunks)

            # Validate schema
            assert len(response.actions) >= 2, "Too few actions returned"
            assert all(a.what_to_do for a in response.actions), "Missing what_to_do"
            assert response.actions == sorted(response.actions, key=lambda x: x.priority), \
                "Actions not sorted by priority"
            assert response.disclaimer, "Missing disclaimer"

            print_response(response)
            print(f"\n✓ Test {i} passed — {len(response.actions)} actions, schema valid")
            passed += 1
        except Exception as e:
            print(f"\n✗ Test {i} failed: {e}")

    print(f"\n{'='*60}")
    print(f"MOCK TEST RESULT: {passed}/{len(test_cases)} passed")
    if passed == len(test_cases):
        print("✓ Schema, parsing, and output formatting all working.")
        print("  When API quota resets, swap mock_actions_agent → actions_agent.")
    print("="*60)


if __name__ == "__main__":
    test()
