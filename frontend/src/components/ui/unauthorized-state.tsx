import React from "react";
import Link from "next/link";
import { ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";

interface UnauthorizedStateProps {
  title?: string;
  message?: string;
}

export function UnauthorizedState({
  title = "Access Restricted",
  message = "You do not have permission to view or manage this section. Please contact your organization administrator if you require access.",
}: UnauthorizedStateProps) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center"
    >
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-rose-50 text-rose-600 border border-rose-200">
        <ShieldAlert className="h-7 w-7" aria-hidden="true" />
      </div>
      <h2 className="text-xl font-bold text-foreground">{title}</h2>
      <p className="mt-2 max-w-md text-sm text-muted leading-relaxed">{message}</p>
      <div className="mt-6">
        <Link href="/">
          <Button variant="outline" size="sm">
            Return to Dashboard
          </Button>
        </Link>
      </div>
    </div>
  );
}
