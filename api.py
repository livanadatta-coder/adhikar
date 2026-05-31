"""
api.py — Adhikar FastAPI backend

Wraps pipeline.py as a REST API for the React frontend.

Endpoints:
  POST /query      — main pipeline endpoint
  POST /transcribe — audio → text via local Whisper
  GET  /health     — health check
  GET  /languages  — supported languages

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
from utils.transcriber import transcribe_audio

app = FastAPI(title="Adhikar API", version="1.0")

# Allow React dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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

class TranscribeResponse(BaseModel):
    text: str
    language: str       # detected language code
    confidence: float   # 0-1


# ── Endpoints ─────────────────────────────────────────────────────────────────

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
    """
    Accepts an audio file (webm/wav/mp3/ogg) and returns transcribed text.
    The frontend records via MediaRecorder API and sends the blob here.
    Whisper auto-detects the language.
    """
    # Validate file type
    allowed = {"audio/webm", "audio/wav", "audio/mpeg", "audio/ogg", "audio/mp4"}
    if file.content_type and file.content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {file.content_type}"
        )

    audio_bytes = await file.read()
    if len(audio_bytes) < 1000:
        raise HTTPException(status_code=400, detail="Audio too short — please speak for at least 2 seconds")

    # Get file extension from content type
    ext_map = {
        "audio/webm": "webm",
        "audio/wav": "wav",
        "audio/mpeg": "mp3",
        "audio/ogg": "ogg",
        "audio/mp4": "mp4",
    }
    ext = ext_map.get(file.content_type or "", "webm")

    try:
        result = transcribe_audio(audio_bytes, file_ext=ext)
        return TranscribeResponse(
            text=result["text"],
            language=result["language"],
            confidence=result["confidence"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
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
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
