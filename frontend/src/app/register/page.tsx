"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

export default function RegisterPage() {
  const router = useRouter();
  const { register, isAuthenticated, error, clearError } = useAuth();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
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

    if (!firstName.trim() || !lastName.trim()) {
      setFormError("First and last names are required.");
      return;
    }
    if (!email.trim()) {
      setFormError("Email is required.");
      return;
    }
    if (password.length < 8) {
      setFormError("Password must be at least 8 characters long.");
      return;
    }
    if (password !== confirmPassword) {
      setFormError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
        password,
      });
      router.push("/");
    } catch (err: any) {
      setFormError(err?.message || "Registration failed. Please check your details.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeError = formError || error;

  return (
    <div
      style={{
        maxWidth: "480px",
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
          Create an Account
        </h1>
        <p style={{ color: "var(--muted)", fontSize: "0.875rem" }}>
          Register to join the DealFlow360 Deal &amp; Discount Governance platform
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

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.1rem" }}>
        <div style={{ display: "flex", gap: "0.75rem" }}>
          <div style={{ flex: 1 }}>
            <label
              htmlFor="firstName"
              style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.375rem" }}
            >
              First Name
            </label>
            <input
              id="firstName"
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder="Jane"
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

          <div style={{ flex: 1 }}>
            <label
              htmlFor="lastName"
              style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.375rem" }}
            >
              Last Name
            </label>
            <input
              id="lastName"
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              placeholder="Doe"
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
        </div>

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
            placeholder="jane.doe@company.com"
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
            Password (min. 8 characters)
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

        <div>
          <label
            htmlFor="confirmPassword"
            style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: "0.375rem" }}
          >
            Confirm Password
          </label>
          <input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
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
          {isSubmitting ? "Creating account..." : "Create Account"}
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
        Already have an account?{" "}
        <Link
          href="/login"
          style={{ color: "var(--primary)", fontWeight: 600, textDecoration: "underline" }}
        >
          Sign in here
        </Link>
      </div>
    </div>
  );
}
