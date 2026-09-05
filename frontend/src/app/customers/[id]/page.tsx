"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  Building2,
  Phone,
  Mail,
  MapPin,
  Calendar,
  Clock,
  ShieldCheck,
  Award,
  ShoppingBag,
  TrendingUp,
  Plus,
  Edit,
  DollarSign,
  FileText,
  AlertCircle,
} from "lucide-react";

import { useToast } from "@/context/ToastContext";
import { customersApi, customerTiersApi } from "@/lib/api";
import {
  Customer,
  CustomerTier,
  CustomerPurchaseHistory,
  CustomerDealHistory,
  PurchaseHistoryCreateInput,
  DealHistoryCreateInput,
} from "@/types/customer";
import { DataTable, ColumnDef } from "@/components/ui/data-table";
import { Modal } from "@/components/ui/modal";
import { FormItem, FormLabel } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { LoadingState } from "@/components/ui/loading-state";
import { ErrorState } from "@/components/ui/error-state";

export default function CustomerProfilePage() {
  const params = useParams();
  const customerId = params?.id as string;
  const toast = useToast();

  const [customer, setCustomer] = useState<Customer | null>(null);
  const [tiers, setTiers] = useState<CustomerTier[]>([]);
  const [purchases, setPurchases] = useState<CustomerPurchaseHistory[]>([]);
  const [deals, setDeals] = useState<CustomerDealHistory[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Active tab state
  const [activeTab, setActiveTab] = useState<"purchases" | "deals">("purchases");

  // Tier Management Modal (Phase 058)
  const [isTierModalOpen, setIsTierModalOpen] = useState<boolean>(false);
  const [selectedTierId, setSelectedTierId] = useState<string>("");
  const [tierLoading, setTierLoading] = useState<boolean>(false);

  // Add Purchase Modal (Phase 059)
  const [isPurchaseModalOpen, setIsPurchaseModalOpen] = useState<boolean>(false);
  const [purchaseLoading, setPurchaseLoading] = useState<boolean>(false);
  const [newPurchase, setNewPurchase] = useState<PurchaseHistoryCreateInput>({
    order_number: "",
    total_amount: "",
    status: "COMPLETED",
    item_count: 1,
    notes: "",
  });

  // Add Deal Modal (Phase 060)
  const [isDealModalOpen, setIsDealModalOpen] = useState<boolean>(false);
  const [dealLoading, setDealLoading] = useState<boolean>(false);
  const [newDeal, setNewDeal] = useState<DealHistoryCreateInput>({
    deal_code: "",
    title: "",
    deal_value: "",
    status: "WON",
    sales_rep_name: "",
    notes: "",
  });

  const loadCustomerDetails = useCallback(async () => {
    if (!customerId) return;
    try {
      setError(null);
      const [custData, tierData, purchaseData, dealData] = await Promise.all([
        customersApi.getById(customerId),
        customerTiersApi.getAll(),
        customersApi.getPurchaseHistory(customerId),
        customersApi.getDealHistory(customerId),
      ]);
      setCustomer(custData);
      setTiers(tierData);
      setPurchases(purchaseData);
      setDeals(dealData);
      setSelectedTierId(custData.tier_id || "");
    } catch (err: any) {
      setError(err.message || "Failed to load customer profile.");
    } finally {
      setIsLoading(false);
    }
  }, [customerId]);

  useEffect(() => {
    loadCustomerDetails();
  }, [loadCustomerDetails]);

  // Handle Tier Update (Phase 058)
  const handleUpdateTier = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customer) return;

    try {
      setTierLoading(true);
      const updated = await customersApi.updateTier(customer.id, selectedTierId || null);
      setCustomer(updated);
      toast.success("Customer discount tier updated successfully.");
      setIsTierModalOpen(false);
    } catch (err: any) {
      toast.error(err.message || "Failed to update discount tier.");
    } finally {
      setTierLoading(false);
    }
  };

  // Handle Add Purchase (Phase 059)
  const handleCreatePurchase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customer) return;
    if (!newPurchase.order_number.trim() || !newPurchase.total_amount) {
      toast.error("Order number and total amount are required.");
      return;
    }

    try {
      setPurchaseLoading(true);
      await customersApi.createPurchaseHistory(customer.id, {
        ...newPurchase,
        order_number: newPurchase.order_number.trim(),
        total_amount: Number(newPurchase.total_amount),
        item_count: Number(newPurchase.item_count) || 1,
      });
      toast.success("Purchase transaction recorded.");
      setIsPurchaseModalOpen(false);
      setNewPurchase({
        order_number: "",
        total_amount: "",
        status: "COMPLETED",
        item_count: 1,
        notes: "",
      });
      const updatedPurchases = await customersApi.getPurchaseHistory(customer.id);
      setPurchases(updatedPurchases);
    } catch (err: any) {
      toast.error(err.message || "Failed to record purchase.");
    } finally {
      setPurchaseLoading(false);
    }
  };

  // Handle Add Deal (Phase 060)
  const handleCreateDeal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customer) return;
    if (!newDeal.deal_code.trim() || !newDeal.title.trim() || !newDeal.deal_value) {
      toast.error("Deal code, title, and value are required.");
      return;
    }

    try {
      setDealLoading(true);
      await customersApi.createDealHistory(customer.id, {
        ...newDeal,
        deal_code: newDeal.deal_code.trim(),
        title: newDeal.title.trim(),
        deal_value: Number(newDeal.deal_value),
      });
      toast.success("Deal record added.");
      setIsDealModalOpen(false);
      setNewDeal({
        deal_code: "",
        title: "",
        deal_value: "",
        status: "WON",
        sales_rep_name: "",
        notes: "",
      });
      const updatedDeals = await customersApi.getDealHistory(customer.id);
      setDeals(updatedDeals);
    } catch (err: any) {
      toast.error(err.message || "Failed to add deal record.");
    } finally {
      setDealLoading(false);
    }
  };

  // Purchase Columns (Phase 059)
  const purchaseColumns: ColumnDef<CustomerPurchaseHistory>[] = [
    {
      id: "order_number",
      header: "Order #",
      accessorKey: "order_number",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-semibold text-slate-800 bg-slate-100 px-2 py-1 rounded">
          {row.order_number}
        </span>
      ),
    },
    {
      id: "purchase_date",
      header: "Purchase Date",
      sortable: true,
      cell: (row) => (
        <span className="text-xs text-slate-700">
          {new Date(row.purchase_date).toLocaleDateString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
          })}
        </span>
      ),
    },
    {
      id: "total_amount",
      header: "Total Value",
      sortable: true,
      cell: (row) => (
        <span className="font-semibold text-sm text-foreground">
          ${Number(row.total_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      id: "items",
      header: "Items",
      accessorKey: "item_count",
      align: "center",
      cell: (row) => (
        <span className="text-xs text-muted font-medium">{row.item_count} items</span>
      ),
    },
    {
      id: "status",
      header: "Status",
      cell: (row) => (
        <Badge
          variant={
            row.status === "COMPLETED"
              ? "success"
              : row.status === "PROCESSING"
              ? "primary"
              : "outline"
          }
        >
          {row.status}
        </Badge>
      ),
    },
    {
      id: "notes",
      header: "Notes",
      cell: (row) => (
        <span className="text-xs text-muted truncate max-w-[200px] block">
          {row.notes || "—"}
        </span>
      ),
    },
  ];

  // Deal Columns (Phase 060)
  const dealColumns: ColumnDef<CustomerDealHistory>[] = [
    {
      id: "deal_code",
      header: "Deal Code",
      accessorKey: "deal_code",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-semibold text-slate-800 bg-slate-100 px-2 py-1 rounded">
          {row.deal_code}
        </span>
      ),
    },
    {
      id: "title",
      header: "Deal Title",
      accessorKey: "title",
      sortable: true,
      cell: (row) => (
        <div>
          <div className="font-semibold text-xs text-foreground">{row.title}</div>
          {row.sales_rep_name && (
            <div className="text-[11px] text-muted">Rep: {row.sales_rep_name}</div>
          )}
        </div>
      ),
    },
    {
      id: "deal_value",
      header: "Contract Value",
      sortable: true,
      cell: (row) => (
        <span className="font-semibold text-sm text-emerald-700">
          ${Number(row.deal_value).toLocaleString(undefined, { minimumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      id: "status",
      header: "Stage",
      cell: (row) => (
        <Badge
          variant={
            row.status === "WON"
              ? "success"
              : row.status === "NEGOTIATING"
              ? "warning"
              : row.status === "PROPOSED"
              ? "primary"
              : "secondary"
          }
        >
          {row.status}
        </Badge>
      ),
    },
    {
      id: "created_at",
      header: "Date Logged",
      cell: (row) => (
        <span className="text-xs text-muted">
          {new Date(row.created_at).toLocaleDateString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
          })}
        </span>
      ),
    },
    {
      id: "notes",
      header: "Summary",
      cell: (row) => (
        <span className="text-xs text-muted truncate max-w-[200px] block">
          {row.notes || "—"}
        </span>
      ),
    },
  ];

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto py-12">
        <LoadingState message="Loading customer account profile..." />
      </div>
    );
  }

  if (error || !customer) {
    return (
      <div className="max-w-7xl mx-auto py-8">
        <ErrorState
          title="Customer Profile Error"
          message={error || "Customer record could not be found."}
          onRetry={loadCustomerDetails}
        />
        <div className="mt-4">
          <Link href="/customers">
            <Button variant="outline" size="sm" className="gap-1.5">
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Customers</span>
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  const totalPurchasesAmount = purchases.reduce(
    (acc, p) => acc + Number(p.total_amount),
    0
  );
  const totalDealsAmount = deals.reduce((acc, d) => acc + Number(d.deal_value), 0);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Breadcrumb & Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link href="/customers">
            <Button variant="outline" size="sm" className="h-9 w-9 p-0" title="Back to Customers">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                {customer.name}
              </h1>
              <span className="font-mono text-xs font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                {customer.customer_code}
              </span>
              {customer.is_active ? (
                <Badge variant="success">Active Account</Badge>
              ) : (
                <Badge variant="outline" className="text-slate-500 border-slate-300">
                  Inactive
                </Badge>
              )}
            </div>
            <p className="text-xs text-muted mt-0.5">
              Customer ID: <span className="font-mono">{customer.id}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsTierModalOpen(true)}
            className="gap-1.5"
          >
            <Award className="h-4 w-4 text-amber-600" />
            <span>Manage Tier</span>
          </Button>
        </div>
      </div>

      {/* Main Grid: Profile Info & Tier (Left) vs History Tabs (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Phase 057 Profile Details & Phase 058 Tier */}
        <div className="space-y-6">
          {/* Phase 057: Customer Profile Card */}
          <Card className="border-border shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                <Building2 className="h-4 w-4 text-primary" />
                <span>Account Profile</span>
              </CardTitle>
              <CardDescription className="text-xs text-muted">
                Contact and location information
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="py-2 border-b border-border/50">
                <div className="text-muted font-medium">Email Address</div>
                <div className="text-slate-800 font-medium flex items-center gap-1.5 mt-0.5">
                  <Mail className="h-3.5 w-3.5 text-slate-400" />
                  <span>{customer.email || "No email registered"}</span>
                </div>
              </div>

              <div className="py-2 border-b border-border/50">
                <div className="text-muted font-medium">Telephone</div>
                <div className="text-slate-800 font-medium flex items-center gap-1.5 mt-0.5">
                  <Phone className="h-3.5 w-3.5 text-slate-400" />
                  <span>{customer.phone || "No phone registered"}</span>
                </div>
              </div>

              <div className="py-2 border-b border-border/50">
                <div className="text-muted font-medium">Physical Address</div>
                <div className="text-slate-800 font-medium flex items-start gap-1.5 mt-0.5">
                  <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0 mt-0.5" />
                  <span>
                    {[
                      customer.address,
                      customer.city,
                      customer.state,
                      customer.postal_code,
                      customer.country,
                    ]
                      .filter(Boolean)
                      .join(", ") || "No address specified"}
                  </span>
                </div>
              </div>

              <div className="py-2 border-b border-border/50">
                <div className="text-muted font-medium">Account Created</div>
                <div className="text-slate-700 flex items-center gap-1.5 mt-0.5">
                  <Calendar className="h-3.5 w-3.5 text-slate-400" />
                  <span>{new Date(customer.created_at).toLocaleString()}</span>
                </div>
              </div>

              <div className="py-2">
                <div className="text-muted font-medium">Last Record Update</div>
                <div className="text-slate-700 flex items-center gap-1.5 mt-0.5">
                  <Clock className="h-3.5 w-3.5 text-slate-400" />
                  <span>{new Date(customer.updated_at).toLocaleString()}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Phase 058: Customer Tier Management Card */}
          <Card className="border-border shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Award className="h-4 w-4 text-amber-600" />
                  <span>Discount Tier</span>
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-xs"
                  onClick={() => setIsTierModalOpen(true)}
                >
                  Change
                </Button>
              </div>
              <CardDescription className="text-xs text-muted">
                Discount authorization ceiling for quotation governance
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              {customer.tier ? (
                <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-amber-900">
                      {customer.tier.name}
                    </span>
                    <Badge variant="warning" className="font-mono">
                      {customer.tier.code}
                    </Badge>
                  </div>
                  <p className="text-amber-800 text-[11px] leading-relaxed">
                    {customer.tier.description || "Partner organization with standard baseline governance limits."}
                  </p>
                  <div className="pt-2 border-t border-amber-200/60 flex items-center justify-between text-amber-950 font-medium">
                    <span>Discount Limit:</span>
                    <span className="font-bold text-sm">{customer.tier.discount_limit}%</span>
                  </div>
                </div>
              ) : (
                <div className="rounded-xl border border-border bg-slate-50 p-4 text-center">
                  <p className="text-muted text-xs">No discount tier assigned.</p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Standard pricing rules apply with 0% automated baseline allowance.
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-3 text-xs gap-1.5"
                    onClick={() => setIsTierModalOpen(true)}
                  >
                    <Award className="h-3.5 w-3.5 text-amber-600" />
                    <span>Assign Customer Tier</span>
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: History Tabs (Phases 059 & 060) */}
        <div className="lg:col-span-2 space-y-4">
          {/* Header Navigation Pills */}
          <div className="flex items-center justify-between border-b border-border pb-2">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setActiveTab("purchases")}
                className={`flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                  activeTab === "purchases"
                    ? "bg-primary text-white shadow-xs"
                    : "text-slate-600 hover:bg-slate-100 hover:text-foreground"
                }`}
              >
                <ShoppingBag className="h-3.5 w-3.5" />
                <span>Purchase History (Phase 059)</span>
                <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-white/20">
                  {purchases.length}
                </span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("deals")}
                className={`flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                  activeTab === "deals"
                    ? "bg-primary text-white shadow-xs"
                    : "text-slate-600 hover:bg-slate-100 hover:text-foreground"
                }`}
              >
                <TrendingUp className="h-3.5 w-3.5" />
                <span>Deal History (Phase 060)</span>
                <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-white/20">
                  {deals.length}
                </span>
              </button>
            </div>

            <div>
              {activeTab === "purchases" ? (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setIsPurchaseModalOpen(true)}
                  className="gap-1.5 text-xs"
                >
                  <Plus className="h-3.5 w-3.5" />
                  <span>Record Purchase</span>
                </Button>
              ) : (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setIsDealModalOpen(true)}
                  className="gap-1.5 text-xs"
                >
                  <Plus className="h-3.5 w-3.5" />
                  <span>Log Deal Event</span>
                </Button>
              )}
            </div>
          </div>

          {/* Tab Content */}
          {activeTab === "purchases" ? (
            <div className="space-y-4">
              {/* Purchase Summary KPI */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl border border-border bg-card">
                  <div className="text-[11px] font-medium text-muted uppercase">Total Purchases</div>
                  <div className="text-xl font-bold text-foreground mt-0.5">
                    ${totalPurchasesAmount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </div>
                </div>
                <div className="p-3 rounded-xl border border-border bg-card">
                  <div className="text-[11px] font-medium text-muted uppercase">Orders Completed</div>
                  <div className="text-xl font-bold text-foreground mt-0.5">{purchases.length}</div>
                </div>
              </div>

              {/* Purchase History Data Table (Phase 059 & 054) */}
              <DataTable
                columns={purchaseColumns}
                data={purchases}
                keyExtractor={(item) => item.id}
                emptyTitle="No purchase records"
                emptyDescription="There are no past orders or transactions logged for this customer account."
                emptyAction={
                  <Button
                    size="sm"
                    onClick={() => setIsPurchaseModalOpen(true)}
                    className="gap-1.5 mt-2"
                  >
                    <Plus className="h-4 w-4" />
                    <span>Record First Purchase</span>
                  </Button>
                }
              />
            </div>
          ) : (
            <div className="space-y-4">
              {/* Deals Summary KPI */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl border border-border bg-card">
                  <div className="text-[11px] font-medium text-muted uppercase">Total Deal Value</div>
                  <div className="text-xl font-bold text-emerald-700 mt-0.5">
                    ${totalDealsAmount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </div>
                </div>
                <div className="p-3 rounded-xl border border-border bg-card">
                  <div className="text-[11px] font-medium text-muted uppercase">Deals Tracked</div>
                  <div className="text-xl font-bold text-foreground mt-0.5">{deals.length}</div>
                </div>
              </div>

              {/* Deal History Data Table (Phase 060 & 054) */}
              <DataTable
                columns={dealColumns}
                data={deals}
                keyExtractor={(item) => item.id}
                emptyTitle="No deal history records"
                emptyDescription="No past deals or sales opportunities have been recorded for this client."
                emptyAction={
                  <Button
                    size="sm"
                    onClick={() => setIsDealModalOpen(true)}
                    className="gap-1.5 mt-2"
                  >
                    <Plus className="h-4 w-4" />
                    <span>Log First Deal Event</span>
                  </Button>
                }
              />
            </div>
          )}
        </div>
      </div>

      {/* Tier Reassignment Modal (Phase 058 & 052) */}
      <Modal
        isOpen={isTierModalOpen}
        onClose={() => setIsTierModalOpen(false)}
        title="Manage Customer Tier"
        description="Select a discount tier participating in quotation governance."
        size="md"
      >
        <form onSubmit={handleUpdateTier} className="space-y-4">
          <FormItem>
            <FormLabel>Customer Tier</FormLabel>
            <Select
              value={selectedTierId}
              onChange={(e) => setSelectedTierId(e.target.value)}
            >
              <option value="">No Tier (Standard 0% Baseline)</option>
              {tiers.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.code}) &mdash; Up to {t.discount_limit}% Discount
                </option>
              ))}
            </Select>
          </FormItem>

          <div className="rounded-lg bg-blue-50/70 border border-blue-200 p-3 text-xs text-blue-900 leading-relaxed">
            <p className="font-semibold mb-0.5">Discount Ceiling Enforcement:</p>
            Customer tiers set the baseline automated approval threshold. Sales reps quoting
            discounts above this ceiling will trigger approval workflows in later phases.
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsTierModalOpen(false)}
              disabled={tierLoading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={tierLoading}>
              Save Tier Assignment
            </Button>
          </div>
        </form>
      </Modal>

      {/* Add Purchase Modal (Phase 059 & 052) */}
      <Modal
        isOpen={isPurchaseModalOpen}
        onClose={() => setIsPurchaseModalOpen(false)}
        title="Record Purchase History"
        description="Log an invoice or order transaction for this customer."
        size="md"
      >
        <form onSubmit={handleCreatePurchase} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <FormItem>
              <FormLabel required>Order Number</FormLabel>
              <Input
                placeholder="ORD-2026-001"
                value={newPurchase.order_number}
                onChange={(e) =>
                  setNewPurchase({ ...newPurchase, order_number: e.target.value })
                }
                required
              />
            </FormItem>

            <FormItem>
              <FormLabel required>Total Amount ($)</FormLabel>
              <Input
                type="number"
                step="0.01"
                placeholder="4999.00"
                value={String(newPurchase.total_amount)}
                onChange={(e) =>
                  setNewPurchase({ ...newPurchase, total_amount: e.target.value })
                }
                required
              />
            </FormItem>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <FormItem>
              <FormLabel>Item Count</FormLabel>
              <Input
                type="number"
                min="1"
                value={String(newPurchase.item_count)}
                onChange={(e) =>
                  setNewPurchase({ ...newPurchase, item_count: Number(e.target.value) })
                }
              />
            </FormItem>

            <FormItem>
              <FormLabel>Transaction Status</FormLabel>
              <Select
                value={newPurchase.status}
                onChange={(e) =>
                  setNewPurchase({ ...newPurchase, status: e.target.value })
                }
              >
                <option value="COMPLETED">COMPLETED</option>
                <option value="PROCESSING">PROCESSING</option>
                <option value="REFUNDED">REFUNDED</option>
              </Select>
            </FormItem>
          </div>

          <FormItem>
            <FormLabel>Transaction Notes</FormLabel>
            <Input
              placeholder="e.g. Hardware upgrade batch 1"
              value={newPurchase.notes || ""}
              onChange={(e) =>
                setNewPurchase({ ...newPurchase, notes: e.target.value })
              }
            />
          </FormItem>

          <div className="flex justify-end gap-2 pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsPurchaseModalOpen(false)}
              disabled={purchaseLoading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={purchaseLoading}>
              Record Purchase
            </Button>
          </div>
        </form>
      </Modal>

      {/* Add Deal Modal (Phase 060 & 052) */}
      <Modal
        isOpen={isDealModalOpen}
        onClose={() => setIsDealModalOpen(false)}
        title="Log Deal Record"
        description="Record a negotiated or closed sales deal for this customer."
        size="md"
      >
        <form onSubmit={handleCreateDeal} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <FormItem>
              <FormLabel required>Deal Code</FormLabel>
              <Input
                placeholder="DEAL-2026-01"
                value={newDeal.deal_code}
                onChange={(e) =>
                  setNewDeal({ ...newDeal, deal_code: e.target.value })
                }
                required
              />
            </FormItem>

            <FormItem>
              <FormLabel required>Deal Value ($)</FormLabel>
              <Input
                type="number"
                step="0.01"
                placeholder="50000.00"
                value={String(newDeal.deal_value)}
                onChange={(e) =>
                  setNewDeal({ ...newDeal, deal_value: e.target.value })
                }
                required
              />
            </FormItem>
          </div>

          <FormItem>
            <FormLabel required>Deal Title</FormLabel>
            <Input
              placeholder="Enterprise Server Infrastructure Expansion"
              value={newDeal.title}
              onChange={(e) => setNewDeal({ ...newDeal, title: e.target.value })}
              required
            />
          </FormItem>

          <div className="grid grid-cols-2 gap-3">
            <FormItem>
              <FormLabel>Deal Status</FormLabel>
              <Select
                value={newDeal.status}
                onChange={(e) => setNewDeal({ ...newDeal, status: e.target.value })}
              >
                <option value="WON">WON</option>
                <option value="NEGOTIATING">NEGOTIATING</option>
                <option value="PROPOSED">PROPOSED</option>
                <option value="LOST">LOST</option>
              </Select>
            </FormItem>

            <FormItem>
              <FormLabel>Sales Representative</FormLabel>
              <Input
                placeholder="Representative name"
                value={newDeal.sales_rep_name || ""}
                onChange={(e) =>
                  setNewDeal({ ...newDeal, sales_rep_name: e.target.value })
                }
              />
            </FormItem>
          </div>

          <FormItem>
            <FormLabel>Summary Notes</FormLabel>
            <Input
              placeholder="Key terms, SLA requirements, or discount highlights"
              value={newDeal.notes || ""}
              onChange={(e) => setNewDeal({ ...newDeal, notes: e.target.value })}
            />
          </FormItem>

          <div className="flex justify-end gap-2 pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsDealModalOpen(false)}
              disabled={dealLoading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={dealLoading}>
              Save Deal
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
