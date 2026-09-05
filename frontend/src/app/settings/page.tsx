"use client";

import React from "react";
import { Settings } from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/context/AuthContext";
import { EmptyState } from "@/components/ui/empty-state";
import { UnauthorizedState } from "@/components/ui/unauthorized-state";
import { Badge } from "@/components/ui/badge";

export default function SettingsPage() {
  const { user } = useAuth();
  const hasAccess = user?.roles.includes("Admin");

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">System Settings</h1>
            <p className="text-sm text-muted">Organization configuration and administration</p>
          </div>
          <Badge variant="outline">Scheduled: Future Phase</Badge>
        </div>

        {!hasAccess ? (
          <UnauthorizedState message="System settings and organization parameters are restricted exclusively to Administrators." />
        ) : (
          <EmptyState
            icon={Settings}
            title="Enterprise Configuration"
            description="System parameters, tenant configuration, and integration credentials will be managed here in future authorized roadmap phases."
          />
        )}
      </div>
    </ProtectedRoute>
  );
}
