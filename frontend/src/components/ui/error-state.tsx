import React from "react";
import Link from "next/link";
import { AlertTriangle, WifiOff, FileQuestion, ShieldAlert, RotateCcw, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface ErrorStateProps {
  title?: string;
  message?: string;
  variant?: "generic" | "server" | "network" | "notFound" | "permission";
  onRetry?: () => void;
  homeHref?: string;
  className?: string;
}

export function ErrorState({
  title,
  message,
  variant = "generic",
  onRetry,
  homeHref = "/",
  className,
}: ErrorStateProps) {
  const configs = {
    generic: {
      defaultTitle: "Something Went Wrong",
      defaultMessage:
        "An unexpected error occurred while processing your request. Please try again or return to the dashboard.",
      icon: AlertTriangle,
      iconBg: "bg-rose-50 text-rose-600 border-rose-200",
    },
    server: {
      defaultTitle: "Internal Server Error",
      defaultMessage:
        "The system encountered an internal condition that prevented completing the request. Our engineering team has been notified.",
      icon: AlertTriangle,
      iconBg: "bg-red-50 text-red-600 border-red-200",
    },
    network: {
      defaultTitle: "Connection Issue",
      defaultMessage:
        "Unable to communicate with the DealFlow360 backend service. Please check your network connection and retry.",
      icon: WifiOff,
      iconBg: "bg-amber-50 text-amber-600 border-amber-200",
    },
    notFound: {
      defaultTitle: "Page Not Found",
      defaultMessage:
        "The page or resource you are looking for does not exist, has been removed, or is not yet available in this roadmap phase.",
      icon: FileQuestion,
      iconBg: "bg-slate-100 text-slate-600 border-slate-200",
    },
    permission: {
      defaultTitle: "Access Restricted",
      defaultMessage:
        "You do not have the required role or authorization to access this section. Please contact your organization administrator.",
      icon: ShieldAlert,
      iconBg: "bg-rose-50 text-rose-600 border-rose-200",
    },
  };

  const config = configs[variant];
  const Icon = config.icon;
  const displayTitle = title || config.defaultTitle;
  const displayMessage = message || config.defaultMessage;

  return (
    <div
      role="alert"
      aria-live="assertive"
      className={cn(
        "flex flex-col items-center justify-center min-h-[360px] p-6 sm:p-8 text-center",
        className
      )}
    >
      <div
        className={cn(
          "mb-4 flex h-14 w-14 items-center justify-center rounded-full border shadow-sm",
          config.iconBg
        )}
      >
        <Icon className="h-7 w-7" aria-hidden="true" />
      </div>

      <h2 className="text-xl font-bold tracking-tight text-foreground">{displayTitle}</h2>
      <p className="mt-2 max-w-md text-sm text-muted leading-relaxed">{displayMessage}</p>

      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        {onRetry && (
          <Button
            variant="primary"
            size="sm"
            onClick={onRetry}
            className="gap-1.5"
            aria-label="Retry the failed operation"
          >
            <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Try Again</span>
          </Button>
        )}

        {homeHref && (
          <Link href={homeHref}>
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5 text-slate-700 hover:text-foreground"
              aria-label="Navigate to home dashboard"
            >
              <Home className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Return to Dashboard</span>
            </Button>
          </Link>
        )}
      </div>
    </div>
  );
}
