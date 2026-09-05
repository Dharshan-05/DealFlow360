"use client";

import React from "react";
import { X } from "lucide-react";
import { useUI } from "@/context/UIContext";
import { SidebarNav } from "./SidebarNav";

interface MobileNavProps {
  userRoles?: string[];
}

export function MobileNav({ userRoles = [] }: MobileNavProps) {
  const { mobileNavOpen, closeMobileNav } = useUI();

  if (!mobileNavOpen) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Mobile Navigation">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity"
        onClick={closeMobileNav}
        aria-hidden="true"
      />

      {/* Drawer Panel */}
      <div className="fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-white p-5 shadow-2xl transition-transform">
        <div className="flex items-center justify-between pb-4 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary text-white font-bold text-xs">
              D
            </div>
            <span className="font-bold text-base text-foreground tracking-tight">DealFlow360</span>
          </div>
          <button
            onClick={closeMobileNav}
            aria-label="Close navigation menu"
            className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto pt-5">
          <SidebarNav userRoles={userRoles} onItemClick={closeMobileNav} />
        </div>
      </div>
    </div>
  );
}
