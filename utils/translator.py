"""
utils/translator.py — Phase 3 Multilingual Layer

Translate-at-the-edges architecture:
  - Detect input language
  - Translate non-English input → English before pipeline
  - Translate English response → user's language after pipeline

Currently uses deep-translator (Google Translate).
Designed for drop-in IndicTrans2 swap — just replace the
translate_to_english() and translate_from_english() functions.

Language codes used throughout Adhikar:
  en  — English
  hi  — Hindi
  kn  — Kannada
  ta  — Tamil
  te  — Telugu
"""

from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator


# ── Language config ───────────────────────────────────────────────────────────

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "ta": "Tamil",
    "te": "Telugu",
}

# Map langdetect codes → our codes (they mostly match but just to be safe)
LANGDETECT_MAP = {
    "en": "en",
    "hi": "hi",
    "kn": "kn",
    "ta": "ta",
    "te": "te",
}

# Google Translate language codes
GOOGLE_LANG_MAP = {
    "en": "en",
    "hi": "hi",
    "kn": "kn",
    "ta": "ta",
    "te": "te",
}


# ── Language detection ────────────────────────────────────────────────────────

def detect_language(text: str) -> str:
    """
    Detect the language of the input text.
    Returns a language code: 'en', 'hi', 'kn', 'ta', 'te'.
    Falls back to 'en' if detection fails or language is unsupported.
    """
    if not text or len(text.strip()) < 3:
        return "en"

    try:
        detected = detect(text)
        lang = LANGDETECT_MAP.get(detected, None)
        if lang and lang in SUPPORTED_LANGUAGES:
            return lang
        # If detected but not in our supported list, default to English
        return "en"
    except LangDetectException:
        return "en"


# ── Translation ───────────────────────────────────────────────────────────────

def translate_to_english(text: str, src_lang: str) -> str:
    """
    Translate text from src_lang to English.
    If src_lang is already 'en', returns text unchanged.
    """
    if src_lang == "en" or not text.strip():
        return text

    try:
        google_src = GOOGLE_LANG_MAP.get(src_lang, "auto")
        translator = GoogleTranslator(source=google_src, target="en")
        return translator.translate(text)
    except Exception as e:
        print(f"  [translator] translate_to_english failed ({src_lang}→en): {e}")
        return text  # fallback: return original


def translate_from_english(text: str, tgt_lang: str) -> str:
    """
    Translate text from English to tgt_lang.
    If tgt_lang is 'en', returns text unchanged.
    """
    if tgt_lang == "en" or not text.strip():
        return text

    try:
        google_tgt = GOOGLE_LANG_MAP.get(tgt_lang, "en")
        translator = GoogleTranslator(source="en", target=google_tgt)
        return translator.translate(text)
    except Exception as e:
        print(f"  [translator] translate_from_english failed (en→{tgt_lang}): {e}")
        return text  # fallback: return English


# ── Response translation ──────────────────────────────────────────────────────

