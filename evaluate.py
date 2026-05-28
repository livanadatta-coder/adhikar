"""
Adhikar Evaluation Harness
Usage:
    python evaluate.py              # runs all 30 scenarios with live agents
    python evaluate.py --mock       # runs with mock agents (no API calls)
    python evaluate.py --domain police_fir   # run one domain only
    python evaluate.py --id PF001   # run single scenario by ID
"""

import json
import argparse
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

GOLDEN_SET_PATH = Path("data/golden_set.json")

# ── source normalisation ──────────────────────────────────────────────────────
NORMALISATION_MAP = {
    "crpc 41":          "Section 41 CrPC",
    "section 41 crpc":  "Section 41 CrPC",
    "section 41":       "Section 41 CrPC",
    "§41":              "Section 41 CrPC",
    "crpc 41a":         "Section 41A CrPC",
    "section 41a crpc": "Section 41A CrPC",
    "section 41a":      "Section 41A CrPC",
    "crpc 50":          "Section 50 CrPC",
    "section 50 crpc":  "Section 50 CrPC",
    "section 50":       "Section 50 CrPC",
    "§50":              "Section 50 CrPC",
    "crpc 57":          "Section 57 CrPC",
    "section 57 crpc":  "Section 57 CrPC",
    "crpc 154":         "Section 154 CrPC",
    "section 154 crpc": "Section 154 CrPC",
    "section 154":      "Section 154 CrPC",
    "§154":             "Section 154 CrPC",
    "crpc 167":         "Section 167 CrPC",
    "section 167 crpc": "Section 167 CrPC",
    "section 167":      "Section 167 CrPC",
    "crpc 437":         "Section 437 CrPC",
    "section 437 crpc": "Section 437 CrPC",
    "code of criminal procedure, 1973, section 41":  "Section 41 CrPC",
    "code of criminal procedure, 1973, section 50":  "Section 50 CrPC",
    "code of criminal procedure, 1973, section 154": "Section 154 CrPC",
    "code of criminal procedure":                    "Section 41 CrPC",  # fallback — only matches bare string
    "d.k. basu":          "D.K. Basu guidelines",
    "dk basu":            "D.K. Basu guidelines",
    "d k basu":           "D.K. Basu guidelines",
    "d.k basu":           "D.K. Basu guidelines",
    "dk basu guidelines": "D.K. Basu guidelines",
    "d.k. basu guidelines": "D.K. Basu guidelines",
    "d.k. basu v. state of west bengal air 1997 sc 610": "D.K. Basu guidelines",
    "article 22":        "Article 22",
    "article 22(2)":     "Article 22",
    "art. 22":           "Article 22",
    "constitution of india article 22":    "Article 22",
    "constitution of india article 22(2)": "Article 22",
    "constitution of india article 22(1)": "Article 22",
    "article 21":        "Article 21",
    "art. 21":           "Article 21",
    "constitution of india article 21": "Article 21",
    "consumer protection act 2019":          "Consumer Protection Act 2019",
    "consumer protection act, 2019":         "Consumer Protection Act 2019",
    "cpa 2019":                              "Consumer Protection Act 2019",
    "transfer of property act":              "Transfer of Property Act",
    "topa":                                  "Transfer of Property Act",
    "maharashtra rent control act":          "Maharashtra Rent Control Act",
    "mhrca":                                 "Maharashtra Rent Control Act",
    "rera":                                  "RERA Act",
    "d.k. basu v. state of west bengal, air 1997 sc 610": "D.K. Basu guidelines",
    "constitution of india, article 22": "Article 22",
    "constitution of india, article 21": "Article 21",
    "constitution of india, article 22(1)": "Article 22",
    "constitution of india, article 22(2)": "Article 22",
    "crpc section 41":   "Section 41 CrPC",
    "crpc section 41a":  "Section 41A CrPC",
    "crpc section 50":   "Section 50 CrPC",
    "crpc section 154":  "Section 154 CrPC",
    "crpc section 167":  "Section 167 CrPC",
    "crpc section 437":  "Section 437 CrPC",
    "crpc section 46":   "Section 46 CrPC",
    "crpc section 50a":  "Section 50A CrPC",
    "crpc section 57":   "Section 57 CrPC",
    "crpc section 165":  "Section 165 CrPC",
    "code of criminal procedure, 1973 - section 41":   "Section 41 CrPC",
    "code of criminal procedure, 1973 - section 41a":  "Section 41A CrPC",
    "code of criminal procedure, 1973 - section 46":   "Section 46 CrPC",
    "code of criminal procedure, 1973 - section 50":   "Section 50 CrPC",
    "code of criminal procedure, 1973 - section 50a":  "Section 50A CrPC",
    "code of criminal procedure, 1973 - section 57":   "Section 57 CrPC",
    "code of criminal procedure, 1973 - section 154":  "Section 154 CrPC",
    "code of criminal procedure, 1973 - section 165":  "Section 165 CrPC",
    "code of criminal procedure, 1973 - section 167":  "Section 167 CrPC",
    "code of criminal procedure, 1973 - section 437":  "Section 437 CrPC",
    "code of criminal procedure, 1973 - section 46(4)": "Section 46 CrPC",
    "constitution of india - article 21":  "Article 21",
    "constitution of india - article 22":  "Article 22",
    "constitution of india - article 22(1)": "Article 22",
    "constitution of india - article 22(2)": "Article 22",
    "constitution of india article 22(1)": "Article 22",
    "code of criminal procedure, 1973, section 46":  "Section 46 CrPC",
    "code of criminal procedure, 1973, section 165": "Section 165 CrPC",
    "code of criminal procedure, 1973, section 167": "Section 167 CrPC",
    "code of criminal procedure, 1973, section 437": "Section 437 CrPC",
    "code of criminal procedure, 1973, section 57":  "Section 57 CrPC",
    "code of criminal procedure, 1973, section 50a": "Section 50A CrPC",
    "section 46(4) code of criminal procedure, 1973": "Section 46 CrPC",
    "section 46(4)": "Section 46 CrPC",
}
def normalise_source(s: str) -> str:
    key = s.lower().strip()
    return NORMALISATION_MAP.get(key, s.strip())

