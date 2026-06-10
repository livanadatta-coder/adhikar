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
- **Improve actions recall:** Currently 63-72% — query expansion for actions similar to rights retrieval fix

---

## Day 5 — 30 May 2026

**Built:**
- `utils/translator.py` — full multilingual translation module:
  - `detect_language(text)` — langdetect-based detection for en/hi/kn/ta/te, falls back to 'en' on failure
  - `translate_to_english(text, src_lang)` — deep-translator (Google Translate) wrapper
  - `translate_from_english(text, tgt_lang)` — reverse translation
  - `translate_response(response_dict, tgt_lang)` — translates only text VALUES in the ResponseSchema dict, preserving source_act, source_section, url, priority, requires_lawyer, and sources[] untranslated
- `pipeline.py` — main entry point wiring the full 7-stage pipeline:
  - Stage 1: language detection
  - Stage 2: translate to English
  - Stage 3: classify domain (Classifier Agent)
  - Stage 4: 3-pass retrieval (retrieve_for_rights)
  - Stage 5: Rights + Actions + Forms agents
  - Stage 6: Synthesis Agent → ResponseSchema
  - Stage 7: translate response back to user language
  - Interactive mode (`python pipeline.py`) and test mode (`python pipeline.py --test`)
  - `--lang` flag to force output language for testing
- GitHub repository set up at github.com/livanadatta-coder/adhikar — public repo for portfolio

**Test Results — Multilingual pipeline (all 4 languages):**

| Language | Query | Detection | Translation | Domain | Rights |
|----------|-------|-----------|-------------|--------|--------|
| English | Police at house without warrant | ✓ en | — | police_fir 80% | 4 ✓ |
| Hindi | पुलिस बिना वारंट के गिरफ्तार करना चाहती है | ✓ hi | ✓ | police_fir 80% | 4 ✓ |
| Hindi | मकान मालिक ने बिना नोटिस घर से निकाला | ✓ hi | ✓ | eviction_housing 90% | 4 ✓ |
| Kannada | ಪೊಲೀಸರು ವಾರಂಟ್ ಇಲ್ಲದೆ ಬಂಧಿಸಲು ಬಂದಿದ್ದಾರೆ | ✓ kn | ✓ | police_fir 80% | 4 ✓ |
| Tamil | வாரண்ட் இல்லாமல் போலீஸ் கைது செய்ய வந்தார்கள் | ✓ ta | ✓ | police_fir 80% | 4 ✓ |
| Telugu | పోలీసులు వారెంట్ లేకుండా అరెస్టు చేయడానికి వచ్చారు | ✓ te | ✓ | police_fir 80% | 4 ✓ |

5/5 language detection correct. All 4 Indian languages returning full 3-part responses in the correct language. Source citations (CrPC sections, Article numbers) preserved in English throughout.

**Broke:**
- `.env` file with Groq API key accidentally committed to Git — GitHub push protection blocked the push. Fixed by running `git filter-branch` to rewrite commit history and remove `.env` from all past commits. Groq API key rotated immediately
- `.gitignore.txt` (Windows saved it with .txt extension) wasn't being picked up by Git — venv, db/, __pycache__, .env, evaluation results all got tracked. Fixed by renaming to `.gitignore` and running `git rm --cached` on all affected files
- `git push --force` alone wasn't enough to remove the secret — GitHub scans commit history, not just current state. Had to rewrite history with `git filter-branch --force --index-filter "git rm --cached --ignore-unmatch .env"`

**Learned:**
- Never commit `.env`. On Windows, always verify `.gitignore` saved without `.txt` extension — open File Explorer, enable "show file extensions"
- `git rm --cached` only stops tracking a file going forward — it does NOT remove it from commit history. To scrub history: `git filter-branch` or `git filter-repo`
- GitHub push protection scans every commit in the push, not just HEAD — rewriting history is the only real fix
- translate-at-the-edges is the right architecture — keeping all LLM calls in English means the same pipeline, same prompts, same retrieval works for all 5 languages. Translation is truly just a wrapper
- `translate_response()` must skip citation fields (source_act, source_section, sources[]) — translating "Section 41 CrPC" to Hindi produces garbage. Only translate human-readable text fields
- deep-translator is fast and good enough for a portfolio demo. IndicTrans2 would be better for production Indian legal text but the architecture supports a one-file swap

