"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Menu,
  PanelLeftClose,
  PanelLeft,
  LogOut,
  User as UserIcon,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useUI } from "@/context/UIContext";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export function TopNav() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const { sidebarOpen, toggleSidebar, openMobileNav } = useUI();

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const userRoles = user?.roles || [];
  const primaryRole = userRoles.length > 0 ? userRoles[0] : "Authenticated User";

  // Friendly title based on pathname
  const getPageTitle = (path: string) => {
    switch (path) {
      case "/":
        return "Dashboard";
      case "/quotations":
        return "Quotations";
      case "/governance":
        return "Discount Governance";
      case "/warehouses":
        return "Warehouses & Logistics";
      case "/audit-logs":
        return "Audit Logs";
      case "/settings":
        return "System Settings";
      default:
        return "";
    }
  };

  const pageTitle = getPageTitle(pathname);

  return (
    <header
      role="banner"
      aria-label="Global Top Navigation"
      className="sticky top-0 z-40 flex h-16 shrink-0 items-center justify-between border-b border-border bg-white px-4 sm:px-6 shadow-sm"
    >
      {/* Left section: Navigation triggers & Brand */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Mobile menu trigger */}
        {isAuthenticated && (
          <button
            type="button"
            onClick={openMobileNav}
            aria-label="Open mobile navigation"
            className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary lg:hidden"
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>
        )}

        {/* Desktop sidebar toggle trigger */}
        {isAuthenticated && (
          <button
            type="button"
            onClick={toggleSidebar}
            aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
            className="hidden h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary lg:flex"
          >
            {sidebarOpen ? (
              <PanelLeftClose className="h-5 w-5" aria-hidden="true" />
            ) : (
              <PanelLeft className="h-5 w-5" aria-hidden="true" />
            )}
          </button>
        )}

        {/* Brand identity */}
        <Link
          href="/"
          className="flex items-center gap-2.5 rounded-md p-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          aria-label="DealFlow360 Home"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-white font-extrabold text-sm shadow-sm">
            D
          </div>
          <span className="font-bold text-lg text-foreground tracking-tight hidden sm:inline">
            DealFlow360
          </span>
        </Link>

        {/* Active Route Indicator */}
        {pageTitle && (
          <div className="hidden md:flex items-center ml-3 pl-3 border-l border-slate-200">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              {pageTitle}
            </span>
          </div>
        )}
      </div>

      {/* Right section: User info & Actions */}
      <div className="flex items-center gap-3 sm:gap-4">
        {isLoading ? (
          <div
            role="status"
            aria-label="Loading authentication state"
            className="h-8 w-28 animate-pulse rounded bg-slate-100"
          />
        ) : isAuthenticated && user ? (
          <div className="flex items-center gap-3">
            {/* User profile details */}
            <div className="flex items-center gap-2">
              <div
                className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-slate-600 border border-slate-200 text-xs font-semibold"
                aria-hidden="true"
              >
                {user.first_name ? user.first_name[0].toUpperCase() : <UserIcon className="h-4 w-4" />}
              </div>
              <div className="hidden sm:flex flex-col items-start text-left">
                <span className="text-xs font-bold text-foreground leading-tight">
                  {user.first_name} {user.last_name}
                </span>
                <span className="text-[11px] text-muted leading-tight">{user.email}</span>
              </div>
            </div>

            {/* Primary role badge */}
            <Badge variant="outline" className="hidden md:inline-flex text-[11px]">
              {primaryRole}
            </Badge>

            {/* Sign Out Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
              className="gap-1.5 text-xs text-slate-600 hover:text-red-600 hover:border-red-200"
              aria-label="Sign out of your account"
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
  );
}
