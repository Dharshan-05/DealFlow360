import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, disabled, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        disabled={disabled}
        aria-invalid={error ? "true" : undefined}
        className={cn(
          "flex min-h-[80px] w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-foreground shadow-sm transition-colors",
          "placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:border-transparent",
          "disabled:cursor-not-allowed disabled:bg-slate-50 disabled:opacity-60",
          error && "border-rose-400 focus-visible:ring-rose-400",
          className
        )}
        {...props}
      />
    );
  }
);

Textarea.displayName = "Textarea";
