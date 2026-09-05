"use client";

import React from "react";
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from "lucide-react";
import { useToast, ToastType } from "@/context/ToastContext";
import { cn } from "@/lib/utils";

const toastIcons = {
  success: CheckCircle2,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
};

const toastStyles: Record<ToastType, { bg: string; border: string; iconColor: string }> = {
  success: {
    bg: "bg-emerald-50 text-emerald-950",
    border: "border-emerald-200",
    iconColor: "text-emerald-600",
  },
  error: {
    bg: "bg-rose-50 text-rose-950",
    border: "border-rose-200",
    iconColor: "text-rose-600",
  },
  warning: {
    bg: "bg-amber-50 text-amber-950",
    border: "border-amber-200",
    iconColor: "text-amber-600",
  },
  info: {
    bg: "bg-blue-50 text-blue-950",
    border: "border-blue-200",
    iconColor: "text-blue-600",
  },
};

export function ToastContainer() {
  const { toasts, dismiss } = useToast();

  if (toasts.length === 0) return null;

  return (
    <aside
      aria-label="Notification Center"
      aria-live="polite"
      className="fixed bottom-4 right-4 z-50 flex max-h-screen w-full max-w-sm flex-col gap-2.5 pointer-events-none p-4 sm:p-0 sm:bottom-6 sm:right-6"
    >
      {toasts.map((toast) => {
        const Icon = toastIcons[toast.type];
        const style = toastStyles[toast.type];

        return (
          <div
            key={toast.id}
            role="status"
            className={cn(
              "pointer-events-auto flex w-full items-start gap-3 rounded-lg border p-4 shadow-lg transition-all duration-200 animate-in fade-in slide-in-from-bottom-5",
              style.bg,
              style.border
            )}
          >
            <Icon className={cn("h-5 w-5 shrink-0 mt-0.5", style.iconColor)} aria-hidden="true" />

            <div className="flex-1 space-y-1 overflow-hidden">
              {toast.title && (
                <h5 className="text-sm font-semibold leading-none tracking-tight">
                  {toast.title}
                </h5>
              )}
              <p className="text-xs leading-relaxed opacity-90">{toast.message}</p>
            </div>

            <button
              type="button"
              onClick={() => dismiss(toast.id)}
              aria-label="Dismiss notification"
              className="shrink-0 rounded-md p-1 opacity-70 hover:opacity-100 hover:bg-black/5 focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        );
      })}
    </aside>
  );
}
