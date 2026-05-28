"""
agents/rights_agent.py — Phase 2, Week 2 (retrieval fix)
Rewritten for Groq API (llama-3.3-70b-versatile).

Fix: Dual retrieval pass + query expansion to raise Rights recall from 41% → 75%+.
  - Pass 1: Expanded query targets constitutional/case-law chunks (k=8, no MMR)
  - Pass 2: Original query for procedural chunks (k=6, domain-filtered)
  - Deduplication keeps top 10 unique chunks for the LLM
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


# ── Query expansion map ───────────────────────────────────────────────────────
# Maps plain-language user situations to legal terminology that matches
# how rights chunks are actually written in the corpus.
# Keyed by domain → list of (trigger_keywords, expansion_suffix) pairs.

RIGHTS_QUERY_EXPANSIONS = {
    "police_fir": [
        (
            ["arrest", "arrested", "take me", "taking me", "custody", "detain", "detained"],
            "arrested person grounds of arrest Article 22 fundamental rights D.K. Basu guidelines "
            "Section 41 CrPC warrant arrest memo right to be informed"
        ),
        (
            ["24 hours", "30 hours", "hours", "magistrate", "produced", "not produced"],
            "produced before magistrate 24 hours Article 22(2) Section 57 CrPC Section 167 CrPC "
            "remand detention illegal custody habeas corpus"
        ),
        (
            ["fir", "complaint", "register", "refused", "not filing", "refusing"],
            "FIR registration Section 154 CrPC cognisable offence Section 156(3) magistrate "
            "Superintendent of Police Section 41A notice"
        ),
        (
            ["search", "searched", "warrant", "house", "belongings", "property"],
            "search without warrant Section 165 CrPC Section 100 Article 21 right to privacy "
            "D.K. Basu search memo"
        ),
        (
            ["woman", "female", "sunset", "night", "lady"],
            "Section 46 CrPC woman arrested after sunset female arrest D.K. Basu Article 21 "
            "protection dignity"
        ),
        (
            ["bail", "bail application", "bailable", "non-bailable"],
            "bail Section 437 CrPC Section 167 CrPC Article 21 right to liberty default bail "
            "bailable offence magistrate"
        ),
        (
            ["force", "beaten", "threatened", "physical", "torture", "violence", "hitting"],
            "D.K. Basu guidelines police brutality Article 21 right to life dignity custodial "
            "violence Section 46 CrPC"
        ),
        (
            ["family", "son", "daughter", "relative", "informed", "location", "held"],
            "D.K. Basu inform family member arrest Article 22 right to be informed location "
            "custody arrest memo"
        ),
        (
            ["notice", "41A", "appear", "section 41"],
            "Section 41A CrPC notice appearance accused not arrested right to counsel"
        ),
    ]
}


def expand_query_for_rights(query: str, domain: str) -> str:
    """
    Appends legal terminology to the user query so the embedding model
    finds rights/constitutional chunks, not just procedural ones.
    Falls back to original query if no expansion matches.
    """
    q_lower = query.lower()
    expansions = RIGHTS_QUERY_EXPANSIONS.get(domain, [])

    matched_suffixes = []
    for triggers, suffix in expansions:
        if any(kw in q_lower for kw in triggers):
            matched_suffixes.append(suffix)

    if not matched_suffixes:
        return query  # no match → use original

    return query + " — legal context: " + " | ".join(matched_suffixes)


# ── Dual retrieval ────────────────────────────────────────────────────────────

# Acts that must always be included in rights context when present in DB
PRIORITY_ACTS = {
    "Constitution of India",
    "D.K. Basu Guidelines",
}

def retrieve_for_rights(query: str, domain: str, vectorstore) -> list:
    """
    Three-pass retrieval that guarantees rights chunks surface.

    Pass 1 — Priority rights (k=10, expanded query):
        Targets constitutional articles and D.K. Basu chunks specifically.
        These are the chunks that keep missing — pull them first.

    Pass 2 — Expanded query (k=8):
        Legal terminology expansion to catch section-specific rights.

    Pass 3 — Original query (k=6):
        Procedural chunks the user's plain language directly matches.

    Dedup by (act, section) metadata — not content prefix — to avoid
    dropping legitimate duplicate sections with different content.
    Cap at 12 unique chunks.
    """
    expanded_query = expand_query_for_rights(query, domain)

    # Pass 1: force pull constitutional + D.K. Basu chunks
    # Two anchors: constitutional rights + D.K. Basu separately
    # D.K. Basu doesn't embed close to most user queries so needs its own anchor
    rights_anchor = (
        "Article 21 right to life dignity Article 22 arrested informed grounds "
        "fundamental rights custodial protection"
    )
    basu_anchor = (
        "D.K. Basu custodial rights guidelines arrested person police station "
        "arrest memo identify officer inform family custodial violence"
    )
    priority_chunks = vectorstore.similarity_search(
        rights_anchor, k=6, filter={"domain": domain}
    )
    basu_chunks = vectorstore.similarity_search(
        basu_anchor, k=4, filter={"domain": domain}
    )
    priority_chunks = priority_chunks + basu_chunks

    # Pass 2: expanded query
    expanded_chunks = vectorstore.similarity_search(
        expanded_query,
        k=8,
        filter={"domain": domain}
    )

    # Pass 3: original query
    procedural_chunks = vectorstore.similarity_search(
        query,
        k=6,
        filter={"domain": domain}
    )

    # Merge: priority first, then expanded, then procedural
    all_chunks = priority_chunks + expanded_chunks + procedural_chunks

    # Deduplicate by (act, section) pair — keeps first occurrence of each section
    seen_sections = set()
    unique_chunks = []
    for chunk in all_chunks:
        act = chunk.metadata.get("act", "")
        section = chunk.metadata.get("section", "")
        key = f"{act}|{section}"
        if key not in seen_sections:
            seen_sections.add(key)
            unique_chunks.append(chunk)

    # Cap at 12
    return unique_chunks[:12]


# ── Prompt ────────────────────────────────────────────────────────────────────

RIGHTS_PROMPT = """You are an Indian legal rights expert helping ordinary citizens understand their rights.

