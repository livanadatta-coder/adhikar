// src/components/LanguageSelector.jsx

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
  { code: "kn", label: "ಕನ್ನಡ" },
  { code: "ta", label: "தமிழ்" },
  { code: "te", label: "తెలుగు" },
];

export default function LanguageSelector({ selected, onChange }) {
  return (
    <div className="language-selector">
      {LANGUAGES.map((lang) => (
        <button
          key={lang.code}
          className={`lang-btn ${selected === lang.code ? "active" : ""}`}
          onClick={() => onChange(lang.code)}
        >
          {lang.label}
        </button>
      ))}
    </div>
  );
}
