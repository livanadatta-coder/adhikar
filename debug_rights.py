"""
debug_rights.py — run from adhikar\ root
Prints the raw RightsResponse for the 3 worst-scoring scenarios
so we can see exactly what the LLM is returning vs what the evaluator expects.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from agents.rights_agent import run_rights_agent, retrieve_for_rights

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
vs = Chroma(
    persist_directory="./db",
    embedding_function=embeddings,
    collection_name="legal_corpus",
)

scenarios = [
    # (id, query)
    ("PF001", "Police arrived at my house at 11pm and want to take me to the police station without showing me an arrest warrant. What are my rights?"),
    ("PF009", "The police searched my house without a warrant and took away my belongings."),
    ("PF010", "I am a woman and was arrested after sunset. Is this legal?"),
]

for sid, query in scenarios:
    print(f"\n{'='*60}")
    print(f"[{sid}] {query}")
    domain = "police_fir"

    chunks = retrieve_for_rights(query, domain, vs)
    print(f"\nChunks passed to LLM ({len(chunks)}):")
    for c in chunks:
        print(f"  {c.metadata.get('act')} | {c.metadata.get('section')}")

    response = run_rights_agent(query, domain, chunks)

    print(f"\nRights returned:")
    for r in response.rights:
        print(f"  - {r.right} | {r.source_act} | {r.source_section}")

    print(f"\nSources list:")
    for s in response.sources:
        print(f"  - {s}")
