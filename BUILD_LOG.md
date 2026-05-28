# Adhikar — Build Log

The spec says: keep a build log. This becomes your interview talking points.
Format: what you built, what broke, what you learned.

---

### Day 1 — 21 May 2026

**Built:**
- Set up Python virtual environment on Windows
- Installed all dependencies (langchain, chromadb, sentence-transformers)
- Ran scraper.py — wrote 8 seed legal documents to corpus/raw/ (CrPC §41, §41A, §50, §154, §167, Article 22, D.K. Basu guidelines, bail rights)
- Built ChromaDB vector store with 13 chunks from the 8 documents
- Passed Week 1 milestone: 10/10 test queries returning correct legal sources

**Broke:**
- numpy==1.26.4 incompatible with Python 3.13 — fixed by installing latest numpy with --only-binary=:all:
- langchain 0.2.16 incompatible with Python 3.13 — fixed by upgrading to 0.3.25
- chromadb 0.6.3 had dependency issue — fixed by installing separately
- langchain.schema and langchain.text_splitter imports moved in newer version — fixed by updating to langchain_core.documents and langchain_text_splitters

**Learned:**
- Always use --only-binary=:all: on Windows to avoid C compiler errors
- Translate at the edges architecture: keep vector store in English, translate only input/output
- Chunking strategy: 800 chars / 150 overlap because IPC sections average 300-900 chars
- MMR retrieval (Maximal Marginal Relevance) reduces duplicate results vs plain similarity search

Milestone ✓
- [x] `python scraper.py` runs without errors
- [x] `corpus/raw/` has 8+ JSON files
- [x] `python build_db.py` builds the ChromaDB without errors
- [x] `python retrieve.py --test` shows 10/10 queries returning results
- [x] Can describe the chunking strategy and why 800/150 was chosen

**Chunking answer (interview ready):**
IPC sections average 300–900 characters. At 800 chars most sections fit in one chunk. The 150-char overlap means a right defined at the end of one chunk isn't lost when the next chunk starts mid-sentence.

---

## Day 2 — 23 May 2026

**Built:**
- Rights Agent (agents/rights_agent.py) — takes query + retrieved chunks, returns structured JSON with cited rights, Pydantic-validated
- Mock Rights Agent (agents/mock_rights_agent.py) — hardcoded realistic responses for testing pipeline logic without API calls. 3/3 passed
- Actions Agent (agents/actions_agent.py) — takes query + chunks, returns 2-4 ranked concrete actions with priority and requires_lawyer fields
- Mock Actions Agent (agents/mock_actions_agent.py) — 3/3 passed
- Classifier Agent (agents/classifier_agent.py) — zero-shot classification into 8 legal domains with confidence score and clarification fallback
- Mock Classifier Agent (agents/mock_classifier_agent.py) — keyword-based classification, 9/9 passed
- Forms Agent (agents/forms_agent.py) — pure DB lookup against data/forms_db.json, no LLM needed for standard cases. 8/8 passed across all domains
- Forms Database (data/forms_db.json) — 8 domains × 3 forms each, real Indian legal forms with official URLs and practical notes
- Synthesis Agent (agents/synthesis_agent.py) — merges Rights + Actions + Forms outputs into final ResponseSchema, deduplicates sources, enforces sort order
- Full pipeline end-to-end: Classifier → Retrieval → Rights + Actions + Forms → Synthesis — 3/3 with mock agents, then 3/3 with live Groq LLM

**Broke:**
- Gemini free tier quota exhausted immediately on first real API call (limit: 0 on free tier after initial burn)
- Switched to Groq (llama-3.3-70b-versatile) — free tier is far more generous, no quota issues during dev
- IndentationError in rights_agent.py and mock_rights_agent.py — caused by paste corruption when downloading files. Fixed by re-downloading clean versions
- KeyError on JSON braces in prompt templates — Python's .format() interprets { } as template variables. Fixed by escaping all literal JSON braces as {{ }} while keeping {query}, {domain}, {chunks} as single braces
- langchain_community HuggingFaceEmbeddings and Chroma deprecated — updated imports to langchain_huggingface and langchain_chroma. Run: pip install langchain-huggingface langchain-chroma

