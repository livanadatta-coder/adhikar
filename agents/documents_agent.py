"""
documents_agent.py

Agent for handling document guidance queries in Adhikar.
Covers: Government IDs (Aadhaar/PAN/Voter ID), Passport & Travel,
        Civil Certificates (Birth/Marriage/Death), Property & Land documents.

Returns structured response with:
  - matched_document: which document the user is asking about
  - required_documents: checklist of what they need to bring/have
  - process_steps: step-by-step guide
  - fees, processing_time, helpline, website
  - plain_english_summary: short LLM-generated summary for low-literacy users
"""

import json
import os
from pathlib import Path
from groq import Groq

# ── Groq client ──────────────────────────────────────────────────────────────
_client = None
def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    return _client
MODEL = "llama-3.3-70b-versatile"

# ── Load corpus at import time ────────────────────────────────────────────────
_CORPUS_DIR = Path(__file__).parent.parent / "data" / "documents_corpus"

_ALL_DOCUMENTS: list[dict] = []

def _load_corpus():
    """Load all JSON corpus files into a flat list of document entries."""
    global _ALL_DOCUMENTS
    if _ALL_DOCUMENTS:
        return  # already loaded

    corpus_files = [
        "government_ids.json",
        "passport_travel.json",
        "civil_certificates.json",
        "property_land.json",
    ]

    for fname in corpus_files:
        fpath = _CORPUS_DIR / fname
        if not fpath.exists():
            print(f"[documents_agent] WARNING: corpus file not found: {fpath}")
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for doc in data.get("documents", []):
            doc["_domain"] = data.get("domain", "unknown")
            _ALL_DOCUMENTS.append(doc)

    print(f"[documents_agent] Loaded {len(_ALL_DOCUMENTS)} document entries.")

_load_corpus()


# ── Intent → document matching ────────────────────────────────────────────────

_KEYWORD_MAP: dict[str, list[str]] = {
    "aadhaar_new":              ["aadhaar", "uid", "aadhar", "aadhhaar", "12 digit id", "biometric id", "uidai"],
    "pan_new":                  ["pan card", "pan", "permanent account", "income tax id", "tan", "epan", "e-pan"],
    "voter_id_new":             ["voter id", "voter card", "epic", "election card", "vote", "voting card"],
    "passport_renewal":         ["renew passport", "passport renewal", "expired passport", "re-issue passport",
                                  "passport reissue", "lost passport", "passport expired", "renewal",
                                  "expired", "renew"],
    "passport_new_adult":       ["new passport", "apply passport", "fresh passport", "travel document",
                                  "first passport", "apply for passport"],
    "birth_certificate_original": ["birth certificate", "birth cert", "born certificate", "janam praman",
                                    "duplicate birth", "original birth", "birth registration"],
    "marriage_certificate":     ["marriage certificate", "marriage cert", "vivah praman", "court marriage",
                                  "marriage registration", "wedding certificate", "nikah certificate"],
    "death_certificate":        ["death certificate", "death cert", "mrutyu praman", "death registration"],
    "sale_deed_registration":   ["sale deed", "property registration", "register property", "buy property",
                                  "property purchase", "stamp duty", "sub registrar"],
    "land_records":             ["land record", "7/12", "satbara", "rtc", "patta", "pahani", "khata", "khasra",
                                  "mutation", "bhulekh", "land ownership"],
    "encumbrance_certificate":  ["encumbrance", "ec certificate", "property dues", "property loan check",
                                  "encumbrance certificate"],
}


def _find_best_match(query: str) -> dict | None:
    """
    Simple keyword matching to find the most relevant document entry.
    Returns the document dict or None if no match found.
    """
    query_lower = query.lower()
    scores: dict[str, int] = {}

    for doc_id, keywords in _KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            scores[doc_id] = score

    if not scores:
        return None

    best_id = max(scores, key=scores.__getitem__)
    for doc in _ALL_DOCUMENTS:
        if doc["id"] == best_id:
            return doc

    return None


