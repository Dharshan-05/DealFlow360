import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";

export interface SelectProps
  extends React.SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, error, disabled, children, ...props }, ref) => {
    return (
      <div className="relative">
        <select
          ref={ref}
          disabled={disabled}
          aria-invalid={error ? "true" : undefined}
          className={cn(
            "flex h-10 w-full appearance-none rounded-lg border border-border bg-white px-3 py-2 text-sm text-foreground shadow-sm transition-colors",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:border-transparent",
            "disabled:cursor-not-allowed disabled:bg-slate-50 disabled:opacity-60",
            error && "border-rose-400 focus-visible:ring-rose-400",
            className
          )}
          {...props}
        >
          {children}
        </select>
        <div
          className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400"
          aria-hidden="true"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
    );
  }
);

Select.displayName = "Select";