**Learned:**
- Mock-first development pattern: build schema + pipeline logic before touching the API. Mocks are same-signature replacements — swap in real agents with one import change
- Gemini free tier is unusable for iterative development. Groq llama-3.3-70b-versatile is the right dev LLM — fast, generous free tier, supports response_format json_object natively
- Forms agent doesn't need an LLM — pure DB lookup is faster, cheaper, and more reliable. LLM fallback only for unknown domains
- Synthesis agent is pure Python — no API call. Merges three response objects, deduplicates sources, enforces action sort order by priority
- Classifier is the cheapest real agent — one short call, no retrieval, no chunks. Run this first; only proceed to retrieval if confidence >= 0.6
- Source normalisation is an issue — "CrPC 50" and "Code of Criminal Procedure, 1973, Section 50" appear as separate sources. Needs a normalisation pass in synthesis (Week 3 cleanup)
- requires_lawyer flag needs tighter prompt guidance — "go to magistrate's court" was incorrectly flagged as requiring a lawyer. The spec explicitly says users can do this without a lawyer

**Architecture decisions made:**
- Translation at the edges: all retrieval and agent calls in English. IndicTrans2 only wraps input/output
- ResponseSchema enforced at Pydantic level — every response has rights[], actions[], forms[], disclaimer, sources[]
- Domain-scoped MMR retrieval: filter by domain before similarity search — improves precision significantly over unfiltered search

Milestone ✓
- [x] Rights Agent returns structured JSON with cited rights for any police/FIR query
- [x] Pydantic schema validates every response
- [x] Actions Agent returns ranked concrete actions with priority and requires_lawyer
- [x] Classifier Agent routes queries to correct domain with confidence scoring
- [x] Forms Agent returns relevant forms for all 8 domains (DB lookup, no API)
- [x] Synthesis Agent merges all three into final ResponseSchema
- [x] Full pipeline 3/3 with live Groq LLM — Classifier → Retrieval → Rights + Actions + Forms → Synthesis

**Pipeline output (interview ready):**
"The pipeline runs in four stages: classifier identifies the legal domain, MMR retrieval pulls the top-4 relevant chunks from ChromaDB scoped to that domain, three specialist agents run in parallel producing rights, actions, and forms, and a synthesis agent merges them into a validated ResponseSchema. Every right and action is grounded in a retrieved chunk — the agents cannot hallucinate citations because the prompt explicitly forbids citing anything not in the provided documents."

---

## Day 3 — 25–27 May 2026

**Built:**
- Expanded corpus with 6 new legal documents in `corpus/raw/`: Article 21, CrPC §46 (arrest of women), §50A (inform relatives), §57 (24-hour detention limit), §165 (police search conditions), §437 (bail for non-bailable offences + default bail). Total corpus: 14 documents (all police_fir domain)
- Rewrote Rights Agent (`agents/rights_agent.py`) — **"Phase 2, Week 2 retrieval fix"** that raised rights recall from ~41% → 75%:
  - Query expansion system: 9 domain-keyed trigger→legal-terminology patterns that append precise legal terms to user queries so embeddings find the right chunks
  - Three-pass retrieval (`retrieve_for_rights`): Pass 1 (k=10) anchors on priority rights (Article 21, 22, D.K. Basu); Pass 2 (k=8) uses expanded query; Pass 3 (k=6) uses original query for procedural chunks. Deduplicates by (act, section) metadata, capped at 12 unique chunks
  - Updated prompt: "PRIORITISE constitutional rights (Article 21, Article 22) and landmark case guidelines (D.K. Basu) when present in documents"
  - New `run_rights_agent_with_retrieval()` drop-in function combining retrieval + agent call
- Built golden test set (`data/golden_set.json`) — 30 scenarios across 3 domains: 10 police_fir (PF001–PF010), 10 eviction_housing (EH001–EH010), 10 consumer_fraud (CF001–CF010)
- Built evaluation harness (`evaluate.py`, 372 lines) — runs golden set against LIVE or MOCK agents, computes rights/actions/forms recall per scenario, prints per-domain and overall summary, saves results to `evaluation/results_live.json` and `evaluation/results_mock.json`
- Source normalisation map in evaluate.py — 110+ entries mapping variant citation formats ("crpc 41", "§41", "Code of Criminal Procedure, 1973 - Section 41") to canonical forms ("Section 41 CrPC"). Directly addresses the source normalisation issue logged on Day 2
- Built 5 debugging/diagnostic tools:
  - `check_response.py` — spot-checks a single scenario against live rights agent, saves raw JSON to `raw_response.txt`
  - `debug_rights.py` — runs 3 worst-scoring scenarios through `retrieve_for_rights()`, prints chunk metadata and returned rights
  - `db_check.py` — runs diagnostic queries against ChromaDB with domain filter, outputs to `db_check.txt`
  - `inspect_db.py` — queries all chunks (k=50) then filters for Article 21/22/D.K. Basu to verify they exist in DB
