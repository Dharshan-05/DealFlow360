"use client";

import React from "react";
import { Percent } from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/context/AuthContext";
import { EmptyState } from "@/components/ui/empty-state";
import { UnauthorizedState } from "@/components/ui/unauthorized-state";
import { Badge } from "@/components/ui/badge";

export default function GovernancePage() {
  const { user } = useAuth();
  const allowedRoles = ["Sales Manager", "Finance", "Admin"];
  const hasAccess = user?.roles.some((r) => allowedRoles.includes(r)) || user?.roles.includes("Admin");

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">Discount Governance</h1>
            <p className="text-sm text-muted">Margin policy evaluation and approval chains</p>
          </div>
          <Badge variant="outline">Scheduled: Future Phase</Badge>
        </div>

        {!hasAccess ? (
          <UnauthorizedState message="Discount governance policies are restricted to Sales Managers, Finance officers, and System Administrators." />
        ) : (
          <EmptyState
            icon={Percent}
            title="Discount Governance Engine"
            description="Automated discount threshold calculations, blended margin compliance, and multi-tier approval routing are scheduled for future authorized roadmap phases."
          />
        )}
      </div>
    </ProtectedRoute>
  );
}