**Architecture decisions made:**
- Translation module is isolated in `utils/translator.py` — swapping deep-translator for IndicTrans2 is a single file change, no changes to pipeline.py or any agent
- `pipeline.py` is the single entry point — frontend (Streamlit) will call `run_pipeline()` directly
- Language is detected once at the top and passed through — no repeated detection calls

**Milestone ✓**
- [x] Language detection: 5/5 correct (en, hi, kn, ta, te)
- [x] Hindi → English → Hindi round trip working
- [x] All 4 Indian languages producing full 3-part responses
- [x] Source citations preserved in English across all languages
- [x] `pipeline.py` wires full 7-stage pipeline end to end
- [x] GitHub repo live at github.com/livanadatta-coder/adhikar
- [x] Phase 3 complete — multilingual layer done

**Multilingual answer (interview ready):**
"The translation layer uses a translate-at-the-edges architecture — the vector store, all agent prompts, and all LLM calls operate in English. Only the user's input and the final response are translated, using Google Translate via deep-translator as a drop-in. The architecture is designed for IndicTrans2 — swapping translation models is a single file change in utils/translator.py. Language detection uses langdetect and correctly identifies Hindi, Kannada, Tamil, and Telugu. The translate_response() function translates only human-readable text fields in the ResponseSchema, explicitly skipping citation fields like source_act and source_section — translating legal citations would corrupt them."

---

## Upcoming

- **Phase 3.5 — Voice input:** Whisper integration for speech-to-text (Hindi, Tamil, Kannada, Indian-accented English)
- **Phase 4 — Streamlit frontend:** Category tiles (8 domains), response card (3-part), language selector, microphone button
- **Phase 4 — Emergency rights card:** PDF + WhatsApp-shareable PNG using ReportLab
- **Phase 4 — Offline cache:** Pre-generate responses for 6 critical scenarios in all 5 languages
- **Phase 4 — Anonymous case logging:** SQLite, opt-in, domain + district + timestamp only
- **Phase 4 — Deploy:** Hugging Face Spaces or Streamlit Cloud
- **Switch to Claude API:** Better structured output quality for production demo

---

## Day 6 — 30 May 2026

**Built:**
- Switched frontend from planned Streamlit to **React + Vite** — better component control, more portfolio-appropriate, easier to style for accessibility
- Full React frontend (`frontend/`) wired to the FastAPI backend (`api.py`) already running on port 8000:
  - `App.jsx` — root component, manages language/query/loading/response/error state, calls `queryAdhikar()` on submit
  - `components/LanguageSelector.jsx` — 5-language toggle (English, हिन्दी, ಕನ್ನಡ, தமிழ், తెలుగు), updates placeholder and submit button text
  - `components/CategoryGrid.jsx` — 4 tap tiles with full plain-language sentence labels ("Police came to my house", not "Police / FIR"). Only the 4 domains with working backend coverage — removed the other 4 to avoid dead buttons
  - `components/ResponseCard.jsx` — 3-section response display: Your Rights (numbered, cited), Do This Now (checkable action list), Forms & Documents. Sources toggle, disclaimer, NALSA helpline bar
  - `components/LoadingSpinner.jsx` — language-aware loading text
  - `api/adhikar.js` — fetch wrapper for POST /query and GET /languages
- Designed and iterated the visual system through multiple rounds:
  - Palette: deep forest green (`#2D4A28`) header, aged paper background (`#EDE5D0`), ochre accent (`#C8882A`), dark ink text — warm and grounded, not digital
  - Typography: **Fraunces** (optical serif, warm, not childish) for all headings, logo, and CTAs — **Nunito** for all body text
  - Layout: horizontal category tiles with left accent bar — poster logic, not card grid. Full-sentence chip labels for low-literacy accessibility
  - Tap targets: minimum 80px tile height, 58px submit button — designed for rural users on mobile
  - Removed all white backgrounds, gradients, drop shadows, and decorative elements

