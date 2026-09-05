import React from "react";

export default function HomePage() {
  return (
    <div
      style={{
        maxWidth: "600px",
        width: "100%",
        backgroundColor: "var(--card)",
        border: "1px solid var(--border)",
        borderRadius: "12px",
        padding: "2.5rem",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05)",
      }}
    >
      <div style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          DealFlow360
        </h1>
        <p style={{ color: "var(--muted)", fontSize: "0.95rem" }}>
          Foundation Initialized &mdash; Group 01 (Phases 001&ndash;005)
        </p>
      </div>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "1rem",
          padding: "1.25rem",
          backgroundColor: "#f8fafc",
          borderRadius: "8px",
          border: "1px solid #e2e8f0",
          marginBottom: "1.5rem",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>Frontend Service:</span>
          <span
            style={{
              color: "var(--success)",
              backgroundColor: "var(--success-bg)",
              padding: "0.25rem 0.75rem",
              borderRadius: "9999px",
              fontSize: "0.8rem",
              fontWeight: 600,
              border: "1px solid #bbf7d0",
            }}
          >
            Operational
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>Backend Service:</span>
          <span
            style={{
              color: "var(--warning)",
              backgroundColor: "var(--warning-bg)",
              padding: "0.25rem 0.75rem",
              borderRadius: "9999px",
              fontSize: "0.8rem",
              fontWeight: 600,
              border: "1px solid #fef08a",
            }}
          >
            Pending Integration
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>Current Scope:</span>
          <span style={{ fontSize: "0.85rem", color: "var(--muted)", fontFamily: "monospace" }}>
            G01 (Phases 001–005)
          </span>
        </div>
      </div>

      <div style={{ fontSize: "0.875rem", color: "var(--muted)", lineHeight: 1.6 }}>
        <p style={{ marginBottom: "0.5rem" }}>
          <strong>Architecture Guardrails Active:</strong>
        </p>
        <p>
          Continuous discount governance, approval routing, inventory allocation, and billing
          modules are locked for future authorized roadmap phases.
        </p>
      </div>
    </div>
  );
}
