// src/App.jsx
import { useState, useRef } from "react";
import "./App.css";
import LanguageSelector from "./components/LanguageSelector";
import CategoryGrid from "./components/CategoryGrid";
import LoadingSpinner from "./components/LoadingSpinner";
import ResponseCard from "./components/ResponseCard";
import { queryAdhikar, transcribeAudio } from "./api/adhikar";

const PLACEHOLDER = {
  en: 'For example: "Police came to my house and asked for money without showing any papers..."',
  hi: "उदाहरण: पुलिस मेरे घर आई और बिना कागज दिखाए पैसे मांगे...",
  kn: "ಉದಾಹರಣೆ: ಪೊಲೀಸರು ನನ್ನ ಮನೆಗೆ ಬಂದು ಯಾವುದೇ ದಾಖಲೆ ತೋರಿಸದೆ ಹಣ ಕೇಳಿದರು...",
  ta: "எடுத்துக்காட்டு: காவலர்கள் என் வீட்டிற்கு வந்து எந்த ஆவணமும் காட்டாமல் பணம் கேட்டனர்...",
  te: "ఉదాహరణ: పోలీసులు నా ఇంటికి వచ్చి ఎటువంటి పత్రాలు చూపించకుండా డబ్బు అడిగారు...",
};

const SUBMIT_TEXT = {
  en: "Find My Rights →",
  hi: "मेरे अधिकार खोजें →",
  kn: "ನನ್ನ ಹಕ್ಕುಗಳನ್ನು ಹುಡುಕಿ →",
  ta: "என் உரிமைகளை கண்டறி →",
  te: "నా హక్కులు కనుగొనండి →",
};

const MIC_HINT = {
  en: "Tap to speak",
  hi: "बोलने के लिए दबाएं",
  kn: "ಮಾತನಾಡಲು ಒತ್ತಿರಿ",
  ta: "பேச தொடவும்",
  te: "మాట్లాడటానికి నొక్కండి",
};

export default function App() {
  const [language, setLanguage] = useState("en");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const handleSubmit = async (q = query) => {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const result = await queryAdhikar(q, language === "en" ? null : language);
      setResponse(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCategorySelect = (prompt) => {
    setQuery(prompt);
    handleSubmit(prompt);
  };

  const handleBack = () => {
    setResponse(null);
    setError(null);
  };

  const startRecording = async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        await handleTranscribe(audioBlob);
      };

      mediaRecorder.start();
      setRecording(true);
    } catch (e) {
      setError("Microphone access denied. Please allow microphone access and try again.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  const handleTranscribe = async (audioBlob) => {
    setTranscribing(true);
    try {
      const result = await transcribeAudio(audioBlob);
      setQuery(result.text);
      if (result.language && result.language !== "en") {
        setLanguage(result.language);
      }
    } catch (e) {
      setError("Could not transcribe audio. Please type your query instead.");
    } finally {
      setTranscribing(false);
    }
  };

  const handleMicClick = () => {
    if (recording) stopRecording();
    else startRecording();
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">⚖️</span>
            <span className="logo-text">Adhikar</span>
            <span className="logo-tagline">Free Legal Help · India</span>
          </div>
          <LanguageSelector selected={language} onChange={setLanguage} />
        </div>
      </header>

      <main className="main">
        {response && !loading && (
          <ResponseCard response={response} onBack={handleBack} />
        )}

        {loading && <LoadingSpinner language={language} />}

        {!response && !loading && (
          <>
            <div className="hero">
              <h1 className="hero-title">What is happening to you?</h1>
              <p className="hero-subtitle">
                Pick your situation below — we will tell you your rights, in your language, for free.
              </p>
            </div>

            <CategoryGrid onSelect={handleCategorySelect} language={language} />

            <div className="divider">
              <span>or write it yourself</span>
            </div>

            <div className="query-area">
              <div className="input-wrapper">
                <textarea
                  className="query-input"
                  placeholder={
                    transcribing
                      ? "Transcribing your voice..."
                      : (PLACEHOLDER[language] || PLACEHOLDER.en)
                  }
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  rows={4}
                  disabled={transcribing}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit();
                    }
                  }}
                />
                <button
                  className={`mic-btn ${recording ? "mic-recording" : ""} ${transcribing ? "mic-transcribing" : ""}`}
                  onClick={handleMicClick}
                  disabled={transcribing}
                  title={MIC_HINT[language] || MIC_HINT.en}
                  aria-label={recording ? "Stop recording" : "Start voice input"}
                >
                  {transcribing ? "⏳" : recording ? "⏹" : "🎤"}
                </button>
              </div>

              {recording && (
                <div className="recording-indicator">
                  <span className="recording-dot" />
                  Recording... tap the mic again to stop
                </div>
              )}

              <button
                className="submit-btn"
                onClick={() => handleSubmit()}
                disabled={!query.trim() || transcribing}
              >
                {SUBMIT_TEXT[language] || SUBMIT_TEXT.en}
              </button>
            </div>

            {error && <div className="error-box">⚠️ {error}</div>}

            <div className="helpline-bar">
              <span>🆘 Free legal help — call NALSA anytime</span>
              <a href="tel:15100" className="helpline-number">15100</a>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