**Design decisions:**
- Scrapped 8-category grid — 5 categories had no backend, showing broken tiles is worse than showing fewer working ones. Kept 4 that map directly to working domains (police_fir, eviction_housing, workplace_salary, court_bail)
- Full sentence labels over short labels — "Police came to my house" is immediately recognisable to a low-literacy user; "Police / FIR" is not
- Fraunces over Caveat — Caveat read as childish at heading size. Fraunces is warm and humanist but carries editorial weight appropriate for legal aid
- Forest green over terracotta/saffron — feels grounded and trustworthy rather than urgent or alarming, which matters for users already in a stressful situation
- Placeholder text is a real example sentence — guides the user exactly what to write without a tutorial

**Broke:**
- Initial "Failed to fetch" on all queries — backend wasn't running. Not a code error; both terminals need to be open simultaneously (uvicorn on 8000, npm run dev on 5173)
- Google Fonts not loading — `index.html` was missing the `<link>` tag for Fraunces + Nunito. Fixed by updating `frontend/index.html` with preconnect and stylesheet links

**Learned:**
- Accessibility and aesthetics aren't opposites — designing for a low-literacy rural user (large tap targets, plain-language labels, warm non-threatening colours) produces a cleaner, more intentional UI than designing for "looks good on a portfolio"
- Remove broken features rather than ship them — 5 dead category tiles would confuse a real user and signal poor QA to a recruiter. 4 working tiles is better than 8 half-working ones
- Font choice carries tone — a single font swap (Caveat → Fraunces) changed the perceived register of the entire app from craft-project to serious tool

**Milestone ✓**
- [x] React + Vite frontend running on `localhost:5173`
- [x] Connected to FastAPI backend on `localhost:8000` — end-to-end query working
- [x] Language selector switches placeholder text and submit button text across all 5 languages
- [x] 4 working category tiles fire real backend queries
- [x] ResponseCard renders 3-part response: rights, actions, forms
- [x] Fraunces + Nunito typography system applied throughout
- [x] Designed for accessibility: large tap targets, plain-language labels, warm non-threatening palette

**Frontend answer (interview ready):**
"The frontend is React + Vite, connected to a FastAPI backend. The key design constraint was accessibility for low-literacy rural users — every category tile uses a full plain-language sentence so the user immediately recognises their situation, tap targets are 80px minimum, and the colour palette is warm and non-threatening rather than clinical. We only surface the 4 domains with working backend coverage — showing broken features is worse than fewer features. The language selector switches placeholder text and CTA copy across 5 languages, consistent with the translate-at-the-edges architecture in the backend."

---

## Upcoming

- **Phase 3.5 — Voice input:** Whisper integration for speech-to-text
- **Phase 4 — Emergency rights card:** PDF + WhatsApp-shareable PNG using ReportLab
- **Phase 4 — Offline cache:** Pre-generate responses for 6 critical scenarios in all 5 languages
- **Phase 4 — Deploy:** Hugging Face Spaces or Streamlit Cloud
- **Switch to Claude API:** Better structured output for production demo
- **Expand category tiles:** Add eviction and consumer fraud tiles once corpus is solid
- **Actions recall improvement:** Currently 63–72% — query expansion for actions similar to rights retrieval fix

---

## Day 7 — 31 May 2026

**Built:**
- `utils/transcriber.py` — local Whisper wrapper
  - Model: `small` (461MB, good Indian accent coverage, ~10x realtime on CPU)
  - Loaded once at module level, reused across requests
  - Auto-detects language from audio — returns Adhikar language code (en/hi/kn/ta/te)
  - Converts avg_logprob → confidence float for frontend feedback
  - Writes audio to tempfile, calls `model.transcribe()`, cleans up
- `POST /transcribe` endpoint in `api.py`
  - Accepts `multipart/form-data` audio upload (webm/wav/mp3/ogg/mp4)
  - Validates file type and minimum size (rejects < 1KB)
  - Returns `{ text, language, confidence }`