def extract_sources_from_response(response: dict) -> set:
    sources = set()
    for s in response.get("sources", []):
        sources.add(normalise_source(s))
    for right in response.get("rights", []):
        act = right.get("source_act", "")
        sec = right.get("source_section", "")
        if act and sec:
            sources.add(normalise_source(f"{sec} {act}".strip()))
            sources.add(normalise_source(act))
            sources.add(normalise_source(sec))
        elif act:
            sources.add(normalise_source(act))
    return sources

def compute_rights_recall(expected: list, response: dict) -> float:
    if not expected:
        return 1.0
    found_sources = extract_sources_from_response(response)
    rights_text = " ".join(
        r.get("right", "") + " " + r.get("plain_language", "")
        for r in response.get("rights", [])
    ).lower()
    hits = 0
    for exp in expected:
        exp_norm = normalise_source(exp)
        if exp_norm in found_sources:
            hits += 1
        elif exp.lower() in rights_text:
            hits += 1
        elif any(exp.lower() in s.lower() for s in found_sources):
            hits += 1
    return hits / len(expected)

def compute_actions_recall(expected: list, response: dict) -> float:
    if not expected:
        return 1.0
    actions_text = " ".join(
        a.get("action", "") + " " + a.get("what_to_do", "")
        for a in response.get("actions", [])
    ).lower()
    hits = 0
    for exp in expected:
        keywords = [w for w in exp.lower().split() if len(w) > 3][:3]
        if any(kw in actions_text for kw in keywords):
            hits += 1
    return hits / len(expected)

