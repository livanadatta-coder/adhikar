"""
api.py — Adhikar FastAPI backend

Wraps pipeline.py as a REST API for the React frontend.

Endpoints:
  POST /query      — main pipeline endpoint
  POST /transcribe — audio → text via local Whisper
  GET  /health     — health check
  GET  /languages  — supported languages

  GET  /documents/list       — list all document guidance entries   [NEW]
  GET  /documents/{doc_id}   — get full guidance for one document   [NEW]

Run:
  uvicorn api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pipeline import run_pipeline, load_vectorstore
from utils.translator import SUPPORTED_LANGUAGES
from agents.documents_agent import run_documents_agent, _ALL_DOCUMENTS   # NEW

try:
    from utils.transcriber import transcribe_audio
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

app = FastAPI(title="Adhikar API", version="1.1")

# Allow React dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load vectorstore once at startup
print("Loading vector store...")
vectorstore = load_vectorstore()
print("✓ Vector store ready")


# ── Request / Response schemas ────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    language: Optional[str] = None  # force language override (en/hi/kn/ta/te)

class QueryResponse(BaseModel):
    domain: str
    rights: list
    actions: list
    forms: list
    disclaimer: str
    sources: list
    detected_lang: str
    response_lang: str
    clarification_needed: bool = False
    clarification_question: Optional[str] = None
    documents_result: Optional[dict] = None   # NEW — populated when domain=documents

class TranscribeResponse(BaseModel):
    text: str
    language: str
    confidence: float

# NEW — documents schemas
class DocumentSummary(BaseModel):
    id: str
    title: str
    description: str
    domain: str
    fees: Optional[str]
    processing_time: Optional[str]

class DocumentDetail(BaseModel):
    success: bool
    matched_document: Optional[str]
    domain: Optional[str]
    title: Optional[str]
    description: Optional[str]
    plain_summary: str
    required_documents: list
    process_steps: list
    fees: Optional[str]
    processing_time: Optional[str]
    helpline: Optional[str]
    website: Optional[str]
    not_found_message: Optional[str]


# ── Existing endpoints (unchanged) ────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "message": "Adhikar API is running"}


@app.get("/languages")
def languages():
    return {
        "supported": [
            {"code": code, "name": name, "native": native}
            for code, name, native in [
                ("en", "English", "English"),
                ("hi", "Hindi", "हिन्दी"),
                ("kn", "Kannada", "ಕನ್ನಡ"),
                ("ta", "Tamil", "தமிழ்"),
                ("te", "Telugu", "తెలుగు"),
            ]
        ]
    }


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(file: UploadFile = File(...)):
    if not WHISPER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Voice input is not available in the deployed version. Please type your query."
        )

    allowed = {"audio/webm", "audio/wav", "audio/mpeg", "audio/ogg", "audio/mp4"}
    if file.content_type and file.content_type not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported audio format: {file.content_type}")

    audio_bytes = await file.read()
    if len(audio_bytes) < 1000:
        raise HTTPException(status_code=400, detail="Audio too short — please speak for at least 2 seconds")

    ext_map = {
        "audio/webm": "webm", "audio/wav": "wav",
        "audio/mpeg": "mp3", "audio/ogg": "ogg", "audio/mp4": "mp4",
    }
    ext = ext_map.get(file.content_type or "", "webm")

    try:
        result = transcribe_audio(audio_bytes, file_ext=ext)
        return TranscribeResponse(text=result["text"], language=result["language"], confidence=result["confidence"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        # ── Check if this is a documents query first ──────────────────────────
        # Import classifier to check domain without running full pipeline
        from agents.classifier_agent import classify_query
        classification = classify_query(request.query)

        if classification["domain"] == "documents":
            doc_result = run_documents_agent(request.query)
            # Return a QueryResponse with documents_result populated
            # and empty legal fields so frontend doesn't break
            return QueryResponse(
                domain="documents",
                rights=[],
                actions=[],
                forms=[],
                disclaimer="",
                sources=[],
                detected_lang=request.language or "en",
                response_lang="English",
                documents_result=doc_result,
            )

        # ── Existing legal pipeline for all other domains ─────────────────────
        result = run_pipeline(
            query=request.query,
            vectorstore=vectorstore,
            forced_lang=request.language,
        )
        return QueryResponse(
            domain=result.get("domain", ""),
            rights=result.get("rights", []),
            actions=result.get("actions", []),
            forms=result.get("forms", []),
            disclaimer=result.get("disclaimer", ""),
            sources=result.get("sources", []),
            detected_lang=result.get("detected_lang", "en"),
            response_lang=result.get("response_lang", "English"),
            clarification_needed=result.get("clarification_needed", False),
            clarification_question=result.get("clarification_question"),
            documents_result=None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── New documents endpoints ───────────────────────────────────────────────────

@app.get("/documents/list", response_model=list[DocumentSummary])
def list_documents():
    """Returns all available document guidance entries for the Documents tab."""
    return [
        DocumentSummary(
            id=doc["id"],
            title=doc["title"],
            description=doc.get("description", ""),
            domain=doc.get("_domain", ""),
            fees=doc.get("fees"),
            processing_time=doc.get("processing_time"),
        )
        for doc in _ALL_DOCUMENTS
    ]


@app.get("/documents/{doc_id}", response_model=DocumentDetail)
def get_document(doc_id: str):
    """Returns full guidance for a specific document by ID."""
    doc = next((d for d in _ALL_DOCUMENTS if d["id"] == doc_id), None)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{doc_id}' not found. Call /documents/list for valid IDs."
        )
    return DocumentDetail(
        success=True,
        matched_document=doc["id"],
        domain=doc.get("_domain"),
        title=doc["title"],
        description=doc.get("description", ""),
        plain_summary="",
        required_documents=doc.get("required_documents", []),
        process_steps=doc.get("process_steps", []),
        fees=doc.get("fees"),
        processing_time=doc.get("processing_time"),
        helpline=doc.get("helpline"),
        website=doc.get("website"),
        not_found_message=None,
    )
