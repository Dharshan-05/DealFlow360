import React from "react";
import { LucideIcon, Inbox, Search, FilterX, ShieldX } from "lucide-react";
import { cn } from "@/lib/utils";

export interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
  variant?: "default" | "search" | "filtered" | "permission";
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
  variant = "default",
}: EmptyStateProps) {
  // Determine default icon based on variant if not explicitly provided
  const ResolvedIcon =
    Icon ||
    (variant === "search"
      ? Search
      : variant === "filtered"
      ? FilterX
      : variant === "permission"
      ? ShieldX
      : Inbox);

  const iconColorStyles = {
    default: "bg-slate-100 text-muted",
    search: "bg-blue-50 text-primary",
    filtered: "bg-amber-50 text-amber-600",
    permission: "bg-rose-50 text-rose-600",
  };

  return (
    <div
      role="region"
      aria-label={title}
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-dashed border-border p-8 text-center",
        className
      )}
    >
      <div
        className={cn(
          "mb-4 flex h-12 w-12 items-center justify-center rounded-full",
          iconColorStyles[variant]
        )}
      >
        <ResolvedIcon className="h-6 w-6" aria-hidden="true" />
      </div>
      <h4 className="text-base font-semibold text-foreground">{title}</h4>
      <p className="mt-1 max-w-sm text-sm text-muted leading-relaxed">{description}</p>
      {action && <div className="mt-6 flex items-center gap-3">{action}</div>}
    </div>
  );
}