def compute_forms_recall(expected: list, response: dict) -> float:
    if not expected:
        return 1.0
    forms_text = " ".join(
        f.get("name", "") for f in response.get("forms", [])
    ).lower()
    hits = 0
    for exp in expected:
        keywords = [w for w in exp.lower().split() if len(w) > 3][:3]
        if any(kw in forms_text for kw in keywords):
            hits += 1
    return hits / len(expected)

def response_to_dict(response) -> dict:
    """Convert a Pydantic model or dict to a plain dict."""
    if hasattr(response, "model_dump"):
        return response.model_dump()
    elif hasattr(response, "dict"):
        return response.dict()
    elif isinstance(response, dict):
        return response
    else:
        return {}

def run_pipeline(scenario: str, domain: str, use_mock: bool) -> dict:
    if use_mock:
        from agents.mock_rights_agent import run_mock_rights_agent
        from agents.mock_actions_agent import run_mock_actions_agent
        from agents.forms_agent import run_forms_agent
        from agents.synthesis_agent import run_synthesis_agent

        chunks = []  # mock agents don't use chunks

        rights_response  = run_mock_rights_agent(scenario, domain, chunks)
        actions_response = run_mock_actions_agent(scenario, domain, chunks)
        forms_response   = run_forms_agent(scenario, domain)
        # synthesis signature: run_synthesis_agent(domain, rights, actions, forms)
        final = run_synthesis_agent(domain, rights_response, actions_response, forms_response)
        return response_to_dict(final)

    else:
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_chroma import Chroma
        from agents.rights_agent import run_rights_agent, retrieve_for_rights
        from agents.actions_agent import run_actions_agent
        from agents.forms_agent import run_forms_agent
        from agents.synthesis_agent import run_synthesis_agent

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

        # Rights: dual-pass retrieval (expanded query k=8 + procedural k=6)
        # This is the fix for low rights recall — do NOT share these chunks
        # with actions; rights needs its own broader retrieval pass.
        rights_chunks = retrieve_for_rights(scenario, domain, vectorstore)

        # Actions: standard retrieval, deduplicated by section, capped at 5
        all_chunks = vectorstore.similarity_search(
            scenario, k=10, filter={"domain": domain}
        )
        seen = set()
        action_chunks = []
        for c in all_chunks:
            key = c.metadata.get("section", "")
            if key not in seen:
                seen.add(key)
                action_chunks.append(c)
                if len(action_chunks) == 5:
                    break

        rights_response  = run_rights_agent(scenario, domain, rights_chunks)
        actions_response = run_actions_agent(scenario, domain, action_chunks)
        forms_response   = run_forms_agent(scenario, domain)
        final = run_synthesis_agent(domain, rights_response, actions_response, forms_response)
        return response_to_dict(final)
def evaluate_single(test_case: dict, use_mock: bool, verbose: bool = True) -> dict:
    scenario_id = test_case["id"]
    domain      = test_case["domain"]
    scenario    = test_case["scenario"]

    if verbose:
        print(f"\n{'─'*60}")
        print(f"  [{scenario_id}] {scenario[:80]}...")

    try:
        response = run_pipeline(scenario, domain, use_mock)

        rights_recall  = compute_rights_recall(test_case["expected_rights"], response)
        actions_recall = compute_actions_recall(test_case["expected_actions"], response)
        forms_recall   = compute_forms_recall(test_case["expected_forms"], response)

        if verbose:
            print(f"  Rights recall:  {rights_recall:.0%}")
            print(f"  Actions recall: {actions_recall:.0%}")
            print(f"  Forms recall:   {forms_recall:.0%}")
            if rights_recall < 1.0:
                expected_norm = [normalise_source(e) for e in test_case["expected_rights"]]
                found = extract_sources_from_response(response)
                missing = [e for e in expected_norm
                           if e not in found and not any(e.lower() in s.lower() for s in found)]
                if missing:
                    print(f"  ⚠ Missing rights: {missing}")

        return {
            "id": scenario_id, "domain": domain,
            "rights_recall": rights_recall,
            "actions_recall": actions_recall,
            "forms_recall": forms_recall,
            "error": None
        }

    except Exception as e:
        if verbose:
            print(f"  ✗ ERROR: {e}")
        return {
            "id": scenario_id, "domain": domain,
            "rights_recall": 0.0, "actions_recall": 0.0, "forms_recall": 0.0,
            "error": str(e)
        }

