/**
 * DocumentsTab.jsx
 *
 * Documents guidance tab for Adhikar frontend.
 * Displays all available documents in a browsable grid,
 * and a detail view with required documents checklist + step-by-step process.
 *
 * Usage in App.jsx:
 *   import DocumentsTab from './components/DocumentsTab';
 *   // Add to tab list: { id: 'documents', label: 'Documents' }
 *   // Render: <DocumentsTab apiBase={API_BASE_URL} />
 *
 * Expects backend running at apiBase with:
 *   GET /documents/list
 *   GET /documents/{doc_id}
 */

import { useState, useEffect } from "react";

// ── Domain metadata ──────────────────────────────────────────────────────────
const DOMAIN_META = {
  government_ids: {
    label: "Government IDs",
    icon: "🪪",
    color: "#C17535",       // terracotta
    bg: "#FDF6EC",
  },
  passport_travel: {
    label: "Passport & Travel",
    icon: "📘",
    color: "#2E6B5E",       // deep teal
    bg: "#EBF4F1",
  },
  civil_certificates: {
    label: "Birth, Marriage & Death",
    icon: "📜",
    color: "#5C4A2A",       // deep brown
    bg: "#FAF5EE",
  },
  property_land: {
    label: "Property & Land",
    icon: "🏠",
    color: "#3B5E3A",       // forest
    bg: "#EEF4EE",
  },
};

// ── Helpers ───────────────────────────────────────────────────────────────────
const groupByDomain = (docs) => {
  const groups = {};
  docs.forEach((doc) => {
    if (!groups[doc.domain]) groups[doc.domain] = [];
    groups[doc.domain].push(doc);
  });
  return groups;
};

// ── Sub-components ────────────────────────────────────────────────────────────

function DomainBadge({ domain }) {
  const meta = DOMAIN_META[domain] || { label: domain, icon: "📄", color: "#888", bg: "#f5f5f5" };
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        padding: "3px 10px",
        borderRadius: "99px",
        fontSize: "12px",
        fontWeight: 600,
        color: meta.color,
        background: meta.bg,
        border: `1px solid ${meta.color}30`,
        fontFamily: "'DM Sans', sans-serif",
      }}
    >
      {meta.icon} {meta.label}
    </span>
  );
}

function DocCard({ doc, onClick }) {
  const meta = DOMAIN_META[doc.domain] || { color: "#888", bg: "#f5f5f5", icon: "📄" };
  return (
    <button
      onClick={() => onClick(doc.id)}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        padding: "18px 20px",
        background: "#FFFDF9",
        border: `1.5px solid #E8E0D4`,
        borderRadius: "14px",
        cursor: "pointer",
        textAlign: "left",
        transition: "box-shadow 0.15s, transform 0.15s, border-color 0.15s",
        fontFamily: "'DM Sans', sans-serif",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = `0 4px 16px ${meta.color}22`;
        e.currentTarget.style.borderColor = meta.color;
        e.currentTarget.style.transform = "translateY(-2px)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = "none";
        e.currentTarget.style.borderColor = "#E8E0D4";
        e.currentTarget.style.transform = "translateY(0)";
      }}
    >
      <div style={{ fontSize: "28px" }}>{meta.icon}</div>
      <div>
        <div style={{ fontSize: "15px", fontWeight: 600, color: "#3A2E1E", marginBottom: "4px" }}>
          {doc.title}
        </div>
        <div style={{ fontSize: "13px", color: "#7A6A55", lineHeight: 1.4 }}>
          {doc.description.length > 80 ? doc.description.slice(0, 80) + "…" : doc.description}
        </div>
      </div>
      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "4px" }}>
        {doc.fees && (
          <span style={{ fontSize: "12px", color: "#7A6A55", background: "#F5F0E8", padding: "2px 8px", borderRadius: "6px" }}>
            💰 {doc.fees.length > 30 ? doc.fees.slice(0, 30) + "…" : doc.fees}
          </span>
        )}
        {doc.processing_time && (
          <span style={{ fontSize: "12px", color: "#7A6A55", background: "#F5F0E8", padding: "2px 8px", borderRadius: "6px" }}>
            ⏱ {doc.processing_time.length > 25 ? doc.processing_time.slice(0, 25) + "…" : doc.processing_time}
          </span>
        )}
      </div>
    </button>
  );
}

