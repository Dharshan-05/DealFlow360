"use client";

import React from "react";
import { ErrorState } from "@/components/ui/error-state";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <ErrorState
      variant="server"
      title="Application Error"
      message="DealFlow360 encountered an unexpected runtime condition. You can attempt to reload the component or return to the main dashboard."
      onRetry={reset}
      homeHref="/"
    />
  );
}
