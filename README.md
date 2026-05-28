# Adhikar — Legal First-Responder for India

AI-powered legal information system that tells Indians their rights in their own language — built for the person standing in a police station who doesn't know what the law says.

Adhikar takes a situation described in Hindi, Kannada, Tamil, Telugu, or English and returns three things: what your rights are (cited to the actual law), what to do right now, and what forms you need. Every response is grounded in retrieved legal documents — the system cannot hallucinate citations.

---

## How it works

User describes their situation → language is detected and translated to English → classified into a legal domain → relevant legal chunks retrieved from ChromaDB → three specialist agents (Rights, Actions, Forms) run in parallel → structured response translated back to the user's language.

The vector store and all LLM calls stay in English. Translation only happens at the edges.

---

## Stack

Python · LangChain · ChromaDB · Groq (llama-3.3-70b) · Pydantic · sentence-transformers · deep-translator

---

## Status

- ✅ Phase 1 — RAG pipeline + ChromaDB (24 legal documents, 50 chunks)
- ✅ Phase 2 — Multi-agent pipeline · 75% rights recall on police/FIR · 100% on eviction
- 🔄 Phase 3 — Multilingual layer (in progress)
- ⬜ Phase 4 — Streamlit frontend · emergency rights card · offline mode · deployment

---

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Add a `.env` file with `GROQ_API_KEY=your_key`. Get a free key at console.groq.com.

```bash
python build_db.py    # build vector store
python retrieve.py    # test retrieval
python evaluate.py    # run 30-scenario evaluation
```

---

*Built by Livana Datta · MIT Bangalore*
