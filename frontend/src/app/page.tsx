"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

export default function HomePage() {
  const { user, isAuthenticated, isLoading, logout } = useAuth();

  return (
    <div
      style={{
        maxWidth: "680px",
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
          Continuous Deal &amp; Discount Governance &mdash; Group 08 (Phases 001&ndash;040)
        </p>
      </div>

      {/* User Session Banner */}
      {isLoading ? (
        <div
          style={{
            padding: "1rem",
            backgroundColor: "#f8fafc",
            borderRadius: "8px",
            border: "1px solid #e2e8f0",
            marginBottom: "1.5rem",
            fontSize: "0.9rem",
            color: "var(--muted)",
          }}
        >
          Checking authentication session...
        </div>
      ) : isAuthenticated && user ? (
        <div
          style={{
            padding: "1.25rem",
            backgroundColor: "#f0fdf4",
            borderRadius: "8px",
            border: "1px solid #bbf7d0",
            marginBottom: "1.5rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: "1.1rem", color: "#166534" }}>
                Welcome back, {user.first_name} {user.last_name}!
              </div>
              <div style={{ fontSize: "0.85rem", color: "#15803d" }}>{user.email}</div>
            </div>
            <button
              onClick={() => logout()}
              type="button"
              style={{
                fontSize: "0.8rem",
                fontWeight: 600,
                padding: "0.25rem 0.6rem",
                borderRadius: "6px",
                border: "1px solid #86efac",
                backgroundColor: "#ffffff",
                color: "#166534",
                cursor: "pointer",
              }}
            >
              Sign Out
            </button>
          </div>

          <div style={{ fontSize: "0.85rem", color: "#166534", marginTop: "0.5rem" }}>
            <strong>Assigned Roles:</strong>{" "}
            {user.roles.length > 0 ? (
              <span style={{ display: "inline-flex", gap: "0.4rem", marginLeft: "0.3rem" }}>
                {user.roles.map((r) => (
                  <span
                    key={r}
                    style={{
                      padding: "0.15rem 0.5rem",
                      borderRadius: "9999px",
                      backgroundColor: "#dcfce7",
                      border: "1px solid #86efac",
                      fontSize: "0.75rem",
                      fontWeight: 600,
                    }}
                  >
                    {r}
                  </span>
                ))}
              </span>
            ) : (
              <span style={{ fontStyle: "italic" }}>No roles assigned</span>
            )}
          </div>
        </div>
      ) : (
        <div
          style={{
            padding: "1.25rem",
            backgroundColor: "#eff6ff",
            borderRadius: "8px",
            border: "1px solid #bfdbfe",
            marginBottom: "1.5rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ fontWeight: 600, color: "#1e40af", fontSize: "0.95rem" }}>
              Ready for Authentication
            </div>
            <div style={{ fontSize: "0.85rem", color: "#3b82f6" }}>
              Sign in or register to test the authenticated session lifecycle.
            </div>
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <Link
              href="/login"
              style={{
                fontSize: "0.85rem",
                fontWeight: 600,
                padding: "0.4rem 0.85rem",
                borderRadius: "6px",
                backgroundColor: "var(--primary)",
                color: "#ffffff",
              }}
            >
              Sign In
            </Link>
            <Link
              href="/register"
              style={{
                fontSize: "0.85rem",
                fontWeight: 600,
                padding: "0.4rem 0.85rem",
                borderRadius: "6px",
                backgroundColor: "#ffffff",
                color: "var(--primary)",
                border: "1px solid #bfdbfe",
              }}
            >
              Register
            </Link>
          </div>
        </div>
      )}

      {/* System Status Architecture Grid */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "0.75rem",
          padding: "1.25rem",
          backgroundColor: "#f8fafc",
          borderRadius: "8px",
          border: "1px solid #e2e8f0",
          marginBottom: "1.5rem",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>Authentication UI (Phase 040):</span>
          <span
            style={{
              color: "var(--success)",
              backgroundColor: "var(--success-bg)",
              padding: "0.2rem 0.6rem",
              borderRadius: "9999px",
              fontSize: "0.75rem",
              fontWeight: 600,
              border: "1px solid #bbf7d0",
            }}
          >
            Operational
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>Permission Middleware (Phase 039):</span>
          <span
            style={{
              color: "var(--success)",
              backgroundColor: "var(--success-bg)",
              padding: "0.2rem 0.6rem",
              borderRadius: "9999px",
              fontSize: "0.75rem",
              fontWeight: 600,
              border: "1px solid #bbf7d0",
            }}
          >
            Active
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>Object-Level Auth (Phase 038):</span>
          <span
            style={{
              color: "var(--success)",
              backgroundColor: "var(--success-bg)",
              padding: "0.2rem 0.6rem",
              borderRadius: "9999px",
              fontSize: "0.75rem",
              fontWeight: 600,
              border: "1px solid #bbf7d0",
            }}
          >
            Active
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>Roles &amp; RBAC (Phases 032–037):</span>
          <span
            style={{
              color: "var(--success)",
              backgroundColor: "var(--success-bg)",
              padding: "0.2rem 0.6rem",
              borderRadius: "9999px",
              fontSize: "0.75rem",
              fontWeight: 600,
              border: "1px solid #bbf7d0",
            }}
          >
            6 Canonical Roles Active
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>Current Master Scope:</span>
          <span style={{ fontSize: "0.85rem", color: "var(--muted)", fontFamily: "monospace" }}>
            G08 (Phases 001–040)
          </span>
        </div>
      </div>

      <div style={{ fontSize: "0.875rem", color: "var(--muted)", lineHeight: 1.6 }}>
        <p style={{ marginBottom: "0.5rem" }}>
          <strong>Architecture Guardrails Active:</strong>
        </p>
        <p>
          Continuous discount governance, approval routing, inventory allocation, and billing
          modules remain locked for future authorized roadmap phases (Phase 041+).
        </p>
      </div>
    </div>
  );
}
