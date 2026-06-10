// src/components/ResponseCard.jsx
import { useState } from "react";

const BASE_URL = "http://127.0.0.1:8000";

function RightsSection({ rights }) {
  return (
    <div className="response-section rights-section">
      <div className="section-header">
        <span className="section-icon">📋</span>
        <h2 className="section-title">Your Rights</h2>
      </div>
      <div className="section-content">
        {rights.map((right, i) => (
          <div key={i} className="right-item">
            <div className="right-number">{i + 1}</div>
            <div className="right-body">
              <p className="right-title">{right.right}</p>
              <p className="right-plain">{right.plain_language}</p>
              <span className="right-citation">
                {right.source_act} · {right.source_section}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ActionsSection({ actions }) {
  const [done, setDone] = useState({});
  const toggle = (i) => setDone((d) => ({ ...d, [i]: !d[i] }));

  return (
    <div className="response-section actions-section">
      <div className="section-header">
        <span className="section-icon">⚡</span>
        <h2 className="section-title">Do This Now</h2>
      </div>
      <div className="section-content">
        {actions.map((action, i) => (
          <div
            key={i}
            className={`action-item ${done[i] ? "action-done" : ""}`}
            onClick={() => toggle(i)}
          >
            <div className="action-check">{done[i] ? "✅" : "⬜"}</div>
            <div className="action-body">
              <p className="action-title">{action.action}</p>
              <p className="action-detail">{action.what_to_do}</p>
              {action.requires_lawyer && (
                <span className="lawyer-badge">Lawyer recommended</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FormsSection({ forms }) {
  if (!forms || forms.length === 0) return null;
  return (
    <div className="response-section forms-section">
      <div className="section-header">
        <span className="section-icon">📄</span>
        <h2 className="section-title">Forms & Documents</h2>
      </div>
      <div className="section-content">
        {forms.map((form, i) => (
          <div key={i} className="form-item">
            <p className="form-name">{form.name}</p>
            <p className="form-purpose">{form.purpose}</p>
            <p className="form-where">📍 {form.where_to_get}</p>
            {form.url && (
              <a href={form.url} target="_blank" rel="noreferrer" className="form-link">
                Open official link →
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ResponseCard({ response, onBack }) {
  const [showSources, setShowSources] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const handleDownloadCard = async () => {
    setDownloading(true);
    try {
      const res = await fetch(`${BASE_URL}/rights-card`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: response.rights[0]?.right || "legal rights",
          language: response.detected_lang || "en",
        }),
      });
      if (!res.ok) throw new Error("PDF generation failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "adhikar-rights-card.pdf";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert("Could not generate PDF. Please try again.");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="response-card">
      <div className="response-header">
        <button className="back-btn" onClick={onBack}>← Back</button>
        <span className="domain-badge">{response.domain.replace(/_/g, " ")}</span>
        <span className="lang-badge">{response.response_lang}</span>
      </div>

      <RightsSection rights={response.rights} />
      <ActionsSection actions={response.actions} />
      <FormsSection forms={response.forms} />

      <div className="disclaimer">{response.disclaimer}</div>

      <div className="sources-toggle">
        <button
          className="sources-btn"
          onClick={() => setShowSources((s) => !s)}
        >
          {showSources ? "Hide sources ▲" : "View sources ▼"}
        </button>
        {showSources && (
          <div className="sources-list">
            {response.sources.map((s, i) => (
              <span key={i} className="source-tag">{s}</span>
            ))}
          </div>
        )}
      </div>

      <button
        className="download-card-btn"
        onClick={handleDownloadCard}
        disabled={downloading}
      >
        {downloading ? "Generating PDF..." : "⬇ Download Rights Card (PDF)"}
      </button>

      <div className="helpline-bar">
        <span>🆘 NALSA Free Legal Aid</span>
        <a href="tel:15100" className="helpline-number">15100</a>
      </div>
    </div>
  );
}
