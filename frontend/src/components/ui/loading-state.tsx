import React from "react";
import { cn } from "@/lib/utils";

interface LoadingStateProps {
  message?: string;
  className?: string;
}

export function LoadingState({
  message = "Loading...",
  className,
}: LoadingStateProps) {
  return (
    <div
      role="status"
      aria-live="polite"
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
