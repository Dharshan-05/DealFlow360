"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Menu, PanelLeftClose, PanelLeft, LogOut, ArrowLeft } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useUI } from "@/context/UIContext";
import { SidebarNav } from "@/components/navigation/SidebarNav";
import { MobileNav } from "@/components/navigation/MobileNav";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ApplicationShellProps {
  children: React.ReactNode;
}

export function ApplicationShell({ children }: ApplicationShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const { sidebarOpen, toggleSidebar, openMobileNav } = useUI();

  const isAuthPage = pathname === "/login" || pathname === "/register";

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const userRoles = user?.roles || [];
  const primaryRole = userRoles.length > 0 ? userRoles[0] : "Authenticated User";

  // Auth pages (login / register) render a focused layout without sidebars
  if (isAuthPage) {
    return (
      <div className="flex min-h-screen flex-col bg-slate-50 text-foreground">
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-border bg-white px-6">
          <Link href="/" className="flex items-center gap-2.5 rounded-md p-1 focus:outline-none focus:ring-2 focus:ring-primary">
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

        <main className="flex flex-1 items-center justify-center p-4 sm:p-6">
          {children}
        </main>

        <footer className="border-t border-border bg-white p-4 text-center text-xs text-muted">
          DealFlow360 &bull; Continuous Deal &amp; Discount Governance &bull; Master Roadmap G09
        </footer>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-foreground">
      {/* Top Header */}
      <header className="sticky top-0 z-40 flex h-16 shrink-0 items-center justify-between border-b border-border bg-white px-4 sm:px-6 shadow-sm">
        <div className="flex items-center gap-3">
          {/* Mobile hamburger toggle */}
          <button
            type="button"
            onClick={openMobileNav}
            aria-label="Open mobile navigation"
            className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary lg:hidden"
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>

          {/* Desktop collapse toggle */}
          {isAuthenticated && (
            <button
              type="button"
              onClick={toggleSidebar}
              aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
              className="hidden h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary lg:flex"
            >
              {sidebarOpen ? (
                <PanelLeftClose className="h-5 w-5" aria-hidden="true" />
              ) : (
                <PanelLeft className="h-5 w-5" aria-hidden="true" />
              )}
            </button>
          )}

          {/* Logo / Brand */}
          <Link href="/" className="flex items-center gap-2.5 rounded-md p-1 focus:outline-none focus:ring-2 focus:ring-primary">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-white font-extrabold text-sm shadow-sm">
              D
            </div>
            <span className="font-bold text-lg text-foreground tracking-tight hidden sm:inline">
              DealFlow360
            </span>
          </Link>

          <Badge variant="primary" className="hidden sm:inline-flex ml-2">
            G09 Foundation (Phases 001–045)
          </Badge>
        </div>

        {/* Header Right / Account Area */}
        <div className="flex items-center gap-3 sm:gap-4">
          {isLoading ? (
            <div className="h-8 w-24 animate-pulse rounded bg-slate-100" />
          ) : isAuthenticated && user ? (
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex flex-col items-end text-right">
                <span className="text-xs font-bold text-foreground">
                  {user.first_name} {user.last_name}
                </span>
                <span className="text-[11px] text-muted">{user.email}</span>
              </div>
              <Badge variant="outline" className="hidden md:inline-flex text-[11px]">
                {primaryRole}
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
                className="gap-1.5 text-xs text-slate-600 hover:text-red-600 hover:border-red-200"
                title="Sign out of your account"
              >
                <LogOut className="h-3.5 w-3.5" aria-hidden="true" />
                <span className="hidden sm:inline">Sign Out</span>
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link href="/login">
                <Button variant="ghost" size="sm">
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
                <Button variant="primary" size="sm">
                  Register
                </Button>
              </Link>
            </div>
          )}
        </div>
      </header>

      {/* Main Container: Sidebar + Content */}
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
          className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 flex flex-col justify-between"
        >
          <div className="mx-auto w-full max-w-6xl">{children}</div>

          {/* Footer */}
          <footer className="mt-12 pt-6 border-t border-border text-center text-xs text-muted">
            DealFlow360 &bull; Continuous Deal &amp; Discount Governance &bull; Master Roadmap G09
          </footer>
        </main>
      </div>
    </div>
  );
}
