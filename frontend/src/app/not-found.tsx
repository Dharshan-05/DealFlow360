import React from "react";
import { ErrorState } from "@/components/ui/error-state";

export default function NotFound() {
  return (
    <ErrorState
      variant="notFound"
      title="Page Not Found (404)"
      message="The DealFlow360 resource or path you requested does not exist or may belong to a future roadmap phase."
      homeHref="/"
    />
  );
}
