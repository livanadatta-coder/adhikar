# Adhikar — Week 1 Starter

**Goal:** By end of Week 2, you can type a query and get back 5 relevant legal chunks. Nothing else.

## Setup (Windows)

### 1. Install Python
Download Python 3.11 from https://python.org — check "Add to PATH" during install.

### 2. Create virtual environment
Open **Command Prompt** (not PowerShell) in this folder:
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

You'll see `(venv)` at the start of your prompt when it's active.

### 3. Add your Gemini API key
Get a free key from https://aistudio.google.com/app/apikey

Create a file called `.env` in this folder:
```
GEMINI_API_KEY=your_key_here
```

### 4. Run the pipeline in order

**Step 1 — Scrape legal documents:**
```
python scraper.py
```
This fetches Police/FIR content from NYAAYA and saves JSON files to `corpus/raw/`.

**Step 2 — Build the vector database:**
```
python build_db.py
```
Chunks the documents and indexes them in ChromaDB. Takes ~1 minute.

**Step 3 — Test retrieval:**
```
python retrieve.py
```
Type any police/FIR query and see the top 5 matching legal chunks.

---

## Project Structure
```
adhikar/
├── scraper.py          # Fetches legal docs from NYAAYA, IndianKanoon
├── build_db.py         # Chunks + indexes docs into ChromaDB
├── retrieve.py         # Interactive retrieval tester
├── corpus/
│   ├── raw/            # Scraped JSON files (one per legal topic)
│   └── processed/      # Cleaned, chunked docs (auto-generated)
├── db/                 # ChromaDB vector store (auto-generated)
├── evaluation/
│   └── golden_set.py   # 10 test scenarios for Police/FIR
└── .env                # Your API keys (never commit this)
```

## Week 1 Milestone Check
Run this to verify everything is working:
```
python retrieve.py --test
```
Expected output: 5 chunks returned for a police detention query, each with source metadata.

## Common Windows Issues
- If `venv\Scripts\activate` fails: run `Set-ExecutionPolicy RemoteSigned` in PowerShell as admin
- If ChromaDB install fails: `pip install chromadb --no-cache-dir`
- If you see encoding errors: the scripts use `utf-8` explicitly — should be fine on Python 3.11
