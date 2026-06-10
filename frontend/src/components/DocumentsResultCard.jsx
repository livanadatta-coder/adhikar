/**
 * DocumentsResultCard.jsx
 *
 * Shown inside the chat interface when the pipeline classifies a query
 * as "documents" domain. Displays:
 *   - Plain language summary (from LLM)
 *   - Quick metadata (fees, time, helpline)
 *   - First 2 process steps as a preview
 *   - "View Full Guide" button that opens DocumentsTab at the right document
 *
 * Usage in your chat message renderer:
 *   import DocumentsResultCard from './DocumentsResultCard';
 *   {message.documents_result && <DocumentsResultCard result={message.documents_result} />}
 */

import { useState } from "react";

const DOMAIN_META = {
  government_ids:     { icon: "🪪", color: "#C17535" },
  passport_travel:    { icon: "📘", color: "#2E6B5E" },
  civil_certificates: { icon: "📜", color: "#5C4A2A" },
  property_land:      { icon: "🏠", color: "#3B5E3A" },
};

export default function DocumentsResultCard({ result }) {
  const [expanded, setExpanded] = useState(false);

  if (!result?.success) {
    return (
      <div
        style={{
          padding: "16px",
          background: "#FDF6EC",
          border: "1.5px solid #E8D9C0",
          borderRadius: "12px",
          fontSize: "14px",
          color: "#7A6A55",
          fontFamily: "'DM Sans', sans-serif",
        }}
      >
        {result?.not_found_message || "No document guidance found for your query."}
      </div>
    );
  }

  const meta = DOMAIN_META[result.domain] || { icon: "📄", color: "#C17535" };
  const previewSteps = result.process_steps.slice(0, expanded ? result.process_steps.length : 2);

  const openInDocumentsTab = () => {
    // Emit event — DocumentsTab listens for this to navigate directly
    window.dispatchEvent(
      new CustomEvent("adhikar:open_document", { detail: { doc_id: result.matched_document } })
    );
    // If you have a tab-switching mechanism, trigger it here too:
    window.dispatchEvent(new CustomEvent("adhikar:switch_tab", { detail: { tab: "documents" } }));
  };

  return (
    <div
      style={{
        background: "#FFFDF9",
        border: "1.5px solid #E8D9C0",
        borderRadius: "14px",
        overflow: "hidden",
        fontFamily: "'DM Sans', sans-serif",
        marginTop: "8px",
      }}
    >
      {/* Top accent bar */}
      <div style={{ height: "4px", background: meta.color }} />

      <div style={{ padding: "18px 20px" }}>
        {/* Title row */}
        <div style={{ display: "flex", alignItems: "flex-start", gap: "10px", marginBottom: "10px" }}>
          <span style={{ fontSize: "24px", lineHeight: 1 }}>{meta.icon}</span>
          <div>
            <div style={{ fontSize: "16px", fontWeight: 700, color: "#3A2E1E", fontFamily: "'DM Serif Display', serif" }}>
              {result.title}
            </div>
          </div>
        </div>

        {/* Plain summary */}
        {result.plain_summary && (
          <p style={{ fontSize: "14px", color: "#5A4A35", lineHeight: 1.65, margin: "0 0 14px 0" }}>
            {result.plain_summary}
          </p>
        )}

        {/* Quick metadata pills */}
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "16px" }}>
          {result.fees && (
            <span style={{ fontSize: "12px", background: "#F5F0E8", color: "#5A4A35", padding: "4px 10px", borderRadius: "20px", border: "1px solid #E8D9C0" }}>
              💰 {result.fees.split("|")[0].trim()}
            </span>
          )}
          {result.processing_time && (
            <span style={{ fontSize: "12px", background: "#F5F0E8", color: "#5A4A35", padding: "4px 10px", borderRadius: "20px", border: "1px solid #E8D9C0" }}>
              ⏱ {result.processing_time.split("|")[0].trim()}
            </span>
          )}
          {result.helpline && (
            <span style={{ fontSize: "12px", background: "#EBF4F1", color: "#2E6B5E", padding: "4px 10px", borderRadius: "20px", border: "1px solid #C5E0D8" }}>
              📞 {result.helpline}
            </span>
          )}
        </div>

        {/* Step preview */}
        <div style={{ marginBottom: "14px" }}>
          <div style={{ fontSize: "12px", fontWeight: 700, color: "#9A8A75", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: "8px" }}>
            How to apply
          </div>
          {previewSteps.map((step) => (
            <div
              key={step.step}
              style={{
                display: "flex",
                gap: "10px",
                padding: "6px 0",
                borderBottom: "1px solid #F0EAE0",
              }}
            >
              <div
                style={{
                  width: "22px",
                  height: "22px",
                  minWidth: "22px",
                  borderRadius: "50%",
                  background: meta.color,
                  color: "white",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "11px",
                  fontWeight: 700,
                }}
              >
                {step.step}
              </div>
              <div style={{ fontSize: "13px", color: "#3A2E1E", lineHeight: 1.4, paddingTop: "2px" }}>
                {step.title}
              </div>
            </div>
          ))}

          {result.process_steps.length > 2 && (
            <button
              onClick={() => setExpanded(!expanded)}
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                color: meta.color,
                fontSize: "13px",
                fontWeight: 600,
                padding: "8px 0 0 0",
                fontFamily: "'DM Sans', sans-serif",
              }}
            >
              {expanded
                ? "▲ Show less"
                : `▼ Show all ${result.process_steps.length} steps`}
            </button>
          )}
        </div>

        {/* CTA button */}
        <button
          onClick={openInDocumentsTab}
          style={{
            width: "100%",
            padding: "11px",
            background: meta.color,
            color: "white",
            border: "none",
            borderRadius: "10px",
            fontSize: "14px",
            fontWeight: 600,
            cursor: "pointer",
            fontFamily: "'DM Sans', sans-serif",
            transition: "opacity 0.15s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.88")}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
        >
          📋 View Full Guide with Document Checklist →
        </button>
      </div>
    </div>
  );
}
