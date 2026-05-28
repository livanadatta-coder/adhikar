from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

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

queries = [
    ("police arrest warrant rights", "police_fir"),
    ("D.K. Basu custody guidelines", "police_fir"),
    ("Article 22 fundamental rights arrest", "police_fir"),
]

with open("db_check.txt", "w") as f:
    for query, domain in queries:
        f.write(f"\n=== Query: {query} ===\n")
        docs = vs.similarity_search(query, k=5, filter={"domain": domain})
        for i, d in enumerate(docs):
            f.write(f"  Doc {i+1}: {d.metadata}\n")

print("Done — see db_check.txt")
