"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function HeaderAuth() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  if (isLoading) {
    return (
      <div style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
        Loading...
      </div>
    );
  }

  if (isAuthenticated && user) {
    const primaryRole = user.roles.length > 0 ? user.roles[0] : "User";
    return (
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--foreground)" }}>
            {user.first_name} {user.last_name}
          </span>
          <span
            style={{
              fontSize: "0.75rem",
              padding: "0.15rem 0.5rem",
              borderRadius: "9999px",
              backgroundColor: "#f1f5f9",
              color: "var(--muted)",
              fontWeight: 600,
              border: "1px solid var(--border)",
            }}
          >
            {primaryRole}
          </span>
        </div>
        <button
          onClick={handleLogout}
          type="button"
          style={{
            fontSize: "0.85rem",
            fontWeight: 600,
            padding: "0.35rem 0.75rem",
            borderRadius: "6px",
            border: "1px solid var(--border)",
            backgroundColor: "#ffffff",
            color: "var(--foreground)",
            cursor: "pointer",
            transition: "all 0.15s ease",
          }}
        >
          Sign Out
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
      <Link
        href="/login"
        style={{
          fontSize: "0.875rem",
          fontWeight: 600,
          padding: "0.35rem 0.75rem",
          borderRadius: "6px",
          color: "var(--foreground)",
        }}
      >
        Sign In
      </Link>
      <Link
        href="/register"
        style={{
          fontSize: "0.875rem",
          fontWeight: 600,
          padding: "0.35rem 0.75rem",
          borderRadius: "6px",
          backgroundColor: "var(--primary)",
          color: "var(--primary-foreground)",
        }}
      >
        Register
      </Link>
    </div>
  );
}
