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
                  G16 (Phases 076–080)
                </Badge>
              </div>
              <CardDescription className="text-sm text-muted mt-1">
                Continuous Deal &amp; Discount Governance &mdash; Product Tax, Units, Variants, Attributes &amp; Subscriptions
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
        {/* Product Configurations Foundation (G16) */}
        <Card className="border-primary/30 shadow-xs">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Package className="h-5 w-5 text-primary" />
                <CardTitle className="text-base font-semibold">
                  Product Configurations (G16)
                </CardTitle>
              </div>
              <Link href="/products">
                <Button variant="primary" size="sm" className="h-7 text-xs">
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
                Strict Roadmap Guardrails Active (Phases 081+ Locked)
              </p>
              <p>
                In strict compliance with the 520-phase DealFlow360 master roadmap, Recurring Billing Frequencies,
                Billing Intervals, Invoices, Renewals (Phase 081+), Inventory &amp; Stock Levels, Warehouses, Quotation Workflows,
                Approval Systems, and Discount Engines remain strictly locked.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
