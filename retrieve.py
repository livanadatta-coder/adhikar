"""
retrieve.py — Phase 1, Week 1
Interactive retrieval tester. This IS your Week 1 milestone.

Usage:
    python retrieve.py           # interactive mode
    python retrieve.py --test    # runs the 10 golden test queries automatically
"""

import argparse
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
DB_DIR = "./db"
COLLECTION_NAME = "legal_corpus"

# ── 10 test queries for the Police/FIR domain ─────────────────────────────────
# These represent real scenarios your users will face.
# By end of Week 2, all 10 should return relevant chunks.
TEST_QUERIES = [
    "Police came to my house and want to take me to the station without a warrant",
    "Can police arrest me without showing any document?",
    "I was arrested and not told why. What are my rights?",
    "How do I file an FIR? Police are refusing to register my complaint",
    "Police are holding me for more than 24 hours without producing me before a magistrate",
    "What is default bail? I have been in custody for 60 days without charge sheet",
    "Police did not allow me to call my family after arrest",
    "I want to file an FIR but police say it is not a cognisable offence",
    "What are the D.K. Basu guidelines?",
    "I was arrested for a bailable offence. Can they deny me bail?",
]


def load_retriever():
    if not Path(DB_DIR).exists():
        raise FileNotFoundError(
            f"Database not found at {DB_DIR}/. Run build_db.py first."
        )
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    vectorstore = Chroma(
        persist_directory=DB_DIR,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )
    return vectorstore


def retrieve(vectorstore, query: str, k: int = 5, domain: str = "police_fir"):
    """MMR retrieval scoped to a domain."""
    results = vectorstore.max_marginal_relevance_search(
        query,
        k=k,
        fetch_k=20,
        filter={"domain": domain},
    )
    return results


def print_results(query: str, results: list):
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    if not results:
        print("No results found. Check that build_db.py ran successfully.")
        return
    for i, doc in enumerate(results, 1):
        m = doc.metadata
        print(f"\n  [{i}] {m['act']} § {m['section']} — {m['title']}")
        print(f"      Source: {m['source']}")
        print(f"      {doc.page_content[:300].strip()}...")


def run_test_mode(vectorstore):
    print("\n=== ADHIKAR — WEEK 1 MILESTONE TEST ===")
    print(f"Running {len(TEST_QUERIES)} test queries against Police/FIR corpus\n")
    hits = 0
    for i, query in enumerate(TEST_QUERIES, 1):
        results = retrieve(vectorstore, query)
        has_results = len(results) > 0
        status = "✓" if has_results else "✗"
        print(f"  {status} [{i:02d}] {query[:65]}...")
        if has_results:
            top = results[0].metadata
            print(f"       Top hit: {top['act']} §{top['section']}")
            hits += 1

    print(f"\nResult: {hits}/{len(TEST_QUERIES)} queries returned results")
    if hits == len(TEST_QUERIES):
        print("✓ WEEK 1 MILESTONE PASSED — move on to Week 2 (agent layer)")
    else:
        print("✗ Some queries returned no results. Add more seed data to corpus/raw/")


def run_interactive(vectorstore):
    print("\n=== ADHIKAR RETRIEVAL — Interactive Mode ===")
    print("Type a legal query. Press Ctrl+C to exit.\n")
    while True:
        try:
            query = input("Your query: ").strip()
            if not query:
                continue
            results = retrieve(vectorstore, query)
            print_results(query, results)
        except KeyboardInterrupt:
            print("\n\nExiting.")
            break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Run golden test set")
    args = parser.parse_args()

    print("Loading vector store...")
    vectorstore = load_retriever()
    print("✓ Vector store loaded")

    if args.test:
        run_test_mode(vectorstore)
    else:
        run_interactive(vectorstore)


if __name__ == "__main__":
    main()
