"use client";

import React from "react";
import { FileText } from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/context/AuthContext";
import { EmptyState } from "@/components/ui/empty-state";
import { UnauthorizedState } from "@/components/ui/unauthorized-state";
import { Badge } from "@/components/ui/badge";

export default function QuotationsPage() {
  const { user } = useAuth();
  const allowedRoles = ["Sales Representative", "Sales Manager", "Admin", "Customer Portal"];
  const hasAccess = user?.roles.some((r) => allowedRoles.includes(r)) || user?.roles.includes("Admin");

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">Quotations</h1>
            <p className="text-sm text-muted">Deal drafting and line-item orchestration</p>
          </div>
          <Badge variant="outline">Scheduled: Group 10 (Phase 046+)</Badge>
        </div>

        {!hasAccess ? (
          <UnauthorizedState />
        ) : (
          <EmptyState
            icon={FileText}
            title="Quotation Management Foundation"
            description="Quotation lifecycle, dynamic line-item calculation, and revision tracking are scheduled for implementation in Group 10 (Phase 046+) under the master roadmap."
          />
        )}
      </div>
    </ProtectedRoute>
  );
}
