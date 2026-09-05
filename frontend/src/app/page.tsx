"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LoadingState } from "@/components/ui/loading-state";
import {
  ShieldCheck,
  CheckCircle2,
  Lock,
  Layers,
  LogOut,
  LogIn,
  UserPlus,
  Compass,
  Palette,
  LayoutDashboard,
  Users,
  Package,
  Navigation,
  Smartphone,
  Loader2,
  Inbox,
  AlertCircle,
  Repeat,
  Scale,
  ListTree,
  Sliders,
  Warehouse as WarehouseIcon,
} from "lucide-react";

export default function HomePage() {
  const { user, isAuthenticated, isLoading, logout } = useAuth();

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Welcome / Hero Card */}
      <Card className="border-border shadow-sm">
        <CardHeader className="pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2.5">
                <CardTitle className="text-2xl font-bold tracking-tight text-foreground">
                  DealFlow360
                </CardTitle>
                <Badge variant="primary" className="font-mono">
                  G19 (Phases 091–095)
                </Badge>
              </div>
              <CardDescription className="text-sm text-muted mt-1">
                Continuous Deal &amp; Discount Governance &mdash; Warehouse Priority, Multi-Facility Allocation &amp; Stock Reservation
              </CardDescription>
            </div>
            {isAuthenticated && user && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => logout()}
                className="self-start sm:self-center gap-1.5"
                aria-label="Sign out of your session"
              >
                <LogOut className="h-4 w-4" aria-hidden="true" />
                <span>Sign Out</span>
              </Button>
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* User Session State */}
          {isLoading ? (
            <LoadingState message="Verifying authentication session..." />
          ) : isAuthenticated && user ? (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50/70 p-4 text-emerald-950">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div>
                  <div className="font-semibold text-base text-emerald-900">
                    Welcome back, {user.first_name} {user.last_name}!
                  </div>
                  <div className="text-xs text-emerald-700 font-mono mt-0.5">{user.email}</div>
                </div>
                <div className="flex flex-wrap items-center gap-1.5 pt-1 sm:pt-0">
                  <span className="text-xs font-semibold text-emerald-800 mr-1">Active Roles:</span>
                  {user.roles && user.roles.length > 0 ? (
                    user.roles.map((role) => (
                      <Badge key={role} variant="success" className="text-[11px]">
                        {role}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-xs italic text-emerald-700">No roles assigned</span>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-lg border border-blue-200 bg-blue-50/60 p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <div className="font-semibold text-sm text-blue-900">
                  Ready for Authenticated Session
                </div>
                <div className="text-xs text-blue-700 mt-0.5">
                  Sign in or register to experience the role-aware application shell.
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Link href="/login">
                  <Button size="sm" className="gap-1.5">
                    <LogIn className="h-4 w-4" aria-hidden="true" />
                    <span>Sign In</span>
                  </Button>
                </Link>
                <Link href="/register">
                  <Button variant="outline" size="sm" className="gap-1.5">
                    <UserPlus className="h-4 w-4" aria-hidden="true" />
                    <span>Register</span>
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Grid: Foundation Status & Modules */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Warehouse Priority & Fulfillment Allocation (G19) */}
        <Card className="border-primary/40 shadow-sm ring-1 ring-primary/10">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <WarehouseIcon className="h-5 w-5 text-primary" />
                <CardTitle className="text-base font-semibold">
                  Warehouse Priority &amp; Allocation (G19)
                </CardTitle>
              </div>
              <Link href="/warehouses">
                <Button variant="primary" size="sm" className="h-7 text-xs">
                  Fulfillment Hub
                </Button>
              </Link>
            </div>
            <CardDescription className="text-xs text-muted">
              Facility priority, deterministic selection, multi-warehouse stock, and sequential allocation
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 091 &mdash; Warehouse Priority
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 092 &mdash; Warehouse Selection
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 093 &mdash; Multi-Warehouse Stock
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 094 &mdash; Fulfillment Allocation
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 text-sm">
              <span className="font-medium text-slate-700">
                Phase 095 &mdash; Stock Reservation
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Warehouse & Inventory Foundation (G18) */}
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <WarehouseIcon className="h-5 w-5 text-primary" />
                <CardTitle className="text-base font-semibold">
                  Warehouse &amp; Inventory (G18)
                </CardTitle>
              </div>
              <Link href="/warehouses">
                <Button variant="outline" size="sm" className="h-7 text-xs">
                  Manage Warehouses
                </Button>
              </Link>
            </div>
            <CardDescription className="text-xs text-muted">
              Facility CRUD, warehouse stock, availability check, reserved stock, and ATP
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 086 &mdash; Warehouse CRUD
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 087 &mdash; Warehouse Stock
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 088 &mdash; Stock Availability API
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 089 &mdash; Reserved Stock
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 text-sm">
              <span className="font-medium text-slate-700">
                Phase 090 &mdash; Available-to-Promise (ATP)
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Product Intelligence & Inventory Foundation (G17) */}
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Package className="h-5 w-5 text-primary" />
                <CardTitle className="text-base font-semibold">
                  Product Intelligence &amp; Inventory (G17)
                </CardTitle>
              </div>
              <Link href="/products">
                <Button variant="primary" size="sm" className="h-7 text-xs">
                  Open Product Hub
                </Button>
              </Link>
            </div>
            <CardDescription className="text-xs text-muted">
              Recurring billing cycles, inventory levels, search, filtering, and interactive dashboard
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 081 &mdash; Recurring Frequency
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 082 &mdash; Product Inventory
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 083 &mdash; Product Search
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 084 &mdash; Product Filtering
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 text-sm">
              <span className="font-medium text-slate-700">
                Phase 085 &mdash; Product Dashboard
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Product Configurations Foundation (G16) */}
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Package className="h-5 w-5 text-primary" />
                <CardTitle className="text-base font-semibold">
                  Product Configurations (G16)
                </CardTitle>
              </div>
              <Link href="/products">
                <Button variant="outline" size="sm" className="h-7 text-xs">
                  Manage Products
                </Button>
              </Link>
            </div>
            <CardDescription className="text-xs text-muted">
              Product tax, units of measure, variants, attributes, and subscriptions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 076 &mdash; Product Tax
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 077 &mdash; Product Units
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 078 &mdash; Product Variants
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 079 &mdash; Product Attributes
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 text-sm">
              <span className="font-medium text-slate-700">
                Phase 080 &mdash; Subscription Products
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Product Catalog Baseline (G15) */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Package className="h-5 w-5 text-primary" />
                <CardTitle className="text-base font-semibold">
                  Catalog &amp; Margins (G15)
                </CardTitle>
              </div>
              <Link href="/products">
                <Button variant="outline" size="sm" className="h-7 text-xs">
                  View Catalog
                </Button>
              </Link>
            </div>
            <CardDescription className="text-xs text-muted">
              Product CRUD, categories, base pricing, unit cost, and derived gross margins
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 071 &mdash; Product CRUD
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 072 &mdash; Product Categories
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 073 &mdash; Product Pricing
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 074 &mdash; Product Cost
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 text-sm">
              <span className="font-medium text-slate-700">
                Phase 075 &mdash; Product Margin
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Customer Management Foundation (G12) */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5 text-primary" />
                <CardTitle className="text-base font-semibold">
                  Customer Management (G12)
                </CardTitle>
              </div>
              <Link href="/customers">
                <Button variant="outline" size="sm" className="h-7 text-xs">
                  View Customers
                </Button>
              </Link>
            </div>
            <CardDescription className="text-xs text-muted">
              Customer accounts, profiles, discount tier governance, and history
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 056 &mdash; Customer CRUD
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 057 &mdash; Customer Profile
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 058 &mdash; Customer Tier Management
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 059 &mdash; Customer Purchase History
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 text-sm">
              <span className="font-medium text-slate-700">
                Phase 060 &mdash; Customer Deal History
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Customer Analytics & Dashboard Foundation (G14) */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5 text-primary" />
                <CardTitle className="text-base font-semibold">
                  Analytics &amp; Dashboard (G14)
                </CardTitle>
              </div>
              <Link href="/customers">
                <Button variant="outline" size="sm" className="h-7 text-xs">
                  View Dashboard
                </Button>
              </Link>
            </div>
            <CardDescription className="text-xs text-muted">
              Portfolio analytics, multi-field search, composable filtering, segmentation, and interactive dashboard
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 066 &mdash; Customer Analytics
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 067 &mdash; Customer Search
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 068 &mdash; Customer Filtering
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 069 &mdash; Customer Segmentation
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 text-sm">
              <span className="font-medium text-slate-700">
                Phase 070 &mdash; Customer Dashboard
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Roadmap Scope Notice Card */}
      <Card className="bg-slate-50/80 border-dashed">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <Lock className="h-5 w-5 text-muted mt-0.5 flex-shrink-0" aria-hidden="true" />
            <div className="text-xs text-muted leading-relaxed">
              <p className="font-semibold text-slate-700 mb-1">
                Strict Roadmap Guardrails Active (Phases 091+ Locked)
              </p>
              <p>
                In strict compliance with the 520-phase DealFlow360 master roadmap, Phase 091+ features
                (Warehouse Priority, Warehouse Selection, Multi-Warehouse Stock orchestration, Fulfillment Allocation,
                Stock Reservation workflows, Backorders, Delivery Management, Inventory Alerts, Inventory Dashboard,
                Quotation Workflows, Negotiation, Approval Systems, and Invoicing) remain strictly locked.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
