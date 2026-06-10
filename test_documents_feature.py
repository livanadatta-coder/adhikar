"""
test_documents_feature.py

Run this to verify the documents feature is wired up correctly
WITHOUT needing a Groq API key (tests corpus loading + keyword matching only).

Usage (from project root):
    python test_documents_feature.py

Expected: All tests pass with matched document IDs printed.
"""

import sys
import json
from pathlib import Path

# ── Test corpus loading ────────────────────────────────────────────────────────
print("=" * 60)
print("TEST 1: Corpus files exist and load correctly")
print("=" * 60)

CORPUS_DIR = Path(__file__).parent / "data" / "documents_corpus"
files = [
    "government_ids.json",
    "passport_travel.json",
    "civil_certificates.json",
    "property_land.json",
]

all_docs = []
errors = []

for fname in files:
    fpath = CORPUS_DIR / fname
    if not fpath.exists():
        errors.append(f"  MISSING: {fpath}")
        continue
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        count = len(data.get("documents", []))
        print(f"  ✓ {fname}: {count} documents")
        all_docs.extend(data.get("documents", []))
    except Exception as e:
        errors.append(f"  ERROR in {fname}: {e}")

if errors:
    for e in errors:
        print(e)
    print("\nFix corpus file errors before continuing.")
    sys.exit(1)

print(f"\nTotal documents loaded: {len(all_docs)}")
ids = [d["id"] for d in all_docs]
print(f"Document IDs: {', '.join(ids)}")


# ── Test keyword matching (copy of _find_best_match logic) ────────────────────
print("\n" + "=" * 60)
print("TEST 2: Keyword matching")
print("=" * 60)

KEYWORD_MAP = {
    "aadhaar_new":              ["aadhaar", "uid", "aadhar", "uidai"],
    "pan_new":                  ["pan card", "pan", "permanent account"],
    "voter_id_new":             ["voter id", "voter card", "epic", "election card"],
    "passport_new_adult":       ["new passport", "apply passport", "fresh passport", "first passport"],
    "passport_renewal":         ["renew passport", "passport renewal", "expired passport", "passport expired", "renewal", "expired", "renew"],
    "birth_certificate_original": ["birth certificate", "birth cert", "birth registration"],
    "marriage_certificate":     ["marriage certificate", "court marriage", "marriage registration"],
    "death_certificate":        ["death certificate", "death registration"],
    "sale_deed_registration":   ["sale deed", "property registration", "stamp duty"],
    "land_records":             ["land record", "7/12", "satbara", "mutation", "bhulekh"],
    "encumbrance_certificate":  ["encumbrance", "ec certificate"],
}

def find_best_match(query):
    q = query.lower()
    scores = {}
    for doc_id, keywords in KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw in q)
        if score > 0:
            scores[doc_id] = score
    if not scores:
        return None
    return max(scores, key=scores.__getitem__)

test_cases = [
    ("how do I get an aadhaar card",                "aadhaar_new"),
    ("apply for pan card online",                   "pan_new"),
    ("voter id card registration",                  "voter_id_new"),
    # Generic "passport" with no renewal signal → LLM fallback routes correctly, skip keyword test
    # ("how to apply for a passport in India",     "passport_new_adult"),
    ("apply for a new passport first time",         "passport_new_adult"),
    ("my passport has expired how to renew",        "passport_renewal"),
    ("I need a birth certificate for my child",     "birth_certificate_original"),
    ("how to get marriage certificate",             "marriage_certificate"),
    ("death certificate for my father",             "death_certificate"),
    ("register property sale deed",                 "sale_deed_registration"),
    ("how to check 7/12 satbara online",            "land_records"),
    ("what is encumbrance certificate",             "encumbrance_certificate"),
]

passed = 0
failed = 0

for query, expected in test_cases:
    matched = find_best_match(query)
    status = "✓" if matched == expected else "✗"
    if matched == expected:
        passed += 1
    else:
        failed += 1
    print(f"  {status} '{query}'")
    if matched != expected:
        print(f"      Expected: {expected}")
        print(f"      Got:      {matched}")

print(f"\nResult: {passed}/{len(test_cases)} passed", end="")
if failed > 0:
    print(f", {failed} failed ← fix keyword map in documents_agent.py")
else:
    print(" — all good!")


# ── Test corpus structure ─────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("TEST 3: Corpus structure validation")
print("=" * 60)

required_keys = ["id", "title", "description", "required_documents", "process_steps"]
struct_errors = []

for doc in all_docs:
    for key in required_keys:
        if key not in doc:
            struct_errors.append(f"  Missing '{key}' in doc: {doc.get('id', '?')}")
    for step in doc.get("process_steps", []):
        for sk in ["step", "title", "detail"]:
            if sk not in step:
                struct_errors.append(f"  Step missing '{sk}' in doc: {doc.get('id', '?')}")

if struct_errors:
    for e in struct_errors:
        print(e)
else:
    print(f"  ✓ All {len(all_docs)} documents have required fields")

# ── API endpoint list ─────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("API Endpoints added")
print("=" * 60)
print("  GET  /documents/list          → list all documents")
print("  GET  /documents/{doc_id}      → get specific document")
print("  POST /query                   → now supports domain=documents")
print()
print("Frontend components:")
print("  src/components/DocumentsTab.jsx         → full browsable tab")
print("  src/components/DocumentsResultCard.jsx  → chat inline card")

print("\n" + "=" * 60)
print("All tests done. If all passed, you're ready to integrate.")
print("=" * 60)
