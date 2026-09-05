"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useUI } from "@/context/UIContext";
import { SidebarNav } from "@/components/navigation/SidebarNav";
import { MobileNav } from "@/components/navigation/MobileNav";
import { TopNav } from "@/components/navigation/TopNav";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ApplicationShellProps {
  children: React.ReactNode;
}

export function ApplicationShell({ children }: ApplicationShellProps) {
  const pathname = usePathname();
  const { user, isAuthenticated } = useAuth();
  const { sidebarOpen } = useUI();

  const isAuthPage = pathname === "/login" || pathname === "/register";
  const userRoles = user?.roles || [];

  // Auth pages (login / register) render a focused layout without sidebars
  if (isAuthPage) {
    return (
      <div className="flex min-h-screen flex-col bg-slate-50 text-foreground">
        <header
          role="banner"
          className="flex h-16 shrink-0 items-center justify-between border-b border-border bg-white px-4 sm:px-6"
        >
          <Link
            href="/"
            className="flex items-center gap-2.5 rounded-md p-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            aria-label="DealFlow360 Home"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-white font-extrabold text-sm shadow-sm">
              D
            </div>
            <span className="font-bold text-lg text-foreground tracking-tight">DealFlow360</span>
          </Link>
          <Link href="/">
            <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-muted hover:text-foreground">
              <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Back to Home</span>
            </Button>
          </Link>
        </header>

        <main id="main-content" className="flex flex-1 items-center justify-center p-4 sm:p-6">
          {children}
        </main>

        <footer role="contentinfo" className="border-t border-border bg-white p-4 text-center text-xs text-muted">
          DealFlow360 &bull; Continuous Deal &amp; Discount Governance &bull; Master Roadmap G10
        </footer>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-foreground">
      {/* Skip to main content link for keyboard accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-white focus:shadow-md focus:outline-none"
      >
        Skip to main content
      </a>

      {/* Global Top Navigation (Phase 046) */}
      <TopNav />

      {/* Main Container: Responsive Sidebar + Content (Phase 047) */}
      <div className="flex flex-1 overflow-hidden">
        {/* Persistent Desktop Sidebar */}
        {isAuthenticated && (
          <aside
            aria-label="Sidebar Navigation"
            className={cn(
              "hidden shrink-0 border-r border-border bg-white transition-all duration-200 lg:block overflow-y-auto",
              sidebarOpen ? "w-64 p-5" : "w-16 p-2"
            )}
          >
            <SidebarNav userRoles={userRoles} isCollapsed={!sidebarOpen} />
          </aside>
        )}

        {/* Mobile Navigation Drawer */}
        {isAuthenticated && <MobileNav userRoles={userRoles} />}

        {/* Content Region */}
        <main
          id="main-content"
          role="main"
          tabIndex={-1}
          className="flex-1 overflow-y-auto overflow-x-hidden p-4 sm:p-6 lg:p-8 flex flex-col justify-between focus:outline-none"
        >
          <div className="mx-auto w-full max-w-6xl">{children}</div>

          {/* Footer */}
          <footer role="contentinfo" className="mt-12 pt-6 border-t border-border text-center text-xs text-muted">
            DealFlow360 &bull; Continuous Deal &amp; Discount Governance &bull; Master Roadmap G10
          </footer>
        </main>
      </div>
    </div>
  );
}
