# Adhikar — Legal First-Responder for India

**Adhikar** (Sanskrit/Hindi for "right" or "entitlement") is an AI-powered legal information system built for the person standing in a police station, in front of a landlord, or in a government office, who doesn't know what the law says. You describe a situation in plain language — in English, Hindi, Kannada, Tamil, or Telugu — and Adhikar tells you three things, every time:

1. **Your rights** — grounded in the actual law, with Act and Section cited
2. **What to do right now** — concrete, prioritised, plain-language steps
3. **What forms or documents you need** — and where to get them

Every legal claim Adhikar makes is retrieved from a curated corpus of Indian statutes, constitutional articles, and landmark judgments before the LLM ever sees the question. The system is built so it **cannot answer from memory** — if the law isn't in the retrieved context, the agent has nothing to cite.

> ⚠️ **This is legal information, not legal advice.** Every response carries a disclaimer pointing to the NALSA helpline (15100) for case-specific guidance.

---

## Why this exists

Most people who need to know their legal rights in the moment — during an arrest, an eviction, a wage dispute — don't have a lawyer on call and don't read legal English. Generic LLMs will answer confidently and get section numbers wrong, which is worse than not answering at all. Adhikar's core design bet is **retrieval-grounding over fluency**: every specialist agent is instructed to refuse to speculate beyond the documents it's given, and the documents it's given come from a vetted corpus, not the open web.

---

## System architecture

```
                              ┌─────────────────────┐
                              │   React Frontend     │
                              │  (Vite + components) │
                              └──────────┬───────────┘
                                         │ REST (fetch)
                              ┌──────────▼───────────┐
                              │   FastAPI  (api.py)   │
                              │  /query /transcribe    │
                              │  /documents/*  /health │
                              └──────────┬───────────┘
                                         │
                    ┌────────────────────┼─────────────────────┐
                    │                    │                     │
            documents domain      legal domains (×7)      voice input
                    │                    │                     │
        ┌───────────▼─────────┐  ┌──────▼───────────┐  ┌───────▼────────┐
        │  documents_agent.py  │  │   pipeline.py      │  │ transcriber.py │
        │  keyword match → LLM │  │   (orchestrator)   │  │ local Whisper  │
        │  fallback → JSON     │  └──────┬─────────────┘  │ "small" model  │
        │  corpus lookup       │         │                └────────────────┘
        └──────────────────────┘         │
                                          ▼
                  1. detect_language()  →  translate_to_english()
                                          ▼
                  2. classifier_agent  →  domain (1 of 7) + confidence
                                          ▼
                  3. retrieve_for_rights() — 3-pass ChromaDB search
                                          ▼
                  4. ┌─────────────┬──────────────┬─────────────┐
                     │ rights_agent│ actions_agent │ forms_agent │  (parallel,
                     │  (Groq LLM) │  (Groq LLM)   │ (JSON + LLM │   all on
                     │             │               │  fallback)  │   llama-3.3-70b)
                     └─────────────┴──────────────┴─────────────┘
                                          ▼
                  5. synthesis_agent — pure-Python merge, no LLM call
                                          ▼
                  6. translate_response() back to user's language
                                          ▼
                              ResponseSchema → frontend
```

The vector store and every LLM call operate in **English only**. Translation happens exclusively at the two edges of the pipeline, keeping retrieval quality and prompt engineering independent of which of the five languages the user typed in.

**Stack:** Python · FastAPI · LangChain · ChromaDB · Groq (`llama-3.3-70b-versatile`) · Pydantic · `sentence-transformers` (`all-MiniLM-L6-v2`) · `deep-translator` · local Whisper (`small`) · ReportLab · React + Vite

---

## The two kinds of queries

Adhikar routes to **two different systems** depending on what you ask, both exposed through the same `/query` endpoint:

| Type | Domains | How it answers |
|---|---|---|
| **Legal RAG pipeline** | `police_fir`, `eviction_housing`, `workplace_salary`, `consumer_fraud`, `domestic_violence`, `land_property`, `court_bail`, `government_schemes` | Full 7-stage pipeline below — classify → retrieve → 3 specialist agents → synthesise |
| **Document guidance** | `documents` (Aadhaar, PAN, Voter ID, Passport, Birth/Marriage/Death certificates, Sale Deed, Land Records, Encumbrance Certificate — 11 document types total) | Bypasses the vector store entirely — keyword match against a structured JSON corpus, LLM fallback only for ambiguous phrasing |

This split exists because government document requirements are **stable and procedural** — "what do I need for a passport" doesn't change month to month and doesn't need semantic search over legal text. A cheap keyword pre-check in `classifier_agent.py` catches document queries before the legal classifier even runs, so they never touch ChromaDB or the 7-stage pipeline.

---

## The multi-agent pipeline, step by step

For the 8 legal domains, `pipeline.py` runs this sequence:

**1. Language detection** — `langdetect` identifies the input language.

**2. Translate to English** — via `deep-translator` (Google Translate backend). No-op if already English.

**3. Classify** — a Groq call sorts the English query into exactly one of 8 domains, with a confidence score. If confidence is below 0.6, the agent asks a clarifying question instead of guessing.

**4. Retrieve** — a 3-pass ChromaDB similarity search (see below) returns up to 12 deduplicated, domain-filtered chunks.

**5. Three specialist agents run on the same chunks:**

- **Rights agent** — "what are my rights here, cited to law." Forced to use **only** the retrieved documents; the prompt explicitly forbids inventing section numbers and instructs the model to prioritise constitutional articles (21, 22) and the D.K. Basu guidelines whenever they're present.
- **Actions agent** — "what do I do in the next few hours." Outputs are ranked by `priority` and each carries a `requires_lawyer` boolean, with an explicit allow-list (filing an FIR, going to a magistrate, calling a helpline) and deny-list (writ petitions, contested hearings, civil suits) baked into the prompt.
- **Forms agent** — looks up relevant forms from a static `forms_db.json` first; only calls the LLM for situations the database doesn't cover.

**6. Synthesis** — the one stage with **no LLM call at all**. A pure-Python merge: deduplicate sources across all three agents, enforce the 2–4 rights / 2–4 actions / 0–3 forms cap, sort actions by priority, and validate the whole thing against a single Pydantic `ResponseSchema` — the schema the frontend renders directly.

**7. Translate back** — translates only the human-readable text fields (right titles, plain-language explanations, action text, form names) — never the Act/Section citations, URLs, or the `priority`/`domain` fields, which must stay exact regardless of UI language.

---

## Retrieval: the hard problem and how it was solved

The hardest engineering problem in this project was that **users don't talk the way the law is written.** Someone typing "police beat me and won't let me call my family" needs to retrieve the D.K. Basu custodial guidelines and Article 21 — but those chunks don't share much vocabulary with the user's sentence.

The fix, in `agents/rights_agent.py`, is a **three-pass retrieval strategy**:

| Pass | k | Query | Purpose |
|---|---|---|---|
| 1a | 6 | Fixed anchor on Article 21/22 | Always pulls constitutional rights chunks regardless of phrasing |
| 1b | 4 | Separate fixed anchor for D.K. Basu | D.K. Basu's procedural vocabulary doesn't embed close to user queries or the constitutional anchor — it needed its own dedicated pass |
| 2 | 8 | User query + domain-specific legal-terminology expansion | Bridges plain language to the way the corpus is actually phrased |
| 3 | 6 | Original, unmodified user query | Catches procedural chunks the user's own words already match well |

All chunks are pooled, deduplicated by `(act, section)` metadata, and capped at 12 before being handed to the rights/actions agents. This raised rights recall from ~41% to **75%+ on police/FIR and 100% on eviction/housing**.