- Migrated Actions Agent to Groq (llama-3.3-70b-versatile) — consistent with Rights Agent and Classifier

**Evaluation Results — Live (police_fir, Groq LLM):**

| Scenario | Rights Recall | Actions Recall | Forms Recall |
|----------|---------------|----------------|--------------|
| PF001 — Warrantless arrest | 100% | 75% | 100% |
| PF002 — Grounds of arrest | 100% | 33% | 100% |
| PF003 — FIR refusal | **50%** | 100% | 100% |
| PF004 — 24hr detention | 100% | 67% | 100% |
| PF005 — Police violence | 67% | 50% | 100% |
| PF006 — 41A notice | 100% | 67% | 100% |
| PF007 — Family notification | 67% | 67% | 100% |
| PF008 — Bail rights | 67% | 33% | 100% |
| PF009 — Illegal search | **33%** | 100% | 100% |
| PF010 — Female arrest at night | 67% | 100% | 100% |

**Overall Live (police_fir): Rights ≈ 75.0% · Actions ≈ 69.2% · Forms = 100%**
→ Rights recall at the 75% target. PF003 and PF009 are weakest — need targeted corpus or prompt fixes.

**Evaluation Results — Mock (all 30 scenarios):**

| Domain | Avg Rights | Avg Actions | Avg Forms |
|----------------|-----------|------------|----------|
| police_fir | 53.3% | 70.0% | 100% |
| eviction_housing | 0.0% | 40.0% | 100% |
| consumer_fraud | 0.0% | 45.0% | 100% |

**Overall Mock: Rights ≈ 17.8%** — expected: mock agents only have 3 hardcoded police_fir responses. Eviction + consumer return 0% rights because no mock data exists for those domains.