def translate_response(response_dict: dict, tgt_lang: str) -> dict:
    """
    Translate only the VALUES of a ResponseSchema dict, not the keys.
    Handles nested lists (rights[], actions[], forms[]).

    If tgt_lang is 'en', returns the dict unchanged.
    """
    if tgt_lang == "en":
        return response_dict

    # Fields to translate at the top level
    TOP_LEVEL_TEXT_FIELDS = {"disclaimer", "domain"}

    # Fields inside list items to translate
    RIGHTS_TEXT_FIELDS = {"right", "plain_language"}
    ACTIONS_TEXT_FIELDS = {"action", "what_to_do"}
    FORMS_TEXT_FIELDS = {"name", "purpose", "where_to_get", "notes"}

    # Don't translate these — they're citations, section numbers, URLs
    SKIP_FIELDS = {"source_act", "source_section", "url", "priority",
                   "requires_lawyer", "sources", "domain"}

    translated = dict(response_dict)  # shallow copy

    # Translate top-level text fields
    for field in TOP_LEVEL_TEXT_FIELDS:
        if field in translated and isinstance(translated[field], str):
            if field != "domain":  # never translate domain label
                translated[field] = translate_from_english(translated[field], tgt_lang)

    # Translate rights[]
    if "rights" in translated:
        new_rights = []
        for right in translated["rights"]:
            new_right = dict(right)
            for field in RIGHTS_TEXT_FIELDS:
                if field in new_right and isinstance(new_right[field], str):
                    new_right[field] = translate_from_english(new_right[field], tgt_lang)
            new_rights.append(new_right)
        translated["rights"] = new_rights

    # Translate actions[]
    if "actions" in translated:
        new_actions = []
        for action in translated["actions"]:
            new_action = dict(action)
            for field in ACTIONS_TEXT_FIELDS:
                if field in new_action and isinstance(new_action[field], str):
                    new_action[field] = translate_from_english(new_action[field], tgt_lang)
            new_actions.append(new_action)
        translated["actions"] = new_actions

    # Translate forms[]
    if "forms" in translated:
        new_forms = []
        for form in translated["forms"]:
            new_form = dict(form)
            for field in FORMS_TEXT_FIELDS:
                if field in new_form and isinstance(new_form[field], str) and new_form[field]:
                    new_form[field] = translate_from_english(new_form[field], tgt_lang)
            new_forms.append(new_form)
        translated["forms"] = new_forms

    return translated


# ── Test ──────────────────────────────────────────────────────────────────────

def test():
    print("\n=== TRANSLATOR TEST ===\n")

    # Test 1: Language detection
    test_texts = [
        ("Police came to my house without a warrant.", "en"),
        ("पुलिस बिना वारंट के मेरे घर आई।", "hi"),
        ("ಪೊಲೀಸರು ವಾರಂಟ್ ಇಲ್ಲದೆ ನನ್ನ ಮನೆಗೆ ಬಂದರು.", "kn"),
        ("போலீஸ் வாரண்ட் இல்லாமல் என் வீட்டிற்கு வந்தார்கள்.", "ta"),
        ("పోలీసులు వారెంట్ లేకుండా నా ఇంటికి వచ్చారు.", "te"),
    ]

    print("--- Language Detection ---")
    passed = 0
    for text, expected in test_texts:
        detected = detect_language(text)
        status = "✓" if detected == expected else "✗"
        print(f"  {status} '{text[:40]}...' → detected: {detected} (expected: {expected})")
        if detected == expected:
            passed += 1
    print(f"  Detection: {passed}/{len(test_texts)} correct\n")

    # Test 2: Translation to English
    print("--- Translation to English ---")
    hindi_query = "पुलिस बिना वारंट के मुझे गिरफ्तार करना चाहती है"
    english = translate_to_english(hindi_query, "hi")
    print(f"  Hindi input:    {hindi_query}")
    print(f"  English output: {english}\n")

    # Test 3: Translation from English
    print("--- Translation from English ---")
    english_right = "Police cannot arrest you without a warrant unless specific conditions are met."
    for lang in ["hi", "kn", "ta", "te"]:
        translated = translate_from_english(english_right, lang)
        print(f"  {SUPPORTED_LANGUAGES[lang]:10} {translated}")

    # Test 4: Full response translation
    print("\n--- Response Translation (Hindi) ---")
    sample_response = {
        "domain": "police_fir",
        "rights": [
            {
                "right": "Right to know grounds of arrest",
                "source_act": "Code of Criminal Procedure, 1973",
                "source_section": "Section 50",
                "plain_language": "Police must tell you why they are arresting you."
            }
        ],
        "actions": [
            {
                "action": "Ask for the warrant",
                "what_to_do": "Calmly ask the officer to show you their arrest warrant.",
                "priority": 1,
                "requires_lawyer": False
            }
        ],
        "forms": [],
        "disclaimer": "This is legal information, not legal advice.",
        "sources": ["CrPC Section 50"]
    }
    translated_response = translate_response(sample_response, "hi")
    import json
    print(json.dumps(translated_response, ensure_ascii=False, indent=2))

    print("\n=== TRANSLATOR TEST COMPLETE ===")


if __name__ == "__main__":
    test()
