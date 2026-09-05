"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated, error, clearError } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // If already authenticated, redirect to home
  React.useEffect(() => {
    if (isAuthenticated) {
      router.push("/");
    }
  }, [isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    clearError();

    if (!email.trim()) {
      setFormError("Email is required.");
      return;
    }
    if (!password) {
      setFormError("Password is required.");
      return;
    }

    setIsSubmitting(true);
    try {
      await login({ email: email.trim(), password });
      router.push("/");
    } catch (err: any) {
      setFormError(err?.message || "Failed to sign in. Please verify your credentials.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeError = formError || error;

  return (
    <div
      style={{
        maxWidth: "440px",
        width: "100%",
        backgroundColor: "var(--card)",
        border: "1px solid var(--border)",
        borderRadius: "12px",
        padding: "2.5rem",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05)",
      }}
    >
      <div style={{ marginBottom: "2rem", textAlign: "center" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          Sign In to DealFlow360
        </h1>
        <p style={{ color: "var(--muted)", fontSize: "0.875rem" }}>
          Enter your organization credentials to access the portal
        </p>
      </div>

      {activeError && (
        <div
          style={{
            backgroundColor: "#fef2f2",
            color: "#991b1b",
            border: "1px solid #fecaca",
            padding: "0.75rem 1rem",
            borderRadius: "6px",
            fontSize: "0.875rem",
            marginBottom: "1.5rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span>{activeError}</span>
          <button
            type="button"
            onClick={() => {
              setFormError(null);
              clearError();
            }}
            style={{
              background: "none",
              border: "none",
              color: "#991b1b",
              fontWeight: "bold",
              cursor: "pointer",
              marginLeft: "0.5rem",
            }}
          >
            &times;
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        <div>
          <label
            htmlFor="email"
            style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.375rem" }}
          >
            Email Address
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@company.com"
            disabled={isSubmitting}
            required
            style={{
              width: "100%",
              padding: "0.625rem 0.875rem",
              borderRadius: "6px",
              border: "1px solid var(--border)",
              fontSize: "0.95rem",
              backgroundColor: isSubmitting ? "#f8fafc" : "#ffffff",
              color: "var(--foreground)",
              outline: "none",
            }}
          />
        </div>

        <div>
          <label
            htmlFor="password"
            style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.375rem" }}
          >
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;"
            disabled={isSubmitting}
            required
            style={{
              width: "100%",
              padding: "0.625rem 0.875rem",
              borderRadius: "6px",
              border: "1px solid var(--border)",
              fontSize: "0.95rem",
              backgroundColor: isSubmitting ? "#f8fafc" : "#ffffff",
              color: "var(--foreground)",
              outline: "none",
            }}
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          style={{
            marginTop: "0.5rem",
            padding: "0.75rem",
            borderRadius: "6px",
            border: "none",
            backgroundColor: isSubmitting ? "#93c5fd" : "var(--primary)",
            color: "var(--primary-foreground)",
            fontWeight: 600,
            fontSize: "0.95rem",
            cursor: isSubmitting ? "not-allowed" : "pointer",
            transition: "background-color 0.15s ease",
          }}
        >
          {isSubmitting ? "Signing in..." : "Sign In"}
        </button>
      </form>

      <div
        style={{
          marginTop: "1.75rem",
          paddingTop: "1.25rem",
          borderTop: "1px solid var(--border)",
          textAlign: "center",
          fontSize: "0.875rem",
          color: "var(--muted)",
        }}
      >
        Don&apos;t have an account?{" "}
        <Link
          href="/register"
          style={{ color: "var(--primary)", fontWeight: 600, textDecoration: "underline" }}
        >
          Register here
        </Link>
      </div>
    </div>
  );
}