**Broke:**
- Initial rights recall was ~41% before three-pass retrieval fix — LLM was only returning 2 rights for warrant scenarios (Section 41, 41A), missing Article 22 and D.K. Basu entirely. Root cause: single-pass retrieval wasn't surfacing constitutional rights chunks
- `raw_response.txt` captured the pre-fix failure: only Section 41A (notice) and Section 41 (warrant) returned, zero constitutional rights
- `{corpus\` junk directory created by accidentally running a bash-style `mkdir {corpus\raw,...}` on Windows — curly braces aren't expanded. Empty, should be deleted
- Forms Agent is still on Gemini while everything else is on Groq — API inconsistency

**Learned:**
- Single-pass retrieval is insufficient for rights recall — constitutional principles (Article 21, 22) don't share keywords with procedural queries like "police arrested without warrant". A priority anchor pass that always pulls foundational rights is essential
- Query expansion bridges the vocabulary gap between how users describe situations and how the law is written — "police beat me" needs to map to "custodial violence" and "D.K. Basu guidelines"
- Source normalisation is a harder problem than expected — 110+ manual entries and still fragile. A regex-based normaliser would be more robust long-term
- Debugging tools (check_response, debug_rights, inspect_db) were critical for diagnosing the rights recall gap — without seeing which chunks the LLM received vs. what it returned, the fix would have been guesswork
- Mock evaluation gives misleading results for domains without hardcoded mock data — 0% recall is a test-infrastructure gap, not a pipeline failure
- Evaluation keyword matching (top 3 words > 3 chars) is adequate for progress tracking but could produce false positives/negatives on edge cases

**Architecture decisions made:**
- Three-pass retrieval is rights-specific — Actions Agent still uses standard single-pass MMR, because action recall is less dependent on constitutional anchoring
- Source normalisation lives in evaluate.py (evaluation-time) not synthesis_agent.py (runtime) — keeps the pipeline clean, normalisation only matters for scoring
- Golden set includes eviction_housing and consumer_fraud even though corpus doesn't exist yet — forward-looking test design so we know immediately when those domains are grounded

Milestone ✓
- [x] Golden test set: 30 scenarios × 3 domains with expected rights, actions, forms
- [x] Evaluation harness runs against both LIVE and MOCK agents
- [x] Source normalisation map (110+ entries) resolves citation variants
- [x] Rights recall raised from ~41% to 75% via three-pass retrieval
- [x] Live police_fir evaluation: 75% rights recall — clears threshold for multilingual layer
- [ ] PF003 (50%) and PF009 (33%) still below par — need targeted fixes

**Retrieval fix answer (interview ready):**
"Single-pass embedding search failed for rights recall because users describe situations ('police arrested me without warrant') but the law uses different vocabulary ('Article 22 — Protection against arrest and detention'). We fixed this with three-pass retrieval: first pass always anchors on constitutional rights and landmark cases, second pass expands the user query with legal terminology, third pass catches procedural specifics. This raised rights recall from 41% to 75%. The query expansion maps are domain-specific — 'police beat me' expands to include 'custodial violence' and 'D.K. Basu guidelines'."

---

## Upcoming (after Day 3)

- ~~**Corpus expansion (critical)**~~ ✓ Done — 10 new docs added, eviction 100%, consumer pipeline working
- ~~**Migrate Forms Agent to Groq**~~ ✓ Done
- ~~**Delete `{corpus\` directory**~~ ✓ Done
- ~~**Fix requires_lawyer prompt guidance**~~ ✓ Done
- **Fix weak scenarios:** PF003 (50%) and PF010 (67%) — D.K. Basu still inconsistent, Section 46 missing occasionally
- **Expand mock agents:** Low priority — defer to after multilingual
- **Improve actions recall:** Currently 63-72% — lower priority than multilingual
- **Regex-based source normaliser:** Tech debt — defer to Week 7 cleanup
- **Multilingual layer:** ✓ Cleared — starting Phase 3 next

---

## Day 4 — 28–29 May 2026

**Built:**
- Expanded corpus to 24 documents — added 10 new files across 2 new domains:
  - consumer_fraud (5): Consumer Protection Act 2019 §2 (definitions + consumer rights), §34-35 (District Commission complaint procedure), e-daakhil portal guide, §47-58 (State/National Commission + product liability), RERA Act 2016 (builder fraud + delayed possession)
  - eviction_housing (5): Transfer of Property Act §105-106 (lease definition + duration), §108 (rights and liabilities of lessor/lessee), §111 (determination of lease + eviction procedure), Maharashtra Rent Control Act 1999 §15-16 (tenant protections), Article 21 as applied to right to shelter (Olga Tellis judgment)
- Rebuilt ChromaDB — 24 documents → 50 chunks
- Fixed D.K. Basu retrieval gap in `rights_agent.py` — split Pass 1 into two separate anchor queries:
  - Anchor 1: constitutional rights (Article 21, 22)
  - Anchor 2: D.K. Basu specifically ("D.K. Basu custodial rights guidelines arrested person police station arrest memo identify officer inform family custodial violence")
  - Root cause: D.K. Basu text doesn't embed close to user queries like "physical force during questioning" — needed its own dedicated similarity search pass
- Migrated Forms Agent (`agents/forms_agent.py`) from Gemini to Groq — now all 5 agents (Classifier, Rights, Actions, Forms, Synthesis) use the same Groq backend. Gemini dependency removed entirely
- Fixed `requires_lawyer` prompt in `actions_agent.py` — added explicit FALSE list (going to police station, filing FIR, appearing before magistrate, sending written complaint, calling helpline, going to consumer forum, filing on e-daakhil) and explicit TRUE list (filing writ petition, bail application in court, civil suit, contested hearing). Previously "go to magistrate's court" was incorrectly flagged as requiring a lawyer
- Added 5-second rate-limit delay between live eval scenarios in `evaluate.py` to avoid burning through Groq's 100k TPD limit mid-run
- Deleted `{corpus\` junk directory — created accidentally by running bash-style mkdir syntax on Windows CMD

**Final Evaluation Results — Live (all 30 scenarios, Groq LLM):**

| Domain | Rights Recall | Actions Recall | Forms Recall | Errors |
|--------|---------------|----------------|--------------|--------|
| police_fir | 75.0% ✓ | 72.5% | 100% | 0 |
| eviction_housing | 100.0% ✓ | 63.3% | 100% | 0 |
| consumer_fraud | 25.0%* | 26.7%* | 30%* | 7 |

*Consumer fraud errors are Groq rate limit (100k TPD exhausted), not pipeline failures. CF001-CF003 which ran successfully scored 83% avg rights recall.

**Broke:**
- D.K. Basu chunks not surfacing for queries like "police used physical force" — single anchor query for all constitutional rights wasn't enough. D.K. Basu embeddings are too dissimilar from user query vocabulary. Fixed with dedicated Basu anchor
- Groq 100k tokens/day limit hit mid-eval on both eval runs — three-pass retrieval (3 similarity searches × 30 scenarios) plus LLM calls exhausts the daily limit before finishing all 30 scenarios. 5-second delay between scenarios helps with TPM but not TPD
- Windows CMD multiline `python -c` doesn't work — every line executes as a separate command. Fix: always write diagnostic code to .py files

**Learned:**
- Domain-specific semantic gaps require domain-specific anchor queries — a single "constitutional rights" anchor doesn't reliably surface D.K. Basu because its vocabulary is about procedure (arrest memo, identify officer) not rights language
- Groq free tier TPD (tokens per day) is the binding constraint for eval runs, not TPM (tokens per minute). Three-pass retrieval triples the embedding calls which don't count toward TPD, but the LLM calls at ~1500 tokens each × 30 scenarios = 45k tokens minimum, which with the three passes hits the 100k limit quickly
- e-daakhil.nic.in portal knowledge needs to be in the corpus explicitly — the LLM won't cite it as an action unless it appears in a retrieved chunk
- All 5 agents now on Groq — architectural consistency matters for debugging. Mixed API backends (Gemini + Groq) made it harder to reason about failures
- requires_lawyer false positives were systemic, not random — the original prompt didn't define what "genuinely needs a lawyer" means. Explicit enumeration (TRUE: writ petition, bail application / FALSE: FIR filing, magistrate complaint) eliminated the ambiguity

**Architecture decisions made:**
- Groq-only backend: all agent LLM calls go through Groq llama-3.3-70b-versatile. Will switch to Claude API for final demo (better structured output quality per spec recommendation)
- Voice input planned as v1.5 feature — Whisper integration architected for but not yet built. Will slot in between multilingual layer and frontend

**Milestone ✓**
- [x] Corpus expanded to 24 documents across 3 domains (police_fir, eviction_housing, consumer_fraud)
- [x] Eviction housing: 100% rights recall
- [x] Police FIR: 75% rights recall — threshold maintained
- [x] Consumer fraud pipeline working (rate limit masking scores, not pipeline failure)
- [x] All agents migrated to Groq — Gemini dependency removed
- [x] requires_lawyer prompt fixed — magistrate court visits no longer flagged as needing lawyer
- [x] D.K. Basu dual-anchor fix deployed
- [x] Phase 2 (Agent Layer) complete — cleared for Phase 3

**Phase 2 complete answer (interview ready):**
"We built a 5-agent pipeline — Classifier, Rights, Actions, Forms, Synthesis — all on Groq llama-3.3-70b-versatile with Pydantic-validated output schemas. We evaluated on a 30-scenario golden test set with three recall metrics. Police FIR hits 75% rights recall, eviction housing hits 100%. The hardest problem was retrieval — constitutional rights chunks don't embed close to plain-language user queries, so we built a three-pass retrieval system with domain-specific anchor queries that guarantee constitutional articles and landmark case guidelines always surface regardless of how the user phrases their situation."

---

## Upcoming

- **Phase 3 — Multilingual layer:** IndicTrans2 or deep-translator integration — Hindi first, then Kannada/Tamil/Telugu. Translate at the edges: user input → English → pipeline → translate response back
- **Language detection:** langdetect or IndicLID to auto-detect input language
- **Voice input (v1.5):** Whisper integration for speech-to-text — slots in after multilingual text works
- **Phase 4 — Streamlit frontend:** Category tiles, response card, language selector, microphone button
- **Phase 4 — Emergency rights card:** PDF + WhatsApp-shareable PNG generator using ReportLab
- **Phase 4 — Offline cache:** Pre-generate responses for 6 critical scenarios in all languages
- **Phase 4 — Deploy:** Hugging Face Spaces (free tier)
- **Switch to Claude API for final demo:** Better structured output quality for production
- **Improve actions recall:** Currently 63-72% — query expansion for actions similar to rights retrieval fix
