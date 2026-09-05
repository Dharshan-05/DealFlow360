"use client";

import React from "react";
import { AuthProvider } from "@/context/AuthContext";
import { UIProvider } from "@/context/UIContext";
import { ToastProvider } from "@/context/ToastContext";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <UIProvider>
        <ToastProvider>{children}</ToastProvider>
      </UIProvider>
    </AuthProvider>
  );
}
