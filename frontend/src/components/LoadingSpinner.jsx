// src/components/LoadingSpinner.jsx

const LOADING_TEXT = {
  en: "Looking up your rights...",
  hi: "आपके अधिकार खोजे जा रहे हैं...",
  kn: "ನಿಮ್ಮ ಹಕ್ಕುಗಳನ್ನು ಹುಡುಕಲಾಗುತ್ತಿದೆ...",
  ta: "உங்கள் உரிமைகளை தேடுகிறோம்...",
  te: "మీ హక్కులను వెతుకుతున్నాం...",
};

export default function LoadingSpinner({ language = "en" }) {
  return (
    <div className="loading-container">
      <div className="spinner" />
      <p className="loading-text">{LOADING_TEXT[language] || LOADING_TEXT.en}</p>
    </div>
  );
}