def print_summary(results: list):
    print(f"\n{'='*60}")
    print("  EVALUATION RESULTS")
    print(f"{'='*60}")

    domains = {}
    for r in results:
        domains.setdefault(r["domain"], []).append(r)

    for domain, dr in domains.items():
        n = len(dr)
        avg_r = sum(x["rights_recall"]  for x in dr) / n
        avg_a = sum(x["actions_recall"] for x in dr) / n
        avg_f = sum(x["forms_recall"]   for x in dr) / n
        errs  = sum(1 for x in dr if x["error"])
        print(f"\n  {domain.upper().replace('_', ' ')} ({n} scenarios, {errs} errors)")
        print(f"    Rights recall:  {avg_r:.1%}")
        print(f"    Actions recall: {avg_a:.1%}")
        print(f"    Forms recall:   {avg_f:.1%}")

    total = len(results)
    overall_r = sum(x["rights_recall"]  for x in results) / total
    overall_a = sum(x["actions_recall"] for x in results) / total
    overall_f = sum(x["forms_recall"]   for x in results) / total
    errs      = sum(1 for x in results if x["error"])

    print(f"\n  OVERALL ({total} scenarios, {errs} errors)")
    print(f"    Rights recall:  {overall_r:.1%}  {'✓ PASS' if overall_r >= 0.75 else '✗ BELOW TARGET (need 75%)'}")
    print(f"    Actions recall: {overall_a:.1%}")
    print(f"    Forms recall:   {overall_f:.1%}")
    print(f"{'='*60}\n")

    if overall_r >= 0.75:
        print("  ✓ Pipeline cleared for multilingual layer (Week 5)")
    else:
        print("  ✗ Fix retrieval or Rights Agent prompt before proceeding")
        print("    Check: corpus coverage, chunking, MMR filter, prompt constraints")

def main():
    parser = argparse.ArgumentParser(description="Adhikar evaluation harness")
    parser.add_argument("--mock",   action="store_true")
    parser.add_argument("--domain", type=str, default=None)
    parser.add_argument("--id",     type=str, default=None)
    parser.add_argument("--quiet",  action="store_true")
    args = parser.parse_args()

    if not GOLDEN_SET_PATH.exists():
        print(f"ERROR: {GOLDEN_SET_PATH} not found — copy golden_set.json into data/")
        sys.exit(1)

    with open(GOLDEN_SET_PATH) as f:
        golden_set = json.load(f)

    if args.id:
        golden_set = [tc for tc in golden_set if tc["id"] == args.id]
        if not golden_set:
            print(f"ERROR: no test case with id '{args.id}'"); sys.exit(1)

    if args.domain:
        golden_set = [tc for tc in golden_set if tc["domain"] == args.domain]
        if not golden_set:
            print(f"ERROR: no test cases for domain '{args.domain}'"); sys.exit(1)

    mode = "MOCK" if args.mock else "LIVE"
    print(f"\nAdhikar Evaluation Harness — {mode} mode — {len(golden_set)} scenarios")

    import time
    results = []
    for tc in golden_set:
        result = evaluate_single(tc, use_mock=args.mock, verbose=not args.quiet)
        results.append(result)
        if not args.mock and not result["error"]:
            time.sleep(5)  # stay under Groq TPD limit

    if len(results) > 1:
        print_summary(results)

    Path("evaluation").mkdir(exist_ok=True)
    out = Path("evaluation") / f"results_{'mock' if args.mock else 'live'}.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  Results saved to {out}\n")

if __name__ == "__main__":
    main()
