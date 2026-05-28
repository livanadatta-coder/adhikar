"""
agents/actions_agent.py — Phase 2, Week 2
Rewritten for Groq API (llama-3.3-70b-versatile).
"""

import json
import os
import sys
from pathlib import Path

from groq import Groq
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


# ── Output Schema ─────────────────────────────────────────────────────────────

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


# ── Prompt ────────────────────────────────────────────────────────────────────

ACTIONS_PROMPT = """You are a legal first-responder helping ordinary Indian citizens take immediate action.

Based ONLY on the legal documents provided below, give the user 2-4 concrete steps they can take RIGHT NOW.

CRITICAL RULES:
- Actions must be things the user can do TODAY, in the next few hours.
- Rank actions by urgency — priority 1 is the most important first step.
- Write in plain language a Standard 8 student can understand.
- No legal jargon. Say "go to the magistrate's court" not "invoke Section 156(3)".
- Mark requires_lawyer as true ONLY if the step cannot be done without a lawyer.
- requires_lawyer must be FALSE for: going to a police station, filing an FIR, appearing before a magistrate, sending a written complaint, calling a helpline, going to a consumer forum, filing on e-daakhil.nic.in. These are all things a person can do themselves.
- requires_lawyer must be TRUE only for: filing a writ petition, filing a bail application in court, filing a civil suit, representing yourself in a contested hearing.
- Do NOT repeat rights — only concrete actions.
- Do NOT speculate beyond what the documents say.

Respond in JSON only, no markdown, no explanation. Use this exact structure:
{{
  "domain": "<domain>",
  "actions": [
    {{
      "action": "short title of the step",
      "what_to_do": "one plain-language sentence telling them exactly what to do",
      "priority": 1,
      "requires_lawyer": false
    }}
  ],
  "disclaimer": "This is legal information, not legal advice. For your specific situation, consult a lawyer or contact NALSA helpline at 15100.",
  "sources": ["list of Act + Section references that support these actions"]
}}

User situation: {query}

Domain: {domain}

Legal documents:
{chunks}"""


# ── Agent ─────────────────────────────────────────────────────────────────────

def format_chunks(chunks: list) -> str:
    formatted = []
    for i, chunk in enumerate(chunks, 1):
        m = chunk.metadata
        formatted.append(
            f"[Document {i}] {m['act']} {m['section']} — {m['title']}\n{chunk.page_content}"
        )
    return "\n\n".join(formatted)


def run_actions_agent(query: str, domain: str, chunks: list) -> ActionsResponse:
    if not chunks:
        raise ValueError(f"No documents retrieved for domain '{domain}'. Cannot ground response.")

    prompt = ACTIONS_PROMPT.format(
        domain=domain,
        query=query,
        chunks=format_chunks(chunks)
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    data = json.loads(raw)

    if "actions" in data:
        data["actions"].sort(key=lambda x: x.get("priority", 99))

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

    test_cases = [
        {"query": "Police came to my house at night and want to arrest me without showing a warrant.", "domain": "police_fir"},
        {"query": "I was arrested and held for 30 hours without being taken to a magistrate.", "domain": "police_fir"},
        {"query": "Police are refusing to file my FIR. What can I do?", "domain": "police_fir"},
    ]

    for i, tc in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {tc['query']}")
        chunks = vectorstore.similarity_search(tc["query"], k=4, filter={"domain": tc["domain"]})
        print(f"Retrieved {len(chunks)} chunks")
        try:
            response = run_actions_agent(tc["query"], tc["domain"], chunks)
            print_response(response)
            print(f"\n✓ Test {i} passed — {len(response.actions)} actions returned")
        except Exception as e:
            print(f"\n✗ Test {i} failed: {e}")


if __name__ == "__main__":
    test()
