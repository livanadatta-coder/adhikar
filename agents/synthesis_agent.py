"""
agents/synthesis_agent.py — Phase 2, Week 2
The final agent in the Adhikar pipeline.

Takes outputs from Rights, Actions, and Forms agents and merges them
into the single ResponseSchema that the frontend renders.

No LLM call — pure Python merge with validation.
This is what the frontend/Streamlit UI will consume directly.

Run directly to test (uses all mocks — zero API calls):
    python agents/synthesis_agent.py
"""

import sys
from pathlib import Path
from typing import Optional
from pydantic import BaseModel


# ── Final ResponseSchema (this is what the frontend gets) ─────────────────────

class Right(BaseModel):
    right: str
    source_act: str
    source_section: str
    plain_language: str

class Action(BaseModel):
    action: str
    what_to_do: str
    priority: int
    requires_lawyer: bool

class Form(BaseModel):
    name: str
    purpose: str
    where_to_get: str
    url: Optional[str]
    notes: Optional[str]

class ResponseSchema(BaseModel):
    domain: str
    rights: list[Right]       # 2-4 items
    actions: list[Action]     # 2-4 items, sorted by priority
    forms: list[Form]         # 0-3 items
    disclaimer: str
    sources: list[str]        # deduplicated across all three agents


# ── Synthesis function ────────────────────────────────────────────────────────

def run_synthesis_agent(
    domain: str,
    rights_response,
    actions_response,
    forms_response,
) -> ResponseSchema:
    """
    Merges outputs from the three specialist agents into ResponseSchema.

    Accepts the response objects from:
        rights_agent.RightsResponse
        actions_agent.ActionsResponse
        forms_agent.FormsResponse

    Returns a single validated ResponseSchema.
    """

    # Merge and deduplicate sources across all three agents
    all_sources = (
        list(rights_response.sources) +
        list(actions_response.sources) +
        list(forms_response.sources)
    )
    # Deduplicate while preserving order
    seen = set()
    deduped_sources = []
    for s in all_sources:
        if s not in seen:
            seen.add(s)
            deduped_sources.append(s)

    # Convert each agent's output to ResponseSchema types
    # (field names are identical so this is straightforward)
    rights = [Right(**r.model_dump()) for r in rights_response.rights]
    actions = [Action(**a.model_dump()) for a in actions_response.actions]
    forms = [Form(**f.model_dump()) for f in forms_response.forms]

    # Enforce sort order on actions (should already be sorted, but guarantee it)
    actions.sort(key=lambda a: a.priority)

    # Cap lengths per spec: 2-4 rights, 2-4 actions, 0-3 forms
    rights = rights[:4]
    actions = actions[:4]
    forms = forms[:3]

    # Use the rights agent's disclaimer (they're all identical, but be explicit)
    disclaimer = rights_response.disclaimer

    return ResponseSchema(
        domain=domain,
        rights=rights,
        actions=actions,
        forms=forms,
        disclaimer=disclaimer,
        sources=deduped_sources,
    )


def print_response(response: ResponseSchema):
    print("\n" + "="*60)
    print(f"ADHIKAR RESPONSE — {response.domain.upper().replace('_', ' ')}")
    print("="*60)

    print("\n── YOUR RIGHTS ──────────────────────────────────────────")
    for i, right in enumerate(response.rights, 1):
        print(f"\n  {i}. {right.right}")
        print(f"     Law: {right.source_act}, {right.source_section}")
        print(f"     {right.plain_language}")

    print("\n── DO THIS NOW ──────────────────────────────────────────")
    for action in response.actions:
        lawyer_tag = " [needs lawyer]" if action.requires_lawyer else ""
        print(f"\n  {action.priority}. {action.action}{lawyer_tag}")
        print(f"     {action.what_to_do}")

    if response.forms:
        print("\n── FORMS & DOCUMENTS ────────────────────────────────────")
        for i, form in enumerate(response.forms, 1):
            print(f"\n  {i}. {form.name}")
            print(f"     {form.purpose}")
            print(f"     Where: {form.where_to_get}")
            if form.url:
                print(f"     Link: {form.url}")

    print(f"\n── SOURCES ──────────────────────────────────────────────")
    for s in response.sources:
        print(f"  • {s}")

    print(f"\n⚠  {response.disclaimer}")
    print("="*60)


# ── Full pipeline test (all mocks, zero API calls) ────────────────────────────

def test():
    sys.path.append(str(Path(__file__).parent.parent))

    # Import mock agents
    from agents.rights_agent import run_rights_agent as run_mock_rights_agent, RightsResponse
    from agents.actions_agent import run_actions_agent as run_mock_actions_agent, ActionsResponse
    from agents.classifier_agent import run_classifier_agent as run_mock_classifier_agent, ClassifierResponse
    from agents.forms_agent import run_forms_agent, FormsResponse 
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma

    print("\n=== SYNTHESIS AGENT TEST — FULL PIPELINE (MOCK) ===")
    print("Zero API calls — all agents mocked except forms (DB lookup)\n")

    # Load vector store once
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
        "Police came to my house at night and want to arrest me without showing a warrant.",
        "I was arrested and held for 30 hours without being taken to a magistrate.",
        "Police are refusing to file my FIR. What can I do?",
    ]

    passed = 0
    for i, query in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {query}")

        try:
            # Stage 1: Classify
            classifier_result = run_mock_classifier_agent(query)
            domain = classifier_result.domain
            print(f"  Classifier → {domain} ({classifier_result.confidence:.0%} confidence)")

            if classifier_result.clarification_needed:
                print(f"  ⚠ Clarification needed: {classifier_result.clarification_question}")
                print(f"  Skipping — would ask user before continuing")
                continue

            # Stage 2: Retrieve
            chunks = vectorstore.similarity_search(
                query, k=4, filter={"domain": domain}
            )
            print(f"  Retrieval → {len(chunks)} chunks")

            # Stage 3: Run specialist agents
            rights_result = run_mock_rights_agent(query, domain, chunks)
            actions_result = run_mock_actions_agent(query, domain, chunks)
            forms_result = run_forms_agent(query, domain)
            print(f"  Agents → {len(rights_result.rights)} rights, "
                  f"{len(actions_result.actions)} actions, "
                  f"{len(forms_result.forms)} forms")

            # Stage 4: Synthesise
            final = run_synthesis_agent(domain, rights_result, actions_result, forms_result)

            # Validate final schema
            assert len(final.rights) >= 2, "Too few rights"
            assert len(final.actions) >= 2, "Too few actions"
            assert final.actions == sorted(final.actions, key=lambda a: a.priority), \
                "Actions not sorted"
            assert len(final.sources) > 0, "No sources"
            assert final.disclaimer, "Missing disclaimer"
            # No duplicate sources
            assert len(final.sources) == len(set(final.sources)), "Duplicate sources"

            print_response(final)
            print(f"\n✓ Test {i} passed — full pipeline working end-to-end")
            passed += 1

        except Exception as e:
            print(f"\n✗ Test {i} failed: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"SYNTHESIS TEST RESULT: {passed}/{len(test_cases)} passed")
    if passed == len(test_cases):
        print("\n✓ WEEK 2 MILESTONE COMPLETE")
        print("  Full pipeline: Classifier → Retrieval → Rights + Actions + Forms → Synthesis")
        print("  When API quota resets: swap mock agents → real agents, run the same test.")
    print("="*60)


if __name__ == "__main__":
    test()