function CheckboxItem({ text }) {
  const [checked, setChecked] = useState(false);
  return (
    <div
      onClick={() => setChecked(!checked)}
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: "10px",
        padding: "8px 0",
        cursor: "pointer",
        borderBottom: "1px solid #F0EAE0",
      }}
    >
      <div
        style={{
          width: "18px",
          height: "18px",
          minWidth: "18px",
          borderRadius: "4px",
          border: checked ? "none" : "2px solid #C17535",
          background: checked ? "#C17535" : "white",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginTop: "1px",
          transition: "background 0.15s",
        }}
      >
        {checked && <span style={{ color: "white", fontSize: "11px", fontWeight: 700 }}>✓</span>}
      </div>
      <span
        style={{
          fontSize: "14px",
          color: checked ? "#A09080" : "#3A2E1E",
          textDecoration: checked ? "line-through" : "none",
          lineHeight: 1.5,
          transition: "color 0.15s",
          fontFamily: "'DM Sans', sans-serif",
        }}
      >
        {text}
      </span>
    </div>
  );
}

function ProcessStepCard({ step }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      style={{
        border: "1.5px solid #E8E0D4",
        borderRadius: "10px",
        overflow: "hidden",
        marginBottom: "8px",
        background: "#FFFDF9",
      }}
    >
      <button
        onClick={() => setOpen(!open)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          width: "100%",
          padding: "14px 16px",
          background: "transparent",
          border: "none",
          cursor: "pointer",
          textAlign: "left",
          fontFamily: "'DM Sans', sans-serif",
        }}
      >
        <div
          style={{
            width: "28px",
            height: "28px",
            minWidth: "28px",
            borderRadius: "50%",
            background: "#C17535",
            color: "white",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "13px",
            fontWeight: 700,
          }}
        >
          {step.step}
        </div>
        <div style={{ flex: 1, fontSize: "14px", fontWeight: 600, color: "#3A2E1E" }}>
          {step.title}
        </div>
        <div style={{ fontSize: "16px", color: "#C17535", transform: open ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}>
          ▾
        </div>
      </button>
      {open && (
        <div style={{ padding: "0 16px 14px 56px", fontFamily: "'DM Sans', sans-serif" }}>
          <p style={{ fontSize: "13px", color: "#5A4A35", lineHeight: 1.65, margin: "0 0 8px 0" }}>
            {step.detail}
          </p>
          {step.tip && (
            <div
              style={{
                background: "#FEF9EC",
                border: "1px solid #F5D78E",
                borderRadius: "6px",
                padding: "8px 12px",
                fontSize: "12px",
                color: "#8A6A1A",
                display: "flex",
                gap: "6px",
              }}
            >
              <span>💡</span>
              <span>{step.tip}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main Detail View ──────────────────────────────────────────────────────────

function DocDetail({ docId, apiBase, onBack }) {
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("checklist"); // "checklist" | "steps"

  useEffect(() => {
    setLoading(true);
    fetch(`${apiBase}/documents/${docId}`)
      .then((r) => r.json())
      .then((data) => { setDoc(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [docId, apiBase]);

  if (loading) {
    return (
      <div style={{ padding: "40px", textAlign: "center", color: "#7A6A55", fontFamily: "'DM Sans', sans-serif" }}>
        Loading…
      </div>
    );
  }

  if (!doc || !doc.success) {
    return (
      <div style={{ padding: "40px", textAlign: "center", color: "#C17535", fontFamily: "'DM Sans', sans-serif" }}>
        Could not load document. <button onClick={onBack} style={{ color: "#C17535", background: "none", border: "none", cursor: "pointer", textDecoration: "underline" }}>Go back</button>
      </div>
    );
  }

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif", maxWidth: "700px", margin: "0 auto" }}>
      {/* Back button */}
      <button
        onClick={onBack}
        style={{
          background: "none",
          border: "none",
          cursor: "pointer",
          color: "#C17535",
          fontSize: "14px",
          fontWeight: 600,
          padding: "0 0 16px 0",
          display: "flex",
          alignItems: "center",
          gap: "4px",
          fontFamily: "'DM Sans', sans-serif",
        }}
      >
        ← All Documents
      </button>

      {/* Header */}
      <div
        style={{
          background: "linear-gradient(135deg, #FDF6EC 0%, #F5EFE3 100%)",
          border: "1.5px solid #E8D9C0",
          borderRadius: "16px",
          padding: "24px",
          marginBottom: "20px",
        }}
      >
        <DomainBadge domain={doc.domain} />
        <h2 style={{ fontSize: "22px", fontWeight: 700, color: "#3A2E1E", margin: "12px 0 6px 0", fontFamily: "'DM Serif Display', serif" }}>
          {doc.title}
        </h2>
        <p style={{ fontSize: "14px", color: "#5A4A35", lineHeight: 1.5, margin: "0 0 16px 0" }}>
          {doc.description}
        </p>

        {/* Metadata row */}
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          {doc.fees && (
            <div style={{ background: "white", border: "1px solid #E8D9C0", borderRadius: "8px", padding: "8px 14px" }}>
              <div style={{ fontSize: "11px", color: "#9A8A75", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px" }}>Fees</div>
              <div style={{ fontSize: "13px", color: "#3A2E1E", fontWeight: 600, marginTop: "2px" }}>{doc.fees}</div>
            </div>
          )}
          {doc.processing_time && (
            <div style={{ background: "white", border: "1px solid #E8D9C0", borderRadius: "8px", padding: "8px 14px" }}>
              <div style={{ fontSize: "11px", color: "#9A8A75", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px" }}>Time</div>
              <div style={{ fontSize: "13px", color: "#3A2E1E", fontWeight: 600, marginTop: "2px" }}>{doc.processing_time}</div>
            </div>
          )}
          {doc.helpline && (
            <div style={{ background: "white", border: "1px solid #E8D9C0", borderRadius: "8px", padding: "8px 14px" }}>
              <div style={{ fontSize: "11px", color: "#9A8A75", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px" }}>Helpline</div>
              <div style={{ fontSize: "13px", color: "#C17535", fontWeight: 600, marginTop: "2px" }}>{doc.helpline}</div>
            </div>
          )}
        </div>

        {doc.website && (
          <div style={{ marginTop: "12px", fontSize: "13px", color: "#7A6A55" }}>
            🌐 <span style={{ color: "#2E6B5E" }}>{doc.website}</span>
          </div>
        )}
      </div>

      {/* Tab toggle */}
      <div
        style={{
          display: "flex",
          gap: "0",
          background: "#F5F0E8",
          borderRadius: "10px",
          padding: "4px",
          marginBottom: "20px",
        }}
      >
        {[
          { id: "checklist", label: `📋 Documents Needed (${doc.required_documents.length} categories)` },
          { id: "steps", label: `🪜 Steps (${doc.process_steps.length})` },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              flex: 1,
              padding: "9px 16px",
              borderRadius: "8px",
              border: "none",
              cursor: "pointer",
              fontSize: "13px",
              fontWeight: 600,
              fontFamily: "'DM Sans', sans-serif",
              background: activeTab === tab.id ? "white" : "transparent",
              color: activeTab === tab.id ? "#C17535" : "#7A6A55",
              boxShadow: activeTab === tab.id ? "0 1px 4px rgba(0,0,0,0.08)" : "none",
              transition: "all 0.15s",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Checklist tab */}
      {activeTab === "checklist" && (
        <div>
          <p style={{ fontSize: "13px", color: "#7A6A55", marginBottom: "16px" }}>
            Tap each item to check it off as you gather your documents.
          </p>
          {doc.required_documents.map((cat, i) => (
            <div key={i} style={{ marginBottom: "20px" }}>
              <div
                style={{
                  fontSize: "12px",
                  fontWeight: 700,
                  color: "#C17535",
                  textTransform: "uppercase",
                  letterSpacing: "0.6px",
                  marginBottom: "6px",
                }}
              >
                {cat.category}
              </div>
              {cat.options.map((opt, j) => (
                <CheckboxItem key={j} text={opt} />
              ))}
            </div>
          ))}
        </div>
      )}

      {/* Steps tab */}
      {activeTab === "steps" && (
        <div>
          <p style={{ fontSize: "13px", color: "#7A6A55", marginBottom: "16px" }}>
            Tap each step to expand the full details. Tips are highlighted in yellow.
          </p>
          {doc.process_steps.map((step, i) => (
            <ProcessStepCard key={i} step={step} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main DocumentsTab ─────────────────────────────────────────────────────────

export default function DocumentsTab({ apiBase = "http://localhost:8000" }) {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetch(`${apiBase}/documents/list`)
      .then((r) => r.json())
      .then((data) => { setDocs(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [apiBase]);

  // Handle query-driven navigation (called from chat when domain=documents)
  useEffect(() => {
    const handler = (e) => {
      if (e.detail?.doc_id) setSelectedId(e.detail.doc_id);
    };
    window.addEventListener("adhikar:open_document", handler);
    return () => window.removeEventListener("adhikar:open_document", handler);
  }, []);

  if (selectedId) {
    return (
      <div style={{ padding: "20px" }}>
        <DocDetail docId={selectedId} apiBase={apiBase} onBack={() => setSelectedId(null)} />
      </div>
    );
  }

  const filteredDocs = docs.filter((d) =>
    search.trim() === "" ||
    d.title.toLowerCase().includes(search.toLowerCase()) ||
    d.description.toLowerCase().includes(search.toLowerCase())
  );

  const grouped = groupByDomain(filteredDocs);

  return (
    <div style={{ padding: "20px", fontFamily: "'DM Sans', sans-serif", maxWidth: "900px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: "20px" }}>
        <h2 style={{ fontSize: "22px", fontWeight: 700, color: "#3A2E1E", margin: "0 0 6px 0", fontFamily: "'DM Serif Display', serif" }}>
          Document Guide
        </h2>
        <p style={{ fontSize: "14px", color: "#7A6A55", margin: 0 }}>
          Step-by-step guidance for getting government IDs, certificates, passports, and property documents.
        </p>
      </div>

      {/* Search */}
      <div style={{ position: "relative", marginBottom: "24px" }}>
        <span style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)", fontSize: "16px" }}>🔍</span>
        <input
          type="text"
          placeholder="Search documents…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            width: "100%",
            padding: "10px 12px 10px 38px",
            border: "1.5px solid #E8D9C0",
            borderRadius: "10px",
            fontSize: "14px",
            fontFamily: "'DM Sans', sans-serif",
            color: "#3A2E1E",
            background: "#FFFDF9",
            outline: "none",
            boxSizing: "border-box",
          }}
        />
      </div>

      {loading && (
        <div style={{ textAlign: "center", color: "#7A6A55", padding: "40px" }}>Loading documents…</div>
      )}

      {!loading && filteredDocs.length === 0 && (
        <div style={{ textAlign: "center", color: "#7A6A55", padding: "40px" }}>
          No documents found for "{search}".
        </div>
      )}

      {/* Domain groups */}
      {Object.entries(grouped).map(([domain, domainDocs]) => {
        const meta = DOMAIN_META[domain] || { label: domain, icon: "📄" };
        return (
          <div key={domain} style={{ marginBottom: "32px" }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                marginBottom: "14px",
              }}
            >
              <span style={{ fontSize: "20px" }}>{meta.icon}</span>
              <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#3A2E1E", margin: 0 }}>
                {meta.label}
              </h3>
              <div style={{ height: "1px", flex: 1, background: "#E8D9C0" }} />
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
                gap: "12px",
              }}
            >
              {domainDocs.map((doc) => (
                <DocCard key={doc.id} doc={doc} onClick={setSelectedId} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