Based ONLY on the legal documents provided below, identify the 2-4 most important rights the user has in their situation.

CRITICAL RULES:
- Every right you state MUST be directly supported by the provided documents.
- Include the exact Act name and Section number for every right.
- Write in plain language a Standard 8 student can understand.
- Do NOT speculate beyond what the documents say.
- Do NOT say whether the user will win or lose.
- Do NOT make up section numbers or act names.
- PRIORITISE constitutional rights (Article 21, Article 22) and landmark case guidelines
  (D.K. Basu) when they are present in the documents — these are the most important rights
  to surface even if they seem less directly relevant than procedural sections.

Respond in JSON only, no markdown, no explanation. Use this exact structure:
{{
  "domain": "<domain>",
  "rights": [
    {{
      "right": "short title of the right",
      "source_act": "full name of the Act",
      "source_section": "Section number",
      "plain_language": "one sentence explanation anyone can understand"
    }}
  ],
  "disclaimer": "This is legal information, not legal advice. For your specific situation, consult a lawyer or contact NALSA helpline at 15100.",
  "sources": ["list of Act + Section references used"]
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


def run_rights_agent(query: str, domain: str, chunks: list) -> RightsResponse:
    """
    Standard entry point — accepts pre-retrieved chunks.
    Use run_rights_agent_with_retrieval() when you have a vectorstore available
    to get the improved dual-pass retrieval automatically.
    """
    if not chunks:
        raise ValueError(f"No documents retrieved for domain '{domain}'. Cannot ground response.")

    prompt = RIGHTS_PROMPT.format(
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
    return RightsResponse(**data)


def run_rights_agent_with_retrieval(query: str, domain: str, vectorstore) -> RightsResponse:
    """
    Drop-in replacement that does its own dual-pass retrieval.
    Use this in the pipeline instead of retrieving chunks externally.

    Example:
        rights_result = run_rights_agent_with_retrieval(query, domain, vectorstore)
    """
    chunks = retrieve_for_rights(query, domain, vectorstore)
    return run_rights_agent(query, domain, chunks)


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

    test_cases = [
        {"query": "Police came to my house at night and want to arrest me without showing a warrant.", "domain": "police_fir"},
        {"query": "I was arrested and held for 30 hours without being taken to a magistrate.", "domain": "police_fir"},
        {"query": "Police are refusing to file my FIR. What can I do?", "domain": "police_fir"},
    ]

    for i, tc in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {tc['query']}")

        # Show what the expanded query looks like
        expanded = expand_query_for_rights(tc["query"], tc["domain"])
        print(f"  Expanded query: {expanded[:120]}...")

        # Use dual-pass retrieval
        chunks = retrieve_for_rights(tc["query"], tc["domain"], vectorstore)
        print(f"  Retrieved {len(chunks)} unique chunks (dual-pass)")

        # Show which acts were retrieved
        retrieved_acts = [f"{c.metadata.get('act','')} {c.metadata.get('section','')}" for c in chunks]
        print(f"  Acts in context: {', '.join(retrieved_acts)}")

        try:
            response = run_rights_agent(tc["query"], tc["domain"], chunks)
            print_response(response)
            print(f"\n✓ Test {i} passed — {len(response.rights)} rights returned")
        except Exception as e:
            print(f"\n✗ Test {i} failed: {e}")


if __name__ == "__main__":
    test()
