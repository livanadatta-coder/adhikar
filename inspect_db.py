from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

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

print("=== ALL chunks in DB (no filter) ===")
all_results = vs.similarity_search("rights arrested person", k=50)
for r in all_results:
    print(r.metadata.get("act"), "|", r.metadata.get("section"), "|", r.metadata.get("domain"))

print("\n=== Chunks with domain=police_fir ===")
filtered = vs.similarity_search("Article 21 Article 22 D.K. Basu arrested", k=20, filter={"domain": "police_fir"})
for r in filtered:
    print(r.metadata.get("act"), "|", r.metadata.get("section"), "|", r.metadata.get("domain"))
