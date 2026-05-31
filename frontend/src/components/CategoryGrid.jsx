// src/components/CategoryGrid.jsx

const CATEGORIES = [
  {
    id: "police_fir",
    icon: "🚔",
    label: "Police came to my house",
    labelHi: "पुलिस मेरे घर आई",
    prompt: "Police came to my house and want to arrest me without showing a warrant.",
  },
  {
    id: "eviction_housing",
    icon: "🏠",
    label: "Someone is asking me to leave my home",
    labelHi: "कोई मुझे घर छोड़ने को कह रहा है",
    prompt: "My landlord is asking me to leave without going to court.",
  },
  {
    id: "workplace_salary",
    icon: "💼",
    label: "My employer has not paid my salary",
    labelHi: "मेरे मालिक ने वेतन नहीं दिया",
    prompt: "My employer has not paid my salary for the last 2 months.",
  },
  {
    id: "court_bail",
    icon: "⚖️",
    label: "Someone I know has been arrested",
    labelHi: "मेरे किसी को गिरफ्तार किया गया",
    prompt: "I have been arrested and want to apply for bail.",
  },
];

export default function CategoryGrid({ onSelect, language }) {
  return (
    <div className="category-grid">
      {CATEGORIES.map((cat) => (
        <button
          key={cat.id}
          className="category-tile"
          onClick={() => onSelect(cat.prompt, cat.id)}
        >
          <span className="category-icon">{cat.icon}</span>
          <span className="category-label">
            {language === "hi" ? cat.labelHi : cat.label}
          </span>
        </button>
      ))}
    </div>
  );
}
