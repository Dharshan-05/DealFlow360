"use client";

import React from "react";
import { Warehouse } from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/context/AuthContext";
import { EmptyState } from "@/components/ui/empty-state";
import { UnauthorizedState } from "@/components/ui/unauthorized-state";
import { Badge } from "@/components/ui/badge";

export default function WarehousesPage() {
  const { user } = useAuth();
  const allowedRoles = ["Operations", "Admin"];
  const hasAccess = user?.roles.some((r) => allowedRoles.includes(r)) || user?.roles.includes("Admin");

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">Warehouses &amp; Logistics</h1>
            <p className="text-sm text-muted">Distribution facilities and fulfillment routing</p>
          </div>
          <Badge variant="outline">Scheduled: Future Phase</Badge>
        </div>

        {!hasAccess ? (
          <UnauthorizedState message="Warehouse and fulfillment management is restricted to Operations and System Administrators." />
        ) : (
          <EmptyState
            icon={Warehouse}
            title="Warehouse Operations Foundation"
            description="Multi-warehouse inventory reservation, transfer routing, and split-shipment fulfillment will be activated in future authorized roadmap phases."
          />
        )}
      </div>
    </ProtectedRoute>
  );
}