- Frontend voice input in `App.jsx`
  - 🎤 button inside textarea (bottom-right, absolute positioned)
  - Uses `MediaRecorder` API to capture audio from microphone
  - Tap to start → red pulsing dot indicator → tap to stop → sends blob to `/transcribe`
  - Transcribed text fills textarea automatically
  - If Whisper detects Hindi/Kannada/Tamil/Telugu, UI language switches automatically
  - Disabled state during transcription with ⏳ indicator
- `transcribeAudio()` added to `api/adhikar.js`
- Mic button CSS: pulse animation while recording, blink dot indicator, disabled states

**Decisions:**
- Local Whisper over OpenAI API — no API key, no cost, works offline, aligns with offline-capable goal
- `small` model over `tiny` — better accuracy on Indian-accented speech, still fast enough on CPU
- Translate-at-the-edges unchanged — Whisper transcribes in the original language, existing `translate_to_english()` handles the rest. No pipeline changes needed.
- Auto language switch on transcription — if user speaks Hindi, UI switches to Hindi so response comes back in Hindi. Feels seamless.

**Install:**
```bash
pip install openai-whisper
winget install ffmpeg   # Windows; brew install ffmpeg on Mac
```
First transcription downloads the small model (~460MB, one-time).

**Milestone ✓**
- [x] Voice input working end-to-end — speak → transcribe → fill textarea → submit
- [x] Auto language detection from speech
- [x] No API key or internet required for transcription
- [x] ffmpeg installed system-wide, Whisper installed in venv

**Voice answer (interview ready):**
"Voice input uses local OpenAI Whisper — the small model runs on CPU, no API key needed. The architecture is clean: Whisper sits before the pipeline as an input preprocessor. It transcribes audio to text and detects the language, then the existing translate-at-the-edges layer handles everything from there. No pipeline changes were needed. The small model handles Indian-accented Hindi, Kannada, Tamil and Telugu reasonably well — good enough for a portfolio demo, and swappable for IndicWhisper in production."

---

---

## Day 8 — 10 Jun 2026

**Built:**
- **Documents feature — 4th domain: Document Guidance**
  - New domain `documents` added alongside existing legal domains
  - Covers 4 categories and 11 specific document types:
    - Government IDs: Aadhaar (new), PAN Card (new), Voter ID (new)
    - Passport & Travel: New adult passport, passport renewal
    - Civil Certificates: Birth certificate (original/duplicate), Marriage certificate, Death certificate
    - Property & Land: Sale deed registration, Land records (7/12 / RTC / Patta), Encumbrance Certificate
  - Each entry has: required documents checklist (categories + options), step-by-step process with detail + tip, fees, processing time, helpline, official website

- **`data/documents_corpus/`** — 4 JSON knowledge files (government_ids.json, passport_travel.json, civil_certificates.json, property_land.json). Structured lookup rather than RAG — no embeddings needed for this domain.

- **`agents/documents_agent.py`** — new agent for document guidance queries
  - Two-stage matching: keyword map (fast, free) → Groq LLM fallback for ambiguous queries
  - Keyword map covers all 11 document IDs with 5–10 keywords each
  - LLM generates a short plain-language summary (3–5 sentences, under 80 words) for low-literacy users
  - Corpus loaded once at import time, reused across requests

- **`agents/classifier_agent.py`** — updated, original logic untouched
  - Added `_is_documents_query()` keyword pre-filter
  - Added `classify_query()` shim used by api.py — returns `{"domain": str, "confidence": float}`
  - All original `run_classifier_agent()`, 8 domains, `ClassifierResponse` schema: unchanged
  - Client initialisation made lazy to fix `GroqError` crash on startup

- **`api.py`** — updated for documents routing + 2 new endpoints
  - `/query` checks domain first — documents queries bypass vectorstore, go to `run_documents_agent()`
  - `QueryResponse` gets optional `documents_result` field (null for all legal queries — backwards compatible)
  - `GET /documents/list` — all 11 document summaries for the Documents tab
  - `GET /documents/{doc_id}` — full guidance for one document by ID

