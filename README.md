# Adhikar — AI-Powered Multilingual Legal First-Responder for India

> *"350 million Indians live below the poverty line with essentially zero access to legal protection — not because the laws don't protect them, but because they don't know their rights."*

Adhikar is a RAG-powered legal information system that takes a user's situation in Hindi, Kannada, Tamil, Telugu, or English and returns structured, cited legal guidance — what their rights are, what to do right now, and what forms they need. It is designed to work offline, in the user's language, and fast enough to use in a police station.

**This is a legal information product, not a legal advice product.** Adhikar tells people what the law says. It does not tell them whether they will win a case.

---

## Demo

```
Query (Hindi): पुलिस बिना वारंट के मुझे गिरफ्तार करना चाहती है

YOUR RIGHTS
1. Right to know grounds of arrest — Section 41 CrPC
   Police cannot arrest you without a warrant unless specific conditions are met.
   They must write down the reason before arresting you.

2. Protection against arbitrary detention — Article 22, Constitution of India
   You have the right to be informed of the grounds of arrest immediately.
   Police cannot hold you for more than 24 hours without a magistrate's order.

3. Custodial rights — D.K. Basu Guidelines (Supreme Court 1997)
   Police must prepare an arrest memo, show ID, and allow you to inform family.

DO THIS NOW
1. Ask the officer to state and write down the reason for arrest
2. Ask to see their warrant or the written grounds under Section 41 CrPC
3. Call a family member and tell them your location — police must allow this
4. Note the officer's name, badge number, and police station

FORMS & DOCUMENTS
No forms required at this stage — focus on the actions above.
```

---

## Architecture

Adhikar is a **multi-agent RAG system** with a translation wrapper and structured output enforcement.

```
User Input (any language)
        ↓
Language Detection (langdetect)
        ↓
Translation to English (deep-translator / IndicTrans2)
        ↓
Classifier Agent → domain label (police_fir / eviction_housing / consumer_fraud / ...)
        ↓
ChromaDB Retrieval → top-5 deduplicated chunks (domain-scoped MMR)
        ↓
┌─────────────────────────────────────────┐
│  Rights Agent   →  rights[]             │
│  Actions Agent  →  actions[]            │  (parallel)
│  Forms Agent    →  forms[]              │
└─────────────────────────────────────────┘
        ↓
Synthesis Agent → ResponseSchema (Pydantic-validated JSON)
        ↓
Translation back to user language
        ↓
Structured 3-part response card
```

### Key architectural decisions

**Translate at the edges** — the vector store, all agent prompts, and all LLM calls operate in English. Only user input (coming in) and the final response (going out) are translated. This keeps the retrieval layer language-agnostic without indexing documents in 5+ languages.

**Three-pass retrieval for rights** — single-pass embedding search fails for constitutional rights because users say "police beat me" but the law says "custodial violence under D.K. Basu guidelines." Three passes: (1) constitutional anchor query, (2) D.K. Basu anchor query, (3) user query with legal terminology expansion. Raised rights recall from 41% to 75%.

**Grounded citations only** — the Rights Agent prompt explicitly forbids citing anything not in the retrieved chunks. The LLM cannot hallucinate section numbers.

**Forms agent is pure DB lookup** — no LLM needed for the 8 core domains. Faster, cheaper, and more reliable than asking an LLM to recall form names.

---

## Evaluation Results

Evaluated on a 30-scenario golden test set across 3 legal domains:

| Domain | Rights Recall | Actions Recall | Forms Recall |
|--------|--------------|----------------|--------------|
| Police / FIR | **75.0%** | 72.5% | 100% |
| Eviction / Housing | **100.0%** | 63.3% | 100% |
| Consumer Fraud | pipeline working* | — | — |

*Consumer fraud evaluation hit Groq's daily token limit (100k TPD) before completing — the 3 scenarios that ran scored 83% avg rights recall.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Groq llama-3.3-70b-versatile (dev) → Claude API (production) |
| RAG framework | LangChain 0.3+ |
| Vector store | ChromaDB (local) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Translation | deep-translator (Google Translate) — designed for IndicTrans2 swap |
| Language detection | langdetect |
| Output validation | Pydantic v2 |
| Frontend | Streamlit (in progress) |
| PDF generation | ReportLab (planned) |

---

## Project Structure

```
adhikar/
├── agents/
│   ├── rights_agent.py        # 3-pass retrieval + rights extraction
│   ├── actions_agent.py       # Immediate actions, ranked by priority
│   ├── forms_agent.py         # DB lookup for legal forms
│   ├── classifier_agent.py    # Zero-shot domain classification
│   ├── synthesis_agent.py     # Merges all agent outputs → ResponseSchema
│   └── mock_*.py              # Mock agents for pipeline testing without API
├── corpus/
│   └── raw/                   # 24 legal documents (JSON) across 3 domains
├── data/
│   ├── forms_db.json          # 8 domains × 3 forms each
│   └── golden_set.json        # 30 evaluation scenarios
├── db/                        # ChromaDB vector store (auto-generated)
├── evaluation/                # Eval results (gitignored)
├── utils/
│   └── translator.py          # Translation layer (in progress)
├── scraper.py                 # Legal document scraper (NYAAYA, IndianKanoon)
├── build_db.py                # Chunks + indexes corpus into ChromaDB
├── retrieve.py                # Interactive retrieval tester
├── evaluate.py                # Evaluation harness (30-scenario golden set)
├── BUILD_LOG.md               # Day-by-day build log (interview talking points)
└── requirements.txt
```

---

## Setup

```bash
# Python 3.11+ required
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

Create a `.env` file:
```
GROQ_API_KEY=your_groq_key_here
```

Get a free Groq key at console.groq.com.

```bash
# Build the vector database
python build_db.py

# Test retrieval
python retrieve.py

# Run evaluation (requires Groq key)
python evaluate.py --domain police_fir
```

---

## Legal Corpus

24 documents across 3 domains, hand-curated from primary sources:

**Police / FIR (14 docs):** CrPC §41, §41A, §50, §50A, §57, §154, §165, §167, §437, Article 21, Article 22, D.K. Basu Guidelines, bail rights

**Eviction / Housing (5 docs):** Transfer of Property Act §105-106, §108, §111, Maharashtra Rent Control Act §15-16, Article 21 (right to shelter)

**Consumer Fraud (5 docs):** Consumer Protection Act 2019 §2, §34-35, §47-58, e-daakhil portal guide, RERA Act 2016

---

## Roadmap

- [x] Phase 1 — Data pipeline + ChromaDB retrieval
- [x] Phase 2 — Multi-agent pipeline + evaluation harness
- [ ] Phase 3 — Multilingual layer (Hindi, Kannada, Tamil, Telugu)
- [ ] Phase 3.5 — Whisper voice input
- [ ] Phase 4 — Streamlit frontend
- [ ] Phase 4 — Emergency rights card (PDF + WhatsApp PNG)
- [ ] Phase 4 — Offline cache for 6 critical scenarios
- [ ] Phase 4 — Deploy to Hugging Face Spaces

---

## Built by

Livana Datta · MIT Bangalore
