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
  Navigation,
  Smartphone,
  Loader2,
  Inbox,
  AlertCircle
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
                  G12 (Phases 056–060)
                </Badge>
              </div>
              <CardDescription className="text-sm text-muted mt-1">
                Continuous Deal &amp; Discount Governance &mdash; Enterprise Architecture
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

      {/* Grid: Foundation Status & Design System */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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

        {/* UI Infrastructure Layer (G11) */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <LayoutDashboard className="h-5 w-5 text-primary" />
              <CardTitle className="text-base font-semibold">
                UI Infrastructure (G11)
              </CardTitle>
            </div>
            <CardDescription className="text-xs text-muted">
              Toast notifications, modal system, forms, data table, and charts system
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 051 &mdash; Toast Notifications
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 052 &mdash; Modal System
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 053 &mdash; Form System
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-border/50 text-sm">
              <span className="font-medium text-slate-700">
                Phase 054 &mdash; Data Table System
              </span>
              <Badge variant="success">Operational</Badge>
            </div>
            <div className="flex items-center justify-between py-1 text-sm">
              <span className="font-medium text-slate-700">
                Phase 055 &mdash; Charts System
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
                Strict Roadmap Guardrails Active (Phases 061+ Locked)
              </p>
              <p>
                In strict compliance with the 520-phase DealFlow360 master roadmap, customer discount
                history and lifetime value calculations (Phase 061+), quotation business logic, pricing
                engines, discount matrices, approval workflows, inventory allocation, and billing systems
                remain strictly locked.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
