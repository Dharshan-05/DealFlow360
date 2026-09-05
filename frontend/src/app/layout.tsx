import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DealFlow360 — Continuous Deal & Discount Governance",
  description: "Enterprise deal lifecycle and discount governance platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <header
          style={{
            borderBottom: "1px solid var(--border)",
            backgroundColor: "#ffffff",
            padding: "1rem 2rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <div
              style={{
                width: "28px",
                height: "28px",
                borderRadius: "6px",
                backgroundColor: "var(--primary)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#ffffff",
                fontWeight: 700,
                fontSize: "14px",
              }}
            >
              D
            </div>
            <span style={{ fontWeight: 700, fontSize: "1.125rem", color: "var(--foreground)" }}>
              DealFlow360
            </span>
          </div>
          <div
            style={{
              fontSize: "0.75rem",
              fontWeight: 600,
              padding: "0.25rem 0.6rem",
              borderRadius: "9999px",
              backgroundColor: "#eff6ff",
              color: "var(--primary)",
              border: "1px solid #bfdbfe",
            }}
          >
            Phase 001–005 (G01 Foundation)
          </div>
        </header>

        <main style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem" }}>
          {children}
        </main>

        <footer
          style={{
            borderTop: "1px solid var(--border)",
            backgroundColor: "#ffffff",
            padding: "1rem 2rem",
            textAlign: "center",
            fontSize: "0.875rem",
            color: "var(--muted)",
          }}
        >
          DealFlow360 &bull; Continuous Deal &amp; Discount Governance &bull; Master Roadmap G01
        </footer>
      </body>
    </html>
  );
}