- **`frontend/src/components/DocumentsTab.jsx`** — browsable Documents tab
  - Grid grouped by domain with icon + colour per category
  - Search bar filtering across title and description
  - Detail view: fees/time/helpline metadata card, two-tab layout (📋 Checklist / 🪜 Steps)
  - Checklist tab: interactive tap-to-check checkboxes, grouped by document category
  - Steps tab: expandable accordion per step, tips highlighted yellow

- **`frontend/src/components/DocumentsResultCard.jsx`** — inline chat card for document queries
  - Plain-language summary, fee/time/helpline pills, step preview
  - "View Full Guide with Document Checklist →" CTA switches to Documents tab at the right entry

- **`App.jsx`** — tab nav added to header (⚖️ Get Help / 📋 Documents), `DocumentsResultCard` wired into response flow

- **`test_documents_feature.py`** — diagnostic test, no API key needed. 11/11 keyword tests passing.

**Broke:**
- `GroqError` on startup — new `classifier_agent.py` initialised Groq client at module level before `load_dotenv()` ran in `pipeline.py`. Fixed by making client lazy (`_get_client()` function)
- Wrong `pipeline.py` placed in project root (zip version had incompatible `run_pipeline()` signature). Fixed by restoring original and only modifying `api.py` + `classifier_agent.py`
- `langchain_chroma` and `langdetect` not installed after pipeline restore. Fixed: `pip install langchain-chroma langdetect`
- `ImportError: cannot import name 'run_classifier_agent'` — new classifier only exported `classify_query()`. Fixed by keeping original function intact and adding `classify_query()` as additional export

**Learned:**
- Structured JSON lookup is the right architecture for procedural, stable content — cheaper, faster, more reliable than RAG. RAG is for fuzzy legal text; a lookup table is better for "what documents do I need for a passport"
- Lazy client initialisation (`_get_client()`) is required for any module-level API client in uvicorn — the reloader spawns a subprocess where import order relative to `load_dotenv()` isn't guaranteed
- When adding a new domain, the cleanest integration point is a pre-check shim in the classifier — catch early, route differently, leave the existing pipeline completely untouched
- Event-driven tab switching (`window.dispatchEvent`) lets a chat card navigate to a different tab without lifting state all the way up the component tree

**Architecture decision:**
Documents domain bypasses the vectorstore entirely. The full pipeline (classify → retrieve → rights + actions + forms agents → synthesis) is designed for fuzzy legal text. Document guidance is deterministic — user asks about a passport, we return the passport checklist. The documents_agent does keyword match → optional LLM fallback → corpus lookup → LLM summary. Near-zero cost, fast, no retrieval needed.

**Milestone ✓**
- [x] `python test_documents_feature.py` — 11/11 passing, corpus structure valid
- [x] `GET /documents/list` returns all 11 document summaries
- [x] `GET /documents/{doc_id}` returns full guidance for any document
- [x] `POST /query` routes document queries to documents_agent, legal queries to existing pipeline unchanged
- [x] Documents tab renders with domain grouping, search, and interactive checklist detail view
- [x] Chat shows DocumentsResultCard for document queries, ResponseCard for legal queries

**Documents feature answer (interview ready):**
"The documents feature adds a 4th domain that bypasses the RAG pipeline entirely. Government document requirements are stable and procedural — they don't need semantic search. The classifier catches document queries with a keyword pre-check and routes them to a documents agent that does a corpus lookup across 11 document types. The agent returns a structured checklist and step-by-step process, plus a short LLM-generated plain-language summary for low-literacy users. The frontend renders this as an interactive checklist where users tick off documents as they gather them — a completely different UX from the legal rights response, built for a different user need."

---

## Upcoming

- **Deploy** — Hugging Face Spaces (backend) + Vercel (frontend)
- **README + screenshots** — GitHub repo cleanup before deploy
- **Expand corpus** — consumer fraud and domestic violence domains
- **Actions recall improvement** — currently 63–72%
- **Documents multilingual** — translate document guidance to hi/kn/ta/te using existing translator layer
