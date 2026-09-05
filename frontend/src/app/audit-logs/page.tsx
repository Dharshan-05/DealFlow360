"use client";

import React from "react";
import { ShieldCheck } from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/context/AuthContext";
import { EmptyState } from "@/components/ui/empty-state";
import { UnauthorizedState } from "@/components/ui/unauthorized-state";
import { Badge } from "@/components/ui/badge";

export default function AuditLogsPage() {
  const { user } = useAuth();
  const allowedRoles = ["Admin", "Sales Manager", "Finance"];
  const hasAccess = user?.roles.some((r) => allowedRoles.includes(r)) || user?.roles.includes("Admin");

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">Audit Logs</h1>
            <p className="text-sm text-muted">Immutable security and governance event stream</p>
          </div>
          <Badge variant="outline">Scheduled: Future Phase</Badge>
        </div>

        {!hasAccess ? (
          <UnauthorizedState message="System audit logs are restricted to Administrators, Sales Managers, and Finance officers." />
        ) : (
          <EmptyState
            icon={ShieldCheck}
            title="System Audit Log Explorer"
            description="The immutable audit trail view for compliance verification and deal history will be connected in future authorized roadmap phases."
          />
        )}
      </div>
    </ProtectedRoute>
  );
}
