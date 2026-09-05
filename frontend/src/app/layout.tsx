import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/Providers";
import { ApplicationShell } from "@/components/layout/ApplicationShell";

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
        <Providers>
          <ApplicationShell>{children}</ApplicationShell>
        </Providers>
      </body>
    </html>
  );
}
