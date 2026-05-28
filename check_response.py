import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from agents.rights_agent import run_rights_agent

emb = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
vs = Chroma(
    persist_directory="./db",
    embedding_function=emb,
    collection_name="legal_corpus",
)

query = "Police are threatening me and using physical force during questioning at the station."
domain = "police_fir"

# same dedup logic as evaluate.py
all_chunks = vs.similarity_search(query, k=10, filter={"domain": domain})
seen = set()
chunks = []
for c in all_chunks:
    key = c.metadata.get("section", "")
    if key not in seen:
        seen.add(key)
        chunks.append(c)
        if len(chunks) == 5:
            break

with open("raw_response.txt", "w", encoding="utf-8") as f:
    f.write("=== CHUNKS SENT TO AGENT ===\n")
    for i, c in enumerate(chunks):
        f.write(f"\nChunk {i+1}: {c.metadata}\n")
        f.write(f"  Text preview: {c.page_content[:120]}\n")

    f.write("\n=== AGENT RESPONSE ===\n")
    response = run_rights_agent(query, domain, chunks)
    if hasattr(response, "model_dump"):
        f.write(json.dumps(response.model_dump(), indent=2, ensure_ascii=False))
    else:
        f.write(str(response))

print("Done — see raw_response.txt")
