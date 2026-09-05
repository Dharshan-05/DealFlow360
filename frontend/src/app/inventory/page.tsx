"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Boxes,
  CheckCircle2,
  Clock,
  ExternalLink,
  Info,
  Package,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Truck,
  Warehouse,
  XCircle,
} from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ColumnDef, DataTable } from "@/components/ui/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { FormItem, FormLabel } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { LoadingState } from "@/components/ui/loading-state";
import { Modal } from "@/components/ui/modal";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { UnauthorizedState } from "@/components/ui/unauthorized-state";
import { backordersApi, fulfillmentsApi, inventoryApi, productsApi } from "@/lib/api";
import { Product } from "@/types/product";
import {
  Backorder,
  Fulfillment,
  FulfillmentDeliveryStatusUpdateInput,
  InventoryAlert,
  InventoryDashboardResponse,
  WarehouseStockBreakdown,
} from "@/types/inventory";

export default function InventoryPage() {
  const { user } = useAuth();
  const toast = useToast();

  const allowedRoles = ["Admin", "Operations", "Sales Representative", "Sales Manager"];
  const hasAccess =
    user?.roles.some((r) => allowedRoles.includes(r)) || user?.roles.includes("Admin");
  const canMutate =
    user?.roles.some((r) => ["Admin", "Operations"].includes(r)) || user?.roles.includes("Admin");

  // Main navigation tab
  const [activeTab, setActiveTab] = useState<"overview" | "fulfillments" | "backorders" | "alerts">("overview");

  // Data states
  const [dashboard, setDashboard] = useState<InventoryDashboardResponse | null>(null);
  const [fulfillments, setFulfillments] = useState<Fulfillment[]>([]);
  const [backorders, setBackorders] = useState<Backorder[]>([]);
  const [alerts, setAlerts] = useState<InventoryAlert[]>([]);
  const [products, setProducts] = useState<Product[]>([]);

  // Loading / Error states
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  // Modals state
  const [isFulfillmentModalOpen, setIsFulfillmentModalOpen] = useState<boolean>(false);
  const [isDeliveryModalOpen, setIsDeliveryModalOpen] = useState<boolean>(false);
  const [selectedFulfillment, setSelectedFulfillment] = useState<Fulfillment | null>(null);

  // Fulfillment form state
  const [targetProductId, setTargetProductId] = useState<string>("");
  const [requestedQuantity, setRequestedQuantity] = useState<number>(1);
  const [fulfillmentNotes, setFulfillmentNotes] = useState<string>("");
  const [submittingFulfillment, setSubmittingFulfillment] = useState<boolean>(false);

  // Delivery status update form state
  const [nextDeliveryStatus, setNextDeliveryStatus] = useState<string>("");
  const [trackingNumber, setTrackingNumber] = useState<string>("");
  const [deliveryNotes, setDeliveryNotes] = useState<string>("");
  const [submittingDelivery, setSubmittingDelivery] = useState<boolean>(false);

  // Load master data
  const loadData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const [dashData, fData, bData, aData, pData] = await Promise.all([
        inventoryApi.getDashboard(),
        fulfillmentsApi.listFulfillments({ limit: 100 }),
        backordersApi.listBackorders({ limit: 100 }),
        inventoryApi.listAlerts({ limit: 100 }),
        productsApi.getAll({ limit: 100 }),
      ]);


      setDashboard(dashData);
      setFulfillments(fData.items || []);
      setBackorders(bData.items || []);
      setAlerts(aData.items || []);
      setProducts(pData.items || []);
    } catch (err: any) {
      setError(err?.message || "Failed to load inventory data");
      toast.error("Failed to load inventory data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [toast]);

  useEffect(() => {
    if (hasAccess) {
      loadData();
    }
  }, [hasAccess, loadData]);

  // Handle on-demand alert scan
  const handleScanAlerts = async () => {
    try {
      const res = await inventoryApi.scanAlerts();
      toast.success(
        `Scan complete: ${res.alerts_generated} generated, ${res.alerts_resolved} resolved. Active: ${res.total_active}`
      );
      loadData(true);
    } catch (err: any) {
      toast.error(err?.message || "Alert scan failed");
    }
  };

  // Handle alert resolution
  const handleResolveAlert = async (alertId: string) => {
    try {
      await inventoryApi.resolveAlert(alertId, "Manually resolved from inventory console");
      toast.success("Alert resolved successfully");
      loadData(true);
    } catch (err: any) {
      toast.error(err?.message || "Failed to resolve alert");
    }
  };

  // Handle backorder cancellation
  const handleCancelBackorder = async (backorderId: string) => {
    if (!confirm("Are you sure you want to cancel this open backorder?")) return;
    try {
      await backordersApi.cancelBackorder(backorderId, "Cancelled by operations manager");
      toast.success("Backorder cancelled successfully");
      loadData(true);
    } catch (err: any) {
      toast.error(err?.message || "Failed to cancel backorder");
    }
  };

  // Submit New Fulfillment Request
  const handleCreateFulfillment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetProductId) {
      toast.error("Please select a product");
      return;
    }
    if (requestedQuantity <= 0) {
      toast.error("Requested quantity must be strictly greater than 0");
      return;
    }

    setSubmittingFulfillment(true);
    try {
      const result = await fulfillmentsApi.createFulfillment({
        product_id: targetProductId,
        requested_quantity: requestedQuantity,
        notes: fulfillmentNotes || undefined,
      });

      if (result.status === "FULFILLED") {
        toast.success(`Fulfillment created: Fully allocated ${result.fulfilled_quantity} units!`);
      } else if (result.status === "PARTIALLY_FULFILLED") {
        toast.warning(
          `Partially fulfilled (${result.fulfilled_quantity}/${result.requested_quantity}). ${result.remaining_quantity} units placed on backorder!`
        );
      } else {
        toast.error(`Stock unavailable. Entire requested amount (${result.requested_quantity}) backordered.`);
      }

      setIsFulfillmentModalOpen(false);
      setTargetProductId("");
      setRequestedQuantity(1);
      setFulfillmentNotes("");
      loadData(true);
    } catch (err: any) {
      toast.error(err?.message || "Failed to process fulfillment request");
    } finally {
      setSubmittingFulfillment(false);
    }
  };

  // Open delivery status update modal
  const openDeliveryModal = (f: Fulfillment) => {
    setSelectedFulfillment(f);
    setNextDeliveryStatus("");
    setTrackingNumber(f.tracking_number || "");
    setDeliveryNotes("");
    setIsDeliveryModalOpen(true);
  };

  // Submit Delivery Status Update
  const handleUpdateDeliveryStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFulfillment || !nextDeliveryStatus) {
      toast.error("Please select a valid next delivery status");
      return;
    }

    setSubmittingDelivery(true);
    try {
      await fulfillmentsApi.updateDeliveryStatus(selectedFulfillment.id, {
        delivery_status: nextDeliveryStatus as any,
        tracking_number: trackingNumber || undefined,
        notes: deliveryNotes || undefined,
      });

      toast.success(`Delivery status updated to ${nextDeliveryStatus}`);
      setIsDeliveryModalOpen(false);
      setSelectedFulfillment(null);
      loadData(true);
    } catch (err: any) {
      toast.error(err?.message || "Failed to update delivery status");
    } finally {
      setSubmittingDelivery(false);
    }
  };

  // Status badge styling helper
  const getDeliveryBadge = (status: string) => {
    switch (status) {
      case "NOT_STARTED":
        return <Badge variant="outline" className="bg-slate-50 text-slate-700 border-slate-300">NOT STARTED</Badge>;
      case "READY":
        return <Badge className="bg-blue-100 text-blue-800 border-blue-200">READY</Badge>;
      case "DISPATCHED":
        return <Badge className="bg-indigo-100 text-indigo-800 border-indigo-200">DISPATCHED</Badge>;
      case "IN_TRANSIT":
        return <Badge className="bg-amber-100 text-amber-800 border-amber-200">IN TRANSIT</Badge>;
      case "DELIVERED":
        return <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">DELIVERED</Badge>;
      case "CANCELLED":
        return <Badge className="bg-rose-100 text-rose-800 border-rose-200">CANCELLED</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getFulfillmentBadge = (status: string) => {
    switch (status) {
      case "FULFILLED":
        return <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">FULFILLED</Badge>;
      case "PARTIALLY_FULFILLED":
        return <Badge className="bg-amber-100 text-amber-800 border-amber-200">PARTIAL</Badge>;
      case "PENDING":
        return <Badge className="bg-purple-100 text-purple-800 border-purple-200">PENDING</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getAlertBadge = (type: string, severity: string) => {
    if (severity === "CRITICAL") {
      return <Badge className="bg-rose-100 text-rose-800 border-rose-200 font-bold">{type}</Badge>;
    }
    return <Badge className="bg-amber-100 text-amber-800 border-amber-200">{type}</Badge>;
  };

  const getProductName = (prodId: string) => {
    const p = products.find((x) => x.id === prodId);
    return p ? `${p.sku} — ${p.name}` : prodId.substring(0, 8);
  };

  // Role Gate
  if (!hasAccess) {
    return (
      <ProtectedRoute>
        <UnauthorizedState message="You do not have permission to view inventory and fulfillment operations." />
      </ProtectedRoute>
    );
  }


  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-primary/10 rounded-xl text-primary">
                <Boxes className="w-7 h-7" />
              </div>
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
                  Inventory & Fulfillment Operations
                </h1>
                <p className="text-sm text-slate-500 mt-0.5">
                  Backorder Engine, Partial Allocation, Multi-Warehouse Fulfillment & Active Alerts (G20: Phases 096–100)
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadData(true)}
              disabled={refreshing || loading}
              className="gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleScanAlerts}
              className="gap-2 text-amber-600 border-amber-200 hover:bg-amber-50"
            >
              <AlertTriangle className="w-4 h-4" />
              Scan Alerts
            </Button>

            {canMutate && (
              <Button
                size="sm"
                onClick={() => setIsFulfillmentModalOpen(true)}
                className="gap-2"
              >
                <Plus className="w-4 h-4" />
                New Fulfillment Order
              </Button>
            )}
          </div>
        </div>

        {/* Global Error Banner */}
        {error && (
          <div className="mb-6">
            <ErrorState message={error} onRetry={() => loadData(true)} />
          </div>
        )}

        {/* Top Operational KPI Metrics */}
        {dashboard && (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4 mb-8">
            <Card className="bg-slate-50/50 border-slate-200">
              <CardContent className="p-4">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Physical</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{dashboard.kpis.total_physical_stock}</p>
                <p className="text-[11px] text-slate-400 mt-0.5">In facilities</p>
              </CardContent>
            </Card>

            <Card className="bg-amber-50/40 border-amber-200/60">
              <CardContent className="p-4">
                <p className="text-xs font-semibold text-amber-700 uppercase tracking-wider">Reserved</p>
                <p className="text-2xl font-bold text-amber-900 mt-1">{dashboard.kpis.total_reserved_stock}</p>
                <p className="text-[11px] text-amber-600/80 mt-0.5">Locked stock</p>
              </CardContent>
            </Card>

            <Card className="bg-emerald-50/40 border-emerald-200/60">
              <CardContent className="p-4">
                <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">ATP Stock</p>
                <p className="text-2xl font-bold text-emerald-900 mt-1">{dashboard.kpis.total_atp_stock}</p>
                <p className="text-[11px] text-emerald-600/80 mt-0.5">Promiseable</p>
              </CardContent>
            </Card>

            <Card className="bg-rose-50/40 border-rose-200/60">
              <CardContent className="p-4">
                <p className="text-xs font-semibold text-rose-700 uppercase tracking-wider">Out of Stock</p>
                <p className="text-2xl font-bold text-rose-900 mt-1">{dashboard.kpis.out_of_stock_count}</p>
                <p className="text-[11px] text-rose-600/80 mt-0.5">Critical SKUs</p>
              </CardContent>
            </Card>

            <Card className="bg-orange-50/40 border-orange-200/60">
              <CardContent className="p-4">
                <p className="text-xs font-semibold text-orange-700 uppercase tracking-wider">Low Stock</p>
                <p className="text-2xl font-bold text-orange-900 mt-1">{dashboard.kpis.low_stock_count}</p>
                <p className="text-[11px] text-orange-600/80 mt-0.5">&le; 10 units</p>
              </CardContent>
            </Card>

            <Card className="bg-purple-50/40 border-purple-200/60">
              <CardContent className="p-4">
                <p className="text-xs font-semibold text-purple-700 uppercase tracking-wider">Backorders</p>
                <p className="text-2xl font-bold text-purple-900 mt-1">{dashboard.kpis.open_backorders_count}</p>
                <p className="text-[11px] text-purple-600/80 mt-0.5">Active backlog</p>
              </CardContent>
            </Card>

            <Card className="bg-blue-50/40 border-blue-200/60">
              <CardContent className="p-4">
                <p className="text-xs font-semibold text-blue-700 uppercase tracking-wider">Partials</p>
                <p className="text-2xl font-bold text-blue-900 mt-1">{dashboard.kpis.partial_fulfillments_count}</p>
                <p className="text-[11px] text-blue-600/80 mt-0.5">In fulfillment</p>
              </CardContent>
            </Card>

            <Card className="bg-indigo-50/40 border-indigo-200/60">
              <CardContent className="p-4">
                <p className="text-xs font-semibold text-indigo-700 uppercase tracking-wider">Fulfillments</p>
                <p className="text-2xl font-bold text-indigo-900 mt-1">{dashboard.kpis.total_fulfillments_count}</p>
                <p className="text-[11px] text-indigo-600/80 mt-0.5">Total pipeline</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* View Navigation Tabs */}
        <div className="flex border-b border-slate-200 mb-6 gap-2">
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === "overview"
                ? "border-primary text-primary"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            Operations Overview
          </button>
          <button
            onClick={() => setActiveTab("fulfillments")}
            className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === "fulfillments"
                ? "border-primary text-primary"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            Fulfillments & Delivery
            <Badge variant="secondary" className="text-xs px-1.5 py-0">{fulfillments.length}</Badge>
          </button>
          <button
            onClick={() => setActiveTab("backorders")}
            className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === "backorders"
                ? "border-primary text-primary"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            Backorder Engine
            <Badge variant="secondary" className="text-xs px-1.5 py-0">{backorders.filter(b => b.status === "OPEN").length}</Badge>
          </button>
          <button
            onClick={() => setActiveTab("alerts")}
            className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === "alerts"
                ? "border-primary text-primary"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            Inventory Alerts
            <Badge className="bg-rose-100 text-rose-800 text-xs px-1.5 py-0 border-rose-200">
              {alerts.filter(a => a.is_active).length}
            </Badge>
          </button>
        </div>

        {/* Tab 1: Overview */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Warehouse Breakdown & Delivery Pipeline cards */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Warehouse Table */}
              <div className="lg:col-span-2">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Warehouse className="w-5 h-5 text-primary" />
                      Warehouse Network Breakdown (Priority-Ordered)
                    </CardTitle>
                    <CardDescription>
                      Physical stock, active reservations, and promiseable inventory across facilities
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm text-left">
                        <thead className="text-xs text-slate-500 bg-slate-50 border-y border-slate-200">
                          <tr>
                            <th className="px-4 py-3">Priority</th>
                            <th className="px-4 py-3">Code / Facility</th>
                            <th className="px-4 py-3 text-right">Physical</th>
                            <th className="px-4 py-3 text-right">Reserved</th>
                            <th className="px-4 py-3 text-right">ATP</th>
                            <th className="px-4 py-3 text-right">SKUs</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {dashboard?.warehouse_breakdown.map((wh) => (
                            <tr key={wh.warehouse_id} className="hover:bg-slate-50/50">
                              <td className="px-4 py-3">
                                <Badge variant="outline" className="font-mono">
                                  #{wh.priority}
                                </Badge>
                              </td>
                              <td className="px-4 py-3">
                                <div className="font-medium text-slate-900">{wh.warehouse_name}</div>
                                <div className="text-xs text-slate-500 font-mono">{wh.warehouse_code}</div>
                              </td>
                              <td className="px-4 py-3 text-right font-medium text-slate-900">{wh.total_quantity}</td>
                              <td className="px-4 py-3 text-right text-amber-700 font-medium">{wh.total_reserved}</td>
                              <td className="px-4 py-3 text-right font-bold text-emerald-700">{wh.total_atp}</td>
                              <td className="px-4 py-3 text-right text-slate-500">{wh.sku_count}</td>
                            </tr>
                          ))}
                          {(!dashboard || dashboard.warehouse_breakdown.length === 0) && (
                            <tr>
                              <td colSpan={6} className="text-center py-6 text-slate-400">
                                No warehouse facilities found
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Delivery State Distribution */}
              <div>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Truck className="w-5 h-5 text-primary" />
                      Delivery Pipeline
                    </CardTitle>
                    <CardDescription>
                      Distribution of active fulfillments across delivery statuses
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {dashboard && (
                      <>
                        <div className="space-y-2">
                          {Object.entries(dashboard.delivery_status_distribution).map(([st, count]) => (
                            <div key={st} className="flex items-center justify-between text-sm py-1">
                              <div className="flex items-center gap-2">
                                {getDeliveryBadge(st)}
                              </div>
                              <span className="font-semibold text-slate-700">{count}</span>
                            </div>
                          ))}
                        </div>
                        <div className="pt-4 border-t border-slate-100">
                          <Link href="/warehouses">
                            <Button variant="outline" className="w-full justify-between text-xs">
                              Manage Warehouses & Stocks
                              <ArrowRight className="w-3.5 h-3.5" />
                            </Button>
                          </Link>
                        </div>
                      </>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* Active Alerts Fast Feed */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-3">
                <div>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-600" />
                    Active Inventory Alerts
                  </CardTitle>
                  <CardDescription>
                    Real-time warnings: Out of Stock, Low Stock, and Unresolved Backorders
                  </CardDescription>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setActiveTab("alerts")} className="gap-1 text-xs">
                  View All Alerts <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {alerts.filter(a => a.is_active).slice(0, 5).map((a) => (
                    <div
                      key={a.id}
                      className="p-3 rounded-lg border border-slate-200 bg-slate-50/50 flex items-center justify-between gap-4"
                    >
                      <div className="flex items-start gap-3">
                        <div className="mt-0.5">{getAlertBadge(a.alert_type, a.severity)}</div>
                        <div>
                          <p className="text-sm font-medium text-slate-900">{a.message}</p>
                          <p className="text-xs text-slate-400 mt-0.5">
                            {new Date(a.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      {canMutate && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleResolveAlert(a.id)}
                          className="text-xs shrink-0"
                        >
                          Resolve
                        </Button>
                      )}
                    </div>
                  ))}
                  {alerts.filter(a => a.is_active).length === 0 && (
                    <div className="text-center py-6 text-slate-400 text-sm">
                      No active alerts detected. All warehouse stock levels are healthy!
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tab 2: Fulfillments & Delivery Status */}
        {activeTab === "fulfillments" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Fulfillments & Delivery Lifecycle</h3>
                <p className="text-sm text-slate-500">
                  Track allocation fulfillment and advance delivery states (Phase 097 & 098 State Machine)
                </p>
              </div>
              {canMutate && (
                <Button size="sm" onClick={() => setIsFulfillmentModalOpen(true)} className="gap-2">
                  <Plus className="w-4 h-4" /> New Fulfillment
                </Button>
              )}
            </div>

            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs text-slate-500 bg-slate-50 border-b border-slate-200">
                      <tr>
                        <th className="px-4 py-3">Product</th>
                        <th className="px-4 py-3 text-right">Requested</th>
                        <th className="px-4 py-3 text-right">Fulfilled</th>
                        <th className="px-4 py-3 text-right">Remaining</th>
                        <th className="px-4 py-3 text-center">Fulfillment Status</th>
                        <th className="px-4 py-3 text-center">Delivery Status</th>
                        <th className="px-4 py-3">Tracking</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {fulfillments.map((f) => (
                        <tr key={f.id} className="hover:bg-slate-50/50">
                          <td className="px-4 py-3">
                            <div className="font-medium text-slate-900">{getProductName(f.product_id)}</div>
                            <div className="text-xs text-slate-400 font-mono">{f.id.substring(0, 8)}</div>
                          </td>
                          <td className="px-4 py-3 text-right font-medium">{f.requested_quantity}</td>
                          <td className="px-4 py-3 text-right text-emerald-700 font-bold">{f.fulfilled_quantity}</td>
                          <td className="px-4 py-3 text-right text-amber-700 font-medium">{f.remaining_quantity}</td>
                          <td className="px-4 py-3 text-center">{getFulfillmentBadge(f.status)}</td>
                          <td className="px-4 py-3 text-center">{getDeliveryBadge(f.delivery_status)}</td>
                          <td className="px-4 py-3">
                            <span className="font-mono text-xs text-slate-600">
                              {f.tracking_number || "—"}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            {canMutate && f.delivery_status !== "DELIVERED" && f.delivery_status !== "CANCELLED" && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => openDeliveryModal(f)}
                                className="text-xs"
                              >
                                Advance Status
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                      {fulfillments.length === 0 && (
                        <tr>
                          <td colSpan={8} className="text-center py-8 text-slate-400">
                            No fulfillment records recorded yet.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tab 3: Backorders */}
        {activeTab === "backorders" && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-bold text-slate-900">Backorder Engine (Phase 096)</h3>
              <p className="text-sm text-slate-500">
                Managed inventory shortages created automatically when allocations cannot be satisfied immediately
              </p>
            </div>

            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs text-slate-500 bg-slate-50 border-b border-slate-200">
                      <tr>
                        <th className="px-4 py-3">Product</th>
                        <th className="px-4 py-3 text-right">Requested</th>
                        <th className="px-4 py-3 text-right">Allocated</th>
                        <th className="px-4 py-3 text-right">Backordered</th>
                        <th className="px-4 py-3 text-center">Status</th>
                        <th className="px-4 py-3">Notes</th>
                        <th className="px-4 py-3 text-right">Created</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {backorders.map((b) => (
                        <tr key={b.id} className="hover:bg-slate-50/50">
                          <td className="px-4 py-3">
                            <div className="font-medium text-slate-900">{getProductName(b.product_id)}</div>
                            <div className="text-xs text-slate-400 font-mono">{b.id.substring(0, 8)}</div>
                          </td>
                          <td className="px-4 py-3 text-right">{b.requested_quantity}</td>
                          <td className="px-4 py-3 text-right text-emerald-600">{b.allocated_quantity}</td>
                          <td className="px-4 py-3 text-right font-bold text-purple-700">{b.backordered_quantity}</td>
                          <td className="px-4 py-3 text-center">
                            {b.status === "OPEN" ? (
                              <Badge className="bg-purple-100 text-purple-800 border-purple-200">OPEN</Badge>
                            ) : b.status === "FULFILLED" ? (
                              <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">FULFILLED</Badge>
                            ) : (
                              <Badge className="bg-rose-100 text-rose-800 border-rose-200">CANCELLED</Badge>
                            )}
                          </td>
                          <td className="px-4 py-3 text-xs text-slate-500 max-w-xs truncate">{b.notes || "—"}</td>
                          <td className="px-4 py-3 text-right text-xs text-slate-400">
                            {new Date(b.created_at).toLocaleDateString()}
                          </td>
                          <td className="px-4 py-3 text-right">
                            {canMutate && b.status === "OPEN" && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleCancelBackorder(b.id)}
                                className="text-xs text-rose-600 border-rose-200 hover:bg-rose-50"
                              >
                                Cancel
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                      {backorders.length === 0 && (
                        <tr>
                          <td colSpan={8} className="text-center py-8 text-slate-400">
                            No backorders recorded.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tab 4: Inventory Alerts */}
        {activeTab === "alerts" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Inventory Alert Center (Phase 099)</h3>
                <p className="text-sm text-slate-500">
                  Critical Out of Stock alerts and Low Stock warnings with automatic deduplication
                </p>
              </div>
              <Button size="sm" variant="outline" onClick={handleScanAlerts} className="gap-2">
                <RefreshCw className="w-4 h-4" /> Run Alert Scan
              </Button>
            </div>

            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs text-slate-500 bg-slate-50 border-b border-slate-200">
                      <tr>
                        <th className="px-4 py-3">Severity / Type</th>
                        <th className="px-4 py-3">Product</th>
                        <th className="px-4 py-3">Message</th>
                        <th className="px-4 py-3 text-center">Status</th>
                        <th className="px-4 py-3 text-right">Detected</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {alerts.map((a) => (
                        <tr key={a.id} className="hover:bg-slate-50/50">
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              {getAlertBadge(a.alert_type, a.severity)}
                            </div>
                          </td>
                          <td className="px-4 py-3 font-medium text-slate-900">
                            {getProductName(a.product_id)}
                          </td>
                          <td className="px-4 py-3 text-slate-700">{a.message}</td>
                          <td className="px-4 py-3 text-center">
                            {a.is_active ? (
                              <Badge className="bg-rose-100 text-rose-800 border-rose-200">ACTIVE</Badge>
                            ) : (
                              <Badge variant="outline" className="bg-slate-100 text-slate-600">RESOLVED</Badge>
                            )}
                          </td>
                          <td className="px-4 py-3 text-right text-xs text-slate-400">
                            {new Date(a.created_at).toLocaleString()}
                          </td>
                          <td className="px-4 py-3 text-right">
                            {canMutate && a.is_active && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleResolveAlert(a.id)}
                                className="text-xs"
                              >
                                Resolve
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                      {alerts.length === 0 && (
                        <tr>
                          <td colSpan={6} className="text-center py-8 text-slate-400">
                            No inventory alerts found.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Modal: New Fulfillment Order */}
        <Modal
          isOpen={isFulfillmentModalOpen}
          onClose={() => setIsFulfillmentModalOpen(false)}
          title="Create Fulfillment Order"
          description="Allocate stock across priority warehouses and reserve atomically. Shortages automatically trigger backorders."
        >
          <form onSubmit={handleCreateFulfillment} className="space-y-4">
            <FormItem>
              <FormLabel>Select Product *</FormLabel>
              <Select
                value={targetProductId}
                onChange={(e) => setTargetProductId(e.target.value)}
                required
              >
                <option value="">-- Choose Product --</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.sku} — {p.name}
                  </option>
                ))}
              </Select>
            </FormItem>

            <FormItem>
              <FormLabel>Requested Quantity *</FormLabel>
              <Input
                type="number"
                min="1"
                value={requestedQuantity}
                onChange={(e) => setRequestedQuantity(parseInt(e.target.value) || 1)}
                required
              />
            </FormItem>

            <FormItem>
              <FormLabel>Order Notes / Customer Reference</FormLabel>
              <Textarea
                value={fulfillmentNotes}
                onChange={(e) => setFulfillmentNotes(e.target.value)}
                placeholder="e.g., Urgent replenishment order for Enterprise Client"
                rows={3}
              />
            </FormItem>

            <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsFulfillmentModalOpen(false)}
                disabled={submittingFulfillment}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={submittingFulfillment}>
                {submittingFulfillment ? "Allocating & Reserving..." : "Submit Order"}
              </Button>
            </div>
          </form>
        </Modal>

        {/* Modal: Advance Delivery Status */}
        <Modal
          isOpen={isDeliveryModalOpen}
          onClose={() => setIsDeliveryModalOpen(false)}
          title="Advance Delivery Status"
          description={`Current Status: ${selectedFulfillment?.delivery_status}. Only legal state machine transitions are permitted.`}
        >
          <form onSubmit={handleUpdateDeliveryStatus} className="space-y-4">
            <FormItem>
              <FormLabel>Next Delivery Status *</FormLabel>
              <Select
                value={nextDeliveryStatus}
                onChange={(e) => setNextDeliveryStatus(e.target.value)}
                required
              >
                <option value="">-- Select Next Status --</option>
                {selectedFulfillment?.delivery_status === "NOT_STARTED" && (
                  <>
                    <option value="READY">READY</option>
                    <option value="CANCELLED">CANCELLED</option>
                  </>
                )}
                {selectedFulfillment?.delivery_status === "READY" && (
                  <>
                    <option value="DISPATCHED">DISPATCHED</option>
                    <option value="CANCELLED">CANCELLED</option>
                  </>
                )}
                {selectedFulfillment?.delivery_status === "DISPATCHED" && (
                  <>
                    <option value="IN_TRANSIT">IN_TRANSIT</option>
                    <option value="CANCELLED">CANCELLED</option>
                  </>
                )}
                {selectedFulfillment?.delivery_status === "IN_TRANSIT" && (
                  <option value="DELIVERED">DELIVERED</option>
                )}
              </Select>
            </FormItem>

            {(nextDeliveryStatus === "DISPATCHED" || nextDeliveryStatus === "IN_TRANSIT" || nextDeliveryStatus === "DELIVERED") && (
              <FormItem>
                <FormLabel>Tracking Number</FormLabel>
                <Input
                  value={trackingNumber}
                  onChange={(e) => setTrackingNumber(e.target.value)}
                  placeholder="e.g. TRK-98301824"
                />
              </FormItem>
            )}

            <FormItem>
              <FormLabel>Delivery Notes</FormLabel>
              <Textarea
                value={deliveryNotes}
                onChange={(e) => setDeliveryNotes(e.target.value)}
                placeholder="Details about status update, courier notes, or reason"
                rows={2}
              />
            </FormItem>

            <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsDeliveryModalOpen(false)}
                disabled={submittingDelivery}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={submittingDelivery}>
                {submittingDelivery ? "Updating..." : "Confirm Status Change"}
              </Button>
            </div>
          </form>
        </Modal>
      </div>
    </ProtectedRoute>
  );
}