def _llm_pick_document(query: str) -> str | None:
    """
    Use LLM to identify which document the user needs when keyword matching fails.
    Returns document ID string or None.
    """
    doc_ids = [d["id"] for d in _ALL_DOCUMENTS]
    doc_titles = {d["id"]: d["title"] for d in _ALL_DOCUMENTS}
    id_list = "\n".join(f"- {did}: {doc_titles[did]}" for did in doc_ids)

    prompt = f"""You are a document guidance assistant for India. A user has asked:
"{query}"

From the list below, identify which document they are asking about.
Reply with ONLY the exact document ID from the list, nothing else.
If none match, reply: NONE

{id_list}"""

    response = _get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=20,
        temperature=0,
    )
    result = response.choices[0].message.content.strip()
    if result == "NONE" or result not in [d["id"] for d in _ALL_DOCUMENTS]:
        return None
    return result


def _generate_plain_summary(doc: dict, query: str) -> str:
    """
    Generate a short, plain-language summary (3–5 sentences) suitable for
    low-literacy users. Uses Groq LLM.
    """
    step_titles = [f"{s['step']}. {s['title']}" for s in doc.get("process_steps", [])]
    steps_text = "\n".join(step_titles)

    prompt = f"""You help explain Indian government document processes to rural and low-literacy people.
The user asked: "{query}"

They need: {doc['title']}
Key steps:
{steps_text}
Fees: {doc.get('fees', 'Check locally')}
Time: {doc.get('processing_time', 'Varies')}

Write 3–5 short, simple sentences (no bullet points, no jargon) explaining what this document is,
what they need to do first, and roughly how long it takes. Use friendly, reassuring language.
Keep it under 80 words."""

    response = _get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


# ── Main agent function ───────────────────────────────────────────────────────

def run_documents_agent(query: str) -> dict:
    """
    Main entry point. Takes a user query string and returns a structured dict:
    {
        "success": bool,
        "matched_document": str | None,
        "domain": str | None,
        "title": str | None,
        "description": str | None,
        "plain_summary": str,
        "required_documents": list[dict],   # [{category, options}]
        "process_steps": list[dict],         # [{step, title, detail, tip}]
        "fees": str | None,
        "processing_time": str | None,
        "helpline": str | None,
        "website": str | None,
        "not_found_message": str | None,     # only when success=False
    }
    """
    # 1. Try keyword match first (fast, free)
    doc = _find_best_match(query)

    # 2. Fallback to LLM classification
    if doc is None:
        doc_id = _llm_pick_document(query)
        if doc_id:
            doc = next((d for d in _ALL_DOCUMENTS if d["id"] == doc_id), None)

    # 3. Nothing found
    if doc is None:
        return {
            "success": False,
            "matched_document": None,
            "domain": None,
            "title": None,
            "description": None,
            "plain_summary": "",
            "required_documents": [],
            "process_steps": [],
            "fees": None,
            "processing_time": None,
            "helpline": None,
            "website": None,
            "not_found_message": (
                "I could not find specific document guidance for your query. "
                "You can ask about: Aadhaar, PAN Card, Voter ID, Passport, "
                "Birth/Marriage/Death Certificates, Sale Deed registration, "
                "Land Records, or Encumbrance Certificate."
            ),
        }

    # 4. Generate plain summary
    plain_summary = _generate_plain_summary(doc, query)

    return {
        "success": True,
        "matched_document": doc["id"],
        "domain": doc.get("_domain"),
        "title": doc["title"],
        "description": doc.get("description", ""),
        "plain_summary": plain_summary,
        "required_documents": doc.get("required_documents", []),
        "process_steps": doc.get("process_steps", []),
        "fees": doc.get("fees"),
        "processing_time": doc.get("processing_time"),
        "helpline": doc.get("helpline"),
        "website": doc.get("website"),
        "not_found_message": None,
    }


# ── CLI test ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "how do I get a passport in India"
    result = run_documents_agent(query)

    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"Matched: {result['matched_document']} — {result['title']}")
    print(f"\nPlain Summary:\n{result['plain_summary']}")
    print(f"\nFees: {result['fees']}")
    print(f"Time: {result['processing_time']}")
    print(f"Helpline: {result['helpline']}")
    print(f"\nRequired Documents ({len(result['required_documents'])} categories):")
    for cat in result["required_documents"]:
        print(f"  [{cat['category']}]: {len(cat['options'])} options")
    print(f"\nProcess Steps ({len(result['process_steps'])} steps):")
    for s in result["process_steps"]:
        print(f"  Step {s['step']}: {s['title']}")
    print("="*60)
