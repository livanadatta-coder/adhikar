"""
build_db.py — Phase 1, Week 1
Loads scraped JSON docs, chunks them, embeds them, and stores in ChromaDB.

Run AFTER scraper.py:
    python build_db.py

Output: db/ folder (ChromaDB vector store)
"""

import json
import os
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

RAW_DIR = Path("corpus/raw")
DB_DIR = "./db"
COLLECTION_NAME = "legal_corpus"


def load_corpus(corpus_dir: Path) -> list[Document]:
    docs = []
    files = list(corpus_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(
            f"No JSON files found in {corpus_dir}. Run scraper.py first."
        )
    for fpath in files:
        with open(fpath, encoding="utf-8") as f:
            d = json.load(f)
        docs.append(Document(
            page_content=d["text"],
            metadata={
                "source":  d.get("source", "unknown"),
                "domain":  d.get("domain", "unknown"),
                "act":     d.get("act", "unknown"),
                "section": d.get("section", "unknown"),
                "title":   d.get("title", "unknown"),
            }
        ))
    print(f"Loaded {len(docs)} documents from {corpus_dir}")
    return docs


def chunk_documents(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_documents(docs)
    print(f"Split into {len(chunks)} chunks (800 chars, 150 overlap)")
    return chunks


def build_vectorstore(chunks: list[Document]) -> Chroma:
    print("Loading embedding model (downloads ~80MB on first run)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    print(f"Building vector store in {DB_DIR}/ ...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_DIR,
        collection_name=COLLECTION_NAME,
    )
    print(f"Vector store built and persisted to {DB_DIR}/")
    return vectorstore


def sanity_check(vectorstore: Chroma):
    print("\n--- Sanity check: querying 'police arrest without warrant' ---")
    results = vectorstore.similarity_search(
        "police arrest without warrant", k=3, filter={"domain": "police_fir"}
    )
    for i, doc in enumerate(results, 1):
        print(f"\nResult {i}: [{doc.metadata['act']} §{doc.metadata['section']}]")
        print(f"  {doc.page_content[:200]}...")
    print("\nSanity check passed — retrieval is working.")


def run():
    print("\n=== ADHIKAR BUILD DB — Phase 1 ===\n")
    docs = load_corpus(RAW_DIR)
    chunks = chunk_documents(docs)
    vectorstore = build_vectorstore(chunks)
    sanity_check(vectorstore)
    print("\nNext step: run  python retrieve.py")


if __name__ == "__main__":
    run()
