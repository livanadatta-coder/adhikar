"""
utils/transcriber.py — Local Whisper transcription for Adhikar

Uses openai-whisper (local, CPU, no API key needed).
Model: 'small' — best balance of speed and accuracy for Indian-accented speech.

Install:
    pip install openai-whisper
    # also needs ffmpeg:
    # Windows: winget install ffmpeg
    # Mac:     brew install ffmpeg
    # Linux:   sudo apt install ffmpeg
"""

import whisper
import tempfile
import os

# Load once at module level — reused across requests
# 'small' model: ~461MB, good for Indian accents, ~10x realtime on CPU
_model = None

def get_model():
    global _model
    if _model is None:
        print("  [whisper] Loading model (first load ~30s)...")
        _model = whisper.load_model("small")
        print("  [whisper] Model ready")
    return _model


def transcribe_audio(audio_bytes: bytes, file_ext: str = "webm") -> dict:
    """
    Transcribe audio bytes to text using local Whisper.

    Args:
        audio_bytes: Raw audio file bytes (webm/wav/mp3/ogg)
        file_ext:    File extension hint for ffmpeg

    Returns:
        dict with keys:
            text      — transcribed text string
            language  — detected language code (e.g. 'hi', 'en', 'ta')
            confidence — float 0-1 (avg log prob converted)
    """
    model = get_model()

    # Write to temp file — Whisper needs a file path
    with tempfile.NamedTemporaryFile(suffix=f".{file_ext}", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        result = model.transcribe(
            tmp_path,
            task="transcribe",       # transcribe (not translate)
            language=None,           # auto-detect
            fp16=False,              # CPU safe
            verbose=False,
        )

        text = result.get("text", "").strip()
        detected_lang = result.get("language", "en")

        # Map Whisper language codes to Adhikar codes
        WHISPER_LANG_MAP = {
            "english":  "en",
            "hindi":    "hi",
            "kannada":  "kn",
            "tamil":    "ta",
            "telugu":   "te",
            "en": "en", "hi": "hi", "kn": "kn", "ta": "ta", "te": "te",
        }
        adhikar_lang = WHISPER_LANG_MAP.get(detected_lang, "en")

        # Avg log prob → rough confidence (Whisper gives this per segment)
        segments = result.get("segments", [])
        if segments:
            avg_logprob = sum(s.get("avg_logprob", -1) for s in segments) / len(segments)
            # log prob of -0.5 ≈ high confidence, -1.5 ≈ low
            confidence = max(0.0, min(1.0, (avg_logprob + 1.5) / 1.0))
        else:
            confidence = 0.5

        return {
            "text": text,
            "language": adhikar_lang,
            "confidence": round(confidence, 2),
        }

    finally:
        os.unlink(tmp_path)  # clean up temp file
