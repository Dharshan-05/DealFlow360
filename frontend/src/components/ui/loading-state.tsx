import React from "react";
import { cn } from "@/lib/utils";

export interface LoadingStateProps {
  message?: string;
  className?: string;
  variant?: "spinner" | "inline" | "page" | "skeleton";
}

export function LoadingState({
  message = "Loading...",
  className,
  variant = "spinner",
}: LoadingStateProps) {
  if (variant === "inline") {
    return (
      <div
        role="status"
        aria-live="polite"
        aria-busy="true"
        className={cn("inline-flex items-center gap-2 text-sm text-muted", className)}
      >
        <div
          className="h-4 w-4 animate-spin rounded-full border-2 border-slate-200 border-t-primary"
          aria-hidden="true"
        />
        <span>{message}</span>
        <span className="sr-only">{message}</span>
      </div>
    );
  }

  if (variant === "skeleton") {
    return (
      <div
        role="status"
        aria-live="polite"
        aria-busy="true"
        className={cn("w-full space-y-3 p-4", className)}
      >
        <div className="h-6 w-1/3 animate-pulse rounded bg-slate-200" />
        <div className="h-4 w-full animate-pulse rounded bg-slate-100" />
        <div className="h-4 w-5/6 animate-pulse rounded bg-slate-100" />
        <span className="sr-only">{message}</span>
      </div>
    );
  }

  if (variant === "page") {
    return (
      <div
        role="status"
        aria-live="polite"
        aria-busy="true"
        className={cn(
          "flex min-h-[50vh] flex-col items-center justify-center p-8 text-center space-y-4",
          className
        )}
      >
        <div
          className="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-primary"
          aria-hidden="true"
        />
        <div className="space-y-1">
          <p className="text-base font-semibold text-foreground">{message}</p>
          <p className="text-xs text-muted">Please wait while the system prepares your workspace</p>
        </div>
        <span className="sr-only">{message}</span>
      </div>
    );
  }

  // Default spinner
  return (
    <div
      role="status"
      aria-live="polite"
      aria-busy="true"
      className={cn(
        "flex flex-col items-center justify-center min-h-[240px] p-6 text-center space-y-3",
        className
      )}
    >
      <div
        className="h-8 w-8 animate-spin rounded-full border-3 border-slate-200 border-t-primary"
        aria-hidden="true"
      />
      <p className="text-sm font-medium text-muted">{message}</p>
      <span className="sr-only">{message}</span>
    </div>
  );
}
