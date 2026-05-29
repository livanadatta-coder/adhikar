"""
pipeline.py — Adhikar main pipeline entry point

Full flow:
  1. Detect language
  2. Translate to English (if needed)
  3. Classify domain
  4. Retrieve chunks (3-pass for rights)
  5. Run Rights + Actions + Forms agents
  6. Synthesise into ResponseSchema
  7. Translate response back to user language

Usage:
    python pipeline.py
    python pipeline.py --lang hi   # force Hindi output
"""

import json
import os
import sys
import argparse
from pathlib import Path

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from utils.translator import detect_language, translate_to_english, translate_response, SUPPORTED_LANGUAGES
from agents.classifier_agent import run_classifier_agent
from agents.rights_agent import retrieve_for_rights, run_rights_agent
from agents.actions_agent import run_actions_agent
from agents.forms_agent import run_forms_agent
from agents.synthesis_agent import run_synthesis_agent


# ── Load vectorstore once at startup ─────────────────────────────────────────

def load_vectorstore():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    return Chroma(
        persist_directory="./db",
        embedding_function=embeddings,
        collection_name="legal_corpus",
    )


# ── Full pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(query: str, vectorstore, forced_lang: str = None) -> dict:
    """
    Run the full Adhikar pipeline for a user query.

    Args:
        query:        User's input in any supported language
        vectorstore:  Loaded ChromaDB vectorstore
        forced_lang:  Override language detection (e.g. 'hi' for Hindi)

    Returns:
        dict with keys: domain, rights, actions, forms, disclaimer, sources,
                        detected_lang, response_lang
    """

    # Stage 1 — Language detection
    detected_lang = forced_lang if forced_lang else detect_language(query)
    print(f"\n  [pipeline] Language: {SUPPORTED_LANGUAGES.get(detected_lang, detected_lang)}")

    # Stage 2 — Translate to English
    english_query = translate_to_english(query, detected_lang)
    if detected_lang != "en":
        print(f"  [pipeline] Translated: {english_query}")

    # Stage 3 — Classify domain
    classifier_result = run_classifier_agent(english_query)
    domain = classifier_result.domain
    confidence = classifier_result.confidence
    print(f"  [pipeline] Domain: {domain} (confidence: {confidence:.0%})")

    if classifier_result.clarification_needed:
        return {
            "clarification_needed": True,
            "clarification_question": classifier_result.clarification_question,
            "detected_lang": detected_lang,
        }

    # Stage 4 — Retrieve chunks (3-pass for rights)
    chunks = retrieve_for_rights(english_query, domain, vectorstore)
    print(f"  [pipeline] Retrieved {len(chunks)} chunks")

    # Stage 5 — Run agents
    rights_response  = run_rights_agent(english_query, domain, chunks)
    actions_response = run_actions_agent(english_query, domain, chunks)
    forms_response   = run_forms_agent(english_query, domain)

    # Stage 6 — Synthesise
    final = run_synthesis_agent(domain, rights_response, actions_response, forms_response)
    response_dict = final.model_dump() if hasattr(final, "model_dump") else dict(final)

    # Stage 7 — Translate response back
    translated = translate_response(response_dict, detected_lang)
    translated["detected_lang"] = detected_lang
    translated["response_lang"] = SUPPORTED_LANGUAGES.get(detected_lang, detected_lang)

    return translated


# ── Pretty print ──────────────────────────────────────────────────────────────

def print_response(response: dict):
    lang = response.get("response_lang", "English")
    print(f"\n{'='*60}")
    print(f"  ADHIKAR RESPONSE ({lang})")
    print(f"{'='*60}")

    print(f"\n📋 YOUR RIGHTS")
    for i, right in enumerate(response.get("rights", []), 1):
        print(f"\n  {i}. {right['right']}")
        print(f"     Law: {right['source_act']}, {right['source_section']}")
        print(f"     {right['plain_language']}")

    print(f"\n⚡ DO THIS NOW")
    for action in response.get("actions", []):
        lawyer = " [lawyer needed]" if action.get("requires_lawyer") else ""
        print(f"\n  {action['priority']}. {action['action']}{lawyer}")
        print(f"     {action['what_to_do']}")

    if response.get("forms"):
        print(f"\n📄 FORMS & DOCUMENTS")
        for form in response["forms"]:
            print(f"\n  • {form['name']}")
            print(f"    {form['purpose']}")
            print(f"    Get it: {form['where_to_get']}")

    print(f"\n  Sources: {', '.join(response.get('sources', []))}")
    print(f"\n  ⚠ {response.get('disclaimer', '')}")
    print(f"{'='*60}\n")


# ── Interactive mode ──────────────────────────────────────────────────────────

def interactive(vectorstore, forced_lang=None):
    print("\nAdhikar — Legal First-Responder")
    print("Type your situation in any language. Type 'quit' to exit.\n")

    while True:
        try:
            query = input("Your situation: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break

        if query.lower() in ("quit", "exit", "q"):
            break
        if not query:
            continue

        try:
            response = run_pipeline(query, vectorstore, forced_lang)
            if response.get("clarification_needed"):
                print(f"\n  Adhikar: {response['clarification_question']}\n")
            else:
                print_response(response)
        except Exception as e:
            print(f"\n  Error: {e}\n")


# ── Test ──────────────────────────────────────────────────────────────────────

def test(vectorstore):
    test_cases = [
        ("Police arrived at my house at 11pm and want to take me without a warrant.", "en"),
        ("पुलिस बिना वारंट के मुझे गिरफ्तार करना चाहती है।", "hi"),
        ("मेरे मकान मालिक ने बिना नोटिस के मुझे घर से निकाल दिया।", "hi"),
    ]

    print("\n=== PIPELINE TEST ===\n")
    vs = vectorstore
    for i, (query, expected_lang) in enumerate(test_cases, 1):
        print(f"\n--- TEST {i} ---")
        print(f"Query: {query}")
        try:
            response = run_pipeline(query, vs)
            detected = response.get("detected_lang", "?")
            n_rights = len(response.get("rights", []))
            n_actions = len(response.get("actions", []))
            lang_ok = "✓" if detected == expected_lang else f"✗ (got {detected})"
            print(f"  Language detection: {lang_ok}")
            print(f"  Rights returned: {n_rights}")
            print(f"  Actions returned: {n_actions}")
            if n_rights > 0:
                print(f"  First right: {response['rights'][0]['right']}")
            print(f"  ✓ Test {i} passed")
        except Exception as e:
            print(f"  ✗ Test {i} failed: {e}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test",  action="store_true", help="Run test cases")
    parser.add_argument("--lang",  type=str, default=None, help="Force output language (en/hi/kn/ta/te)")
    args = parser.parse_args()

    print("Loading vector store...")
    vs = load_vectorstore()
    print("✓ Ready\n")

    if args.test:
        test(vs)
    else:
        interactive(vs, forced_lang=args.lang)