---

## Multilingual layer

`utils/translator.py` implements a **translate-at-the-edges** design: the vector store, every prompt, and every LLM call work in English only. Input is detected and translated to English before classification; the final response is translated back to the user's language as the last step. This keeps retrieval quality, prompt engineering, and evaluation work done once, in English, instead of five times — and is structured so swapping in IndicTrans2 later only means replacing two functions.

Supported languages: English, Hindi, Kannada, Tamil, Telugu.

---

## Voice input

`utils/transcriber.py` wraps **local OpenAI Whisper** (`small` model, CPU inference) as a pre-processing step in front of the pipeline — no API key, no per-request cost, works offline. The frontend's mic button records via `MediaRecorder`, sends the audio to `/transcribe`, and if Whisper detects a non-English language, the UI automatically switches to match.

---

## Emergency rights card (PDF)

`utils/rights_card.py` generates a printable A5 PDF — styled to match the frontend's palette — that a user can show directly to a police officer or landlord. Built with ReportLab: a header banner, a numbered rights section with citations, and a footer with the NALSA helpline.

---

## Frontend

A React (Vite) single-page app:

- **`App.jsx`** — top-level state, tab navigation (⚖️ Get Help / 📋 Documents), mic recording, language switching
- **`CategoryGrid.jsx`** — landing-state tiles for each legal domain with example prompts
- **`ResponseCard.jsx`** — renders the rights / actions / forms / disclaimer / sources schema
- **`DocumentsTab.jsx`** — browsable directory of all 11 document types with an interactive checklist and step-by-step accordion
- **`DocumentsResultCard.jsx`** — inline chat card for document queries, with a CTA into the Documents tab
- **`LanguageSelector.jsx`**, **`LoadingSpinner.jsx`** — supporting UI
- **`api/adhikar.js`** — fetch client talking to `/query`, `/transcribe`, `/documents/list`, `/documents/{doc_id}`

---

## Project structure

```
adhikar-main/
├── api.py                     FastAPI app — all HTTP endpoints
├── pipeline.py                Orchestrator for the 7-stage legal RAG pipeline
├── build_db.py                Chunk corpus/raw/*.json → embed → persist to ChromaDB
├── scraper.py                 Corpus collection from source legal texts
├── retrieve.py                Standalone retrieval testing
├── evaluate.py                Golden-set evaluation harness
│
├── agents/
│   ├── classifier_agent.py    8-domain legal classifier + documents pre-check
│   ├── rights_agent.py        3-pass retrieval + rights extraction
│   ├── actions_agent.py       Prioritised next-steps extraction
│   ├── forms_agent.py         forms_db.json lookup + LLM fallback
│   ├── documents_agent.py     Keyword/LLM matching over documents_corpus
│   └── synthesis_agent.py     Pure-Python merge into ResponseSchema
│
├── utils/
│   ├── translator.py          Language detection + translate-at-the-edges
│   ├── transcriber.py         Local Whisper voice-to-text
│   └── rights_card.py         A5 PDF rights card generator
│
├── corpus/raw/                 24 source legal documents (JSON) — the ingestion corpus
├── data/
│   ├── documents_corpus/       4 JSON files covering 11 government document types
│   ├── forms_db.json           Static form lookup table
│   └── golden_set.json         30-scenario evaluation set
├── db/                          Persisted ChromaDB vector store (50 chunks)
│
├── frontend/                    React + Vite SPA
└── requirements.txt
```

---

## Setup

**Backend**

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_key_here
```

Get a free key at [console.groq.com](https://console.groq.com).

```bash
python build_db.py              # one-time: build the ChromaDB vector store from corpus/raw/
uvicorn api:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

**Command-line pipeline (no frontend needed)**

```bash
python pipeline.py                  # interactive mode
python pipeline.py --lang hi        # force Hindi output
```

---

*Built by Livana Datta · MIT Bangalore*
