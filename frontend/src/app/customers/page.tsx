"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Users,
  Plus,
  Search,
  Phone,
  Mail,
  Edit2,
  Trash2,
  ExternalLink,
  ShieldCheck,
  Award,
  RefreshCw,
  TrendingUp,
  AlertTriangle,
  Layers,
  X,
} from "lucide-react";

import { useToast } from "@/context/ToastContext";
import { useAuth } from "@/context/AuthContext";
import { customersApi, customerTiersApi } from "@/lib/api";
import {
  Customer,
  CustomerTier,
  CustomerCreateInput,
  CustomerDashboardResponse,
  CustomerSegmentProfile,
} from "@/types/customer";
import { DataTable, ColumnDef } from "@/components/ui/data-table";
import { Modal } from "@/components/ui/modal";
import { FormItem, FormLabel } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { DonutChart, BarChart } from "@/components/ui/charts";

export default function CustomersPage() {
  const { user } = useAuth();
  const toast = useToast();

  // Core Data
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [tiers, setTiers] = useState<CustomerTier[]>([]);
  const [dashboardData, setDashboardData] = useState<CustomerDashboardResponse | null>(null);
  const [segmentationProfiles, setSegmentationProfiles] = useState<CustomerSegmentProfile[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Active View Tab: "directory" | "segmentation"
  const [activeTab, setActiveTab] = useState<"directory" | "segmentation">("directory");

  // Search & Filtering State (Phases 067 & 068)
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [debouncedSearch, setDebouncedSearch] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [tierFilter, setTierFilter] = useState<string>("all");

  // Create Customer Modal (Phase 056)
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false);
  const [createLoading, setCreateLoading] = useState<boolean>(false);
  const [newCustomer, setNewCustomer] = useState<CustomerCreateInput>({
    customer_code: "",
    name: "",
    email: "",
    phone: "",
    address: "",
    city: "",
    state: "",
    country: "",
    postal_code: "",
    tier_id: "",
  });

  // Edit Customer Modal
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const [editLoading, setEditLoading] = useState<boolean>(false);

  // Delete Customer Modal
  const [deletingCustomer, setDeletingCustomer] = useState<Customer | null>(null);
  const [deleteLoading, setDeleteLoading] = useState<boolean>(false);

  // Debounce search input by 300ms
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 300);
    return () => clearTimeout(handler);
  }, [searchTerm]);

  const loadData = useCallback(async () => {
    try {
      setError(null);
      const [custListRes, tierListRes, dashRes, segRes] = await Promise.all([
        customersApi.getAll({
          search: debouncedSearch.trim() || undefined,
          is_active: statusFilter === "all" ? undefined : statusFilter === "active",
          tier_id: tierFilter === "all" ? undefined : tierFilter,
        }),
        customerTiersApi.getAll(),
        customersApi.getDashboard().catch((err) => {
          console.warn("Failed to load dashboard metrics:", err);
          return null;
        }),
        customersApi.getSegmentation().catch((err) => {
          console.warn("Failed to load segmentation profiles:", err);
          return null;
        }),
      ]);

      setCustomers(custListRes.items);
      setTiers(tierListRes);
      if (dashRes) {
        setDashboardData(dashRes);
      }
      if (segRes) {
        setSegmentationProfiles(segRes.customers || []);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load customers.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [debouncedSearch, statusFilter, tierFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadData();
  };

  const handleResetFilters = () => {
    setSearchTerm("");
    setDebouncedSearch("");
    setStatusFilter("all");
    setTierFilter("all");
  };

  const hasActiveFilters = Boolean(
    searchTerm.trim() || statusFilter !== "all" || tierFilter !== "all"
  );

  // Create Customer Submit
  const handleCreateCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCustomer.customer_code.trim() || !newCustomer.name.trim()) {
      toast.error("Customer code and name are required.");
      return;
    }

    try {
      setCreateLoading(true);
      await customersApi.create({
        ...newCustomer,
        customer_code: newCustomer.customer_code.trim().toUpperCase(),
        name: newCustomer.name.trim(),
        tier_id: newCustomer.tier_id ? newCustomer.tier_id : null,
      });
      toast.success(`Customer "${newCustomer.name}" created successfully.`);
      setIsCreateOpen(false);
      setNewCustomer({
        customer_code: "",
        name: "",
        email: "",
        phone: "",
        address: "",
        city: "",
        state: "",
        country: "",
        postal_code: "",
        tier_id: "",
      });
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to create customer.");
    } finally {
      setCreateLoading(false);
    }
  };

  // Update Customer Submit
  const handleUpdateCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCustomer) return;

    try {
      setEditLoading(true);
      await customersApi.update(editingCustomer.id, {
        name: editingCustomer.name.trim(),
        email: editingCustomer.email || undefined,
        phone: editingCustomer.phone || undefined,
        address: editingCustomer.address || undefined,
        city: editingCustomer.city || undefined,
        state: editingCustomer.state || undefined,
        country: editingCustomer.country || undefined,
        postal_code: editingCustomer.postal_code || undefined,
        tier_id: editingCustomer.tier_id || null,
        is_active: editingCustomer.is_active,
      });
      toast.success(`Customer "${editingCustomer.name}" updated successfully.`);
      setEditingCustomer(null);
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to update customer.");
    } finally {
      setEditLoading(false);
    }
  };

  // Delete Customer Submit
  const handleDeleteCustomer = async () => {
    if (!deletingCustomer) return;

    try {
      setDeleteLoading(true);
      await customersApi.delete(deletingCustomer.id, true);
      toast.success(`Customer "${deletingCustomer.name}" deactivated.`);
      setDeletingCustomer(null);
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to delete customer.");
    } finally {
      setDeleteLoading(false);
    }
  };

  // Tier styling helper
  const renderTierBadge = (tier?: CustomerTier | null) => {
    if (!tier) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600">
          Standard
        </span>
      );
    }
    if (tier.code.includes("GOLD")) {
      return (
        <Badge variant="warning" className="gap-1 font-medium bg-amber-50 text-amber-800 border-amber-200">
          <Award className="h-3 w-3" />
          {tier.name} ({tier.discount_limit}%)
        </Badge>
      );
    }
    if (tier.code.includes("SILVER")) {
      return (
        <Badge variant="secondary" className="gap-1 font-medium bg-slate-100 text-slate-800 border-slate-300">
          <Award className="h-3 w-3" />
          {tier.name} ({tier.discount_limit}%)
        </Badge>
      );
    }
    return (
      <Badge variant="primary" className="gap-1 font-medium bg-orange-50 text-orange-800 border-orange-200">
        <Award className="h-3 w-3" />
        {tier.name} ({tier.discount_limit}%)
      </Badge>
    );
  };

  // Customer Directory Table Columns
  const columns: ColumnDef<Customer>[] = [
    {
      id: "customer_code",
      header: "Code",
      accessorKey: "customer_code",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-semibold text-slate-800 bg-slate-100 px-2 py-1 rounded">
          {row.customer_code}
        </span>
      ),
    },
    {
      id: "name",
      header: "Customer Name",
      accessorKey: "name",
      sortable: true,
      cell: (row) => (
        <div>
          <Link
            href={`/customers/${row.id}`}
            className="font-semibold text-primary hover:underline inline-flex items-center gap-1"
          >
            <span>{row.name}</span>
            <ExternalLink className="h-3 w-3 opacity-60" />
          </Link>
          <div className="text-xs text-muted mt-0.5">
            {[row.city, row.country].filter(Boolean).join(", ") || "No location set"}
          </div>
        </div>
      ),
    },
    {
      id: "contact",
      header: "Contact",
      cell: (row) => (
        <div className="text-xs space-y-1">
          {row.email ? (
            <div className="flex items-center gap-1.5 text-slate-700">
              <Mail className="h-3.5 w-3.5 text-slate-400 shrink-0" />
              <span className="truncate max-w-[160px]">{row.email}</span>
            </div>
          ) : (
            <span className="text-slate-400 italic">No email</span>
          )}
          {row.phone && (
            <div className="flex items-center gap-1.5 text-slate-600">
              <Phone className="h-3.5 w-3.5 text-slate-400 shrink-0" />
              <span>{row.phone}</span>
            </div>
          )}
        </div>
      ),
    },
    {
      id: "tier",
      header: "Discount Tier",
      cell: (row) => renderTierBadge(row.tier),
    },
    {
      id: "status",
      header: "Status",
      accessorKey: "is_active",
      sortable: true,
      cell: (row) =>
        row.is_active ? (
          <Badge variant="success">Active</Badge>
        ) : (
          <Badge variant="outline" className="text-slate-500 border-slate-300">
            Inactive
          </Badge>
        ),
    },
    {
      id: "actions",
      header: "Actions",
      align: "right",
      cell: (row) => (
        <div className="flex items-center justify-end gap-1.5">
          <Link href={`/customers/${row.id}`}>
            <Button variant="ghost" size="sm" className="h-8 px-2" title="View Profile">
              <ExternalLink className="h-4 w-4" />
            </Button>
          </Link>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2 text-slate-600 hover:text-foreground"
            onClick={() => setEditingCustomer(row)}
            title="Edit Customer"
          >
            <Edit2 className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2 text-rose-600 hover:bg-rose-50"
            onClick={() => setDeletingCustomer(row)}
            title="Deactivate Customer"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  // Segmentation Table Columns (Phase 069)
  const segmentationColumns: ColumnDef<CustomerSegmentProfile>[] = [
    {
      id: "customer_code",
      header: "Code",
      accessorKey: "customer_code",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-semibold text-slate-800 bg-slate-100 px-2 py-1 rounded">
          {row.customer_code}
        </span>
      ),
    },
    {
      id: "customer_name",
      header: "Customer",
      accessorKey: "customer_name",
      sortable: true,
      cell: (row) => (
        <Link
          href={`/customers/${row.customer_id}`}
          className="font-semibold text-primary hover:underline inline-flex items-center gap-1"
        >
          <span>{row.customer_name}</span>
          <ExternalLink className="h-3 w-3 opacity-60" />
        </Link>
      ),
    },
    {
      id: "segment",
      header: "Assigned Segment",
      accessorKey: "segment",
      cell: (row) => (
        <Badge variant={row.badge_variant} className="font-semibold text-xs">
          {row.segment_label}
        </Badge>
      ),
    },
    {
      id: "rationale",
      header: "Classification Rationale",
      cell: (row) => <span className="text-xs text-muted leading-relaxed">{row.rationale}</span>,
    },
    {
      id: "ltv_amount",
      header: "Calculated LTV",
      accessorKey: "ltv_amount",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-semibold text-slate-900">
          ${Number(row.ltv_amount).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      id: "risk_level",
      header: "Risk Status",
      cell: (row) => (
        <Badge
          variant={
            row.risk_level === "HIGH"
              ? "destructive"
              : row.risk_level === "MEDIUM"
              ? "warning"
              : "success"
          }
        >
          {row.risk_level}
        </Badge>
      ),
    },
  ];

  // Derived KPI values from dashboard response or fallbacks
  const kpis = dashboardData?.kpis || {
    total_customers: customers.length,
    active_customers: customers.filter((c) => c.is_active).length,
    portfolio_ltv: 0,
    high_risk_customers_count: 0,
    active_deals_count: 0,
    settled_revenue: 0,
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Customer Intelligence Dashboard
            </h1>
            <Badge variant="primary" className="font-mono text-[11px]">
              G14 (Phases 066–070)
            </Badge>
          </div>
          <p className="text-sm text-muted mt-1">
            Portfolio analytics, multi-field search, composable filtering, explainable segmentation, and customer records.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="gap-1.5"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsCreateOpen(true)}
            className="gap-1.5"
          >
            <Plus className="h-4 w-4" />
            <span>Add Customer</span>
          </Button>
        </div>
      </div>

      {/* KPI Overview Cards (Phase 070) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-card border-border shadow-xs">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-blue-50 text-blue-600">
              <Users className="h-5 w-5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-muted uppercase tracking-wider">
                Total Accounts
              </div>
              <div className="text-2xl font-bold text-foreground mt-0.5">
                {kpis.total_customers}
              </div>
              <div className="text-[11px] text-muted">
                {kpis.active_customers} active accounts ({Math.round(
                  kpis.total_customers > 0 ? (kpis.active_customers / kpis.total_customers) * 100 : 0
                )}%)
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-card border-border shadow-xs">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-600">
              <TrendingUp className="h-5 w-5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-muted uppercase tracking-wider">
                Portfolio LTV
              </div>
              <div className="text-2xl font-bold text-emerald-700 mt-0.5">
                ${Number(kpis.portfolio_ltv).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className="text-[11px] text-muted">
                Cumulative historical revenue
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-card border-border shadow-xs">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-rose-50 text-rose-600">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-muted uppercase tracking-wider">
                High-Risk Accounts
              </div>
              <div className="text-2xl font-bold text-rose-600 mt-0.5">
                {kpis.high_risk_customers_count}
              </div>
              <div className="text-[11px] text-muted">
                Require credit or follow-up review
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-card border-border shadow-xs">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-amber-50 text-amber-600">
              <Award className="h-5 w-5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-muted uppercase tracking-wider">
                Active Deals & Revenue
              </div>
              <div className="text-2xl font-bold text-foreground mt-0.5">
                ${Number(kpis.settled_revenue).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className="text-[11px] text-muted">
                {kpis.active_deals_count} deals in pipeline
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Interactive Visualizations (Phase 070: Donut & Bar Charts via G11) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DonutChart
          title="Customer Tier Distribution"
          description="Breakdown of customer portfolio across discount tier bands."
          data={(dashboardData?.tier_chart_data || []).map((d) => ({
            label: d.label,
            value: d.value,
            color: d.color || undefined,
          }))}
          isLoading={isLoading}
          error={error}
          onRetry={loadData}
          emptyTitle="No Tier Distribution Data"
          emptyDescription="Assign customers to discount tiers to populate this visualization."
        />

        <BarChart
          title="Portfolio Segmentation Distribution"
          description="Customer count by deterministic behavioral & value segments."
          data={(dashboardData?.segment_chart_data || []).map((d) => ({
            label: d.label,
            value: d.value,
            color: d.color || undefined,
          }))}
          isLoading={isLoading}
          error={error}
          onRetry={loadData}
          emptyTitle="No Segmentation Data"
          emptyDescription="Customer activity data is required to calculate segmentation."
        />
      </div>

      {/* Multi-Field Search & Filter Controls (Phases 067 & 068) */}
      <Card className="p-4 bg-card border-border shadow-xs">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
          {/* Phase 067: Multi-Field Search Input */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              type="text"
              placeholder="Search by code, name, email, or phone..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 h-9 text-xs"
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => setSearchTerm("")}
                className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Phase 068: Composable Filters */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Status Filter */}
            <div className="flex items-center gap-1.5 text-xs text-muted">
              <span>Status:</span>
              <div className="flex items-center rounded-lg border border-border bg-slate-50 p-0.5">
                {(["all", "active", "inactive"] as const).map((filter) => (
                  <button
                    key={filter}
                    type="button"
                    onClick={() => setStatusFilter(filter)}
                    className={`px-2.5 py-1 rounded-md capitalize text-xs font-medium transition-colors ${
                      statusFilter === filter
                        ? "bg-white text-primary shadow-xs font-semibold"
                        : "text-slate-600 hover:text-foreground"
                    }`}
                  >
                    {filter}
                  </button>
                ))}
              </div>
            </div>

            {/* Tier Filter */}
            <div className="flex items-center gap-1.5 text-xs text-muted">
              <span>Tier:</span>
              <Select
                value={tierFilter}
                onChange={(e) => setTierFilter(e.target.value)}
                className="h-8 text-xs py-1 w-36"
              >
                <option value="all">All Tiers</option>
                {tiers.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </Select>
            </div>

            {/* Reset Filters Button */}
            {hasActiveFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleResetFilters}
                className="h-8 px-2 text-xs text-rose-600 hover:bg-rose-50 gap-1"
              >
                <X className="h-3.5 w-3.5" />
                <span>Reset</span>
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* Tabs for Customer Directory vs Customer Segmentation */}
      <div className="border-b border-border">
        <div className="flex items-center gap-6">
          <button
            type="button"
            onClick={() => setActiveTab("directory")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === "directory"
                ? "border-primary text-primary"
                : "border-transparent text-muted hover:text-foreground"
            }`}
          >
            <Users className="h-4 w-4" />
            <span>Customer Directory ({customers.length})</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("segmentation")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === "segmentation"
                ? "border-primary text-primary"
                : "border-transparent text-muted hover:text-foreground"
            }`}
          >
            <Layers className="h-4 w-4" />
            <span>Behavioral Segmentation (Phase 069)</span>
          </button>
        </div>
      </div>

      {/* View Content based on activeTab */}
      {activeTab === "directory" ? (
        <DataTable
          columns={columns}
          data={customers}
          keyExtractor={(item) => item.id}
          isLoading={isLoading}
          error={error}
          onRetry={loadData}
          emptyTitle="No customers match your criteria"
          emptyDescription={
            hasActiveFilters
              ? "Try adjusting or clearing your search term and filters to see more results."
              : "Start by registering a new customer account within your organization."
          }
          emptyAction={
            hasActiveFilters ? (
              <Button size="sm" variant="outline" onClick={handleResetFilters} className="mt-2">
                Clear Filters
              </Button>
            ) : (
              <Button size="sm" onClick={() => setIsCreateOpen(true)} className="gap-1.5 mt-2">
                <Plus className="h-4 w-4" />
                <span>Create First Customer</span>
              </Button>
            )
          }
        />
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-muted">
            <span>
              Categorized according to deterministic LTV, risk profile, and discount sensitivity metrics.
            </span>
            <span>{segmentationProfiles.length} Total Evaluated Accounts</span>
          </div>

          <DataTable
            columns={segmentationColumns}
            data={segmentationProfiles}
            keyExtractor={(item) => item.customer_id}
            isLoading={isLoading}
            error={error}
            onRetry={loadData}
            emptyTitle="No Segmentation Profiles"
            emptyDescription="Review individual customer profiles to inspect their real-time segment classification."
          />
        </div>
      )}

      {/* Add Customer Modal (Phase 056 & 052) */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Add New Customer"
        description="Create a client record scoped to your organization."
        size="lg"
      >
        <form onSubmit={handleCreateCustomer} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormItem>
              <FormLabel required>Customer Code</FormLabel>
              <Input
                placeholder="e.g. CUST-ACME-01"
                value={newCustomer.customer_code}
                onChange={(e) =>
                  setNewCustomer({ ...newCustomer, customer_code: e.target.value })
                }
                required
              />
            </FormItem>

            <FormItem>
              <FormLabel required>Customer Name</FormLabel>
              <Input
                placeholder="Acme Enterprises LLC"
                value={newCustomer.name}
                onChange={(e) => setNewCustomer({ ...newCustomer, name: e.target.value })}
                required
              />
            </FormItem>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormItem>
              <FormLabel>Email Address</FormLabel>
              <Input
                type="email"
                placeholder="procurement@acme.example"
                value={newCustomer.email || ""}
                onChange={(e) => setNewCustomer({ ...newCustomer, email: e.target.value })}
              />
            </FormItem>

            <FormItem>
              <FormLabel>Phone Number</FormLabel>
              <Input
                placeholder="+1-555-0199"
                value={newCustomer.phone || ""}
                onChange={(e) => setNewCustomer({ ...newCustomer, phone: e.target.value })}
              />
            </FormItem>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormItem>
              <FormLabel>Discount Tier (Phase 058)</FormLabel>
              <Select
                value={newCustomer.tier_id || ""}
                onChange={(e) =>
                  setNewCustomer({
                    ...newCustomer,
                    tier_id: e.target.value || null,
                  })
                }
              >
                <option value="">No Tier (Standard Pricing)</option>
                {tiers.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} (Max {t.discount_limit}% Discount)
                  </option>
                ))}
              </Select>
            </FormItem>

            <FormItem>
              <FormLabel>Physical Address</FormLabel>
              <Input
                placeholder="100 Enterprise Way"
                value={newCustomer.address || ""}
                onChange={(e) => setNewCustomer({ ...newCustomer, address: e.target.value })}
              />
            </FormItem>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <FormItem>
              <FormLabel>City</FormLabel>
              <Input
                placeholder="San Francisco"
                value={newCustomer.city || ""}
                onChange={(e) => setNewCustomer({ ...newCustomer, city: e.target.value })}
              />
            </FormItem>
            <FormItem>
              <FormLabel>State / Region</FormLabel>
              <Input
                placeholder="CA"
                value={newCustomer.state || ""}
                onChange={(e) => setNewCustomer({ ...newCustomer, state: e.target.value })}
              />
            </FormItem>
            <FormItem>
              <FormLabel>Country</FormLabel>
              <Input
                placeholder="United States"
                value={newCustomer.country || ""}
                onChange={(e) => setNewCustomer({ ...newCustomer, country: e.target.value })}
              />
            </FormItem>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsCreateOpen(false)}
              disabled={createLoading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={createLoading}>
              Create Customer
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Customer Modal */}
      <Modal
        isOpen={Boolean(editingCustomer)}
        onClose={() => setEditingCustomer(null)}
        title="Edit Customer"
        description="Update contact and account parameters."
        size="lg"
      >
        {editingCustomer && (
          <form onSubmit={handleUpdateCustomer} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormItem>
                <FormLabel>Customer Code</FormLabel>
                <Input value={editingCustomer.customer_code} disabled className="bg-slate-50" />
              </FormItem>

              <FormItem>
                <FormLabel required>Customer Name</FormLabel>
                <Input
                  value={editingCustomer.name}
                  onChange={(e) =>
                    setEditingCustomer({ ...editingCustomer, name: e.target.value })
                  }
                  required
                />
              </FormItem>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormItem>
                <FormLabel>Email Address</FormLabel>
                <Input
                  type="email"
                  value={editingCustomer.email || ""}
                  onChange={(e) =>
                    setEditingCustomer({ ...editingCustomer, email: e.target.value })
                  }
                />
              </FormItem>

              <FormItem>
                <FormLabel>Phone Number</FormLabel>
                <Input
                  value={editingCustomer.phone || ""}
                  onChange={(e) =>
                    setEditingCustomer({ ...editingCustomer, phone: e.target.value })
                  }
                />
              </FormItem>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormItem>
                <FormLabel>Discount Tier (Phase 058)</FormLabel>
                <Select
                  value={editingCustomer.tier_id || ""}
                  onChange={(e) =>
                    setEditingCustomer({
                      ...editingCustomer,
                      tier_id: e.target.value || null,
                    })
                  }
                >
                  <option value="">No Tier (Standard Pricing)</option>
                  {tiers.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name} (Max {t.discount_limit}% Discount)
                    </option>
                  ))}
                </Select>
              </FormItem>

              <FormItem>
                <FormLabel>Account Status</FormLabel>
                <Select
                  value={editingCustomer.is_active ? "true" : "false"}
                  onChange={(e) =>
                    setEditingCustomer({
                      ...editingCustomer,
                      is_active: e.target.value === "true",
                    })
                  }
                >
                  <option value="true">Active Account</option>
                  <option value="false">Inactive / Suspended</option>
                </Select>
              </FormItem>
            </div>

            <FormItem>
              <FormLabel>Physical Address</FormLabel>
              <Input
                value={editingCustomer.address || ""}
                onChange={(e) =>
                  setEditingCustomer({ ...editingCustomer, address: e.target.value })
                }
              />
            </FormItem>

            <div className="grid grid-cols-3 gap-3">
              <FormItem>
                <FormLabel>City</FormLabel>
                <Input
                  value={editingCustomer.city || ""}
                  onChange={(e) =>
                    setEditingCustomer({ ...editingCustomer, city: e.target.value })
                  }
                />
              </FormItem>
              <FormItem>
                <FormLabel>State / Region</FormLabel>
                <Input
                  value={editingCustomer.state || ""}
                  onChange={(e) =>
                    setEditingCustomer({ ...editingCustomer, state: e.target.value })
                  }
                />
              </FormItem>
              <FormItem>
                <FormLabel>Country</FormLabel>
                <Input
                  value={editingCustomer.country || ""}
                  onChange={(e) =>
                    setEditingCustomer({ ...editingCustomer, country: e.target.value })
                  }
                />
              </FormItem>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-border">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setEditingCustomer(null)}
                disabled={editLoading}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" isLoading={editLoading}>
                Save Changes
              </Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={Boolean(deletingCustomer)}
        onClose={() => setDeletingCustomer(null)}
        title="Deactivate Customer Account"
        description={`Are you sure you want to deactivate "${deletingCustomer?.name}" (${deletingCustomer?.customer_code})? This will mark the account as inactive while preserving transaction history.`}
        variant="destructive"
        confirmLabel="Deactivate Customer"
        onConfirm={handleDeleteCustomer}
        isLoading={deleteLoading}
      />
    </div>
  );
}
