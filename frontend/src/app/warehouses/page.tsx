"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowLeft,
  Boxes,
  Building2,
  CheckCircle2,
  Edit2,
  Lock,
  Package,
  Plus,
  PowerOff,
  RefreshCw,
  ShieldCheck,
  Truck,
  Warehouse as WarehouseIcon,
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
import { productsApi, warehousesApi } from "@/lib/api";
import { Product } from "@/types/product";
import {
  AllocationResponse,
  Warehouse,
  WarehouseCreateInput,
  WarehouseSelectionResponse,
  WarehouseStock,
  WarehouseStockListResponse,
  WarehouseUpdateInput,
} from "@/types/warehouse";

export default function WarehousesPage() {
  const { user } = useAuth();
  const toast = useToast();

  const allowedRoles = ["Admin", "Operations", "Sales Representative", "Sales Manager"];
  const hasAccess =
    user?.roles.some((r) => allowedRoles.includes(r)) || user?.roles.includes("Admin");
  const canMutate =
    user?.roles.some((r) => ["Admin", "Operations"].includes(r)) || user?.roles.includes("Admin");

  // View state
  const [selectedWarehouse, setSelectedWarehouse] = useState<Warehouse | null>(null);

  // List State
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [totalWarehouses, setTotalWarehouses] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Warehouse Stock View State
  const [stockData, setStockData] = useState<WarehouseStockListResponse | null>(null);
  const [isStockLoading, setIsStockLoading] = useState<boolean>(false);

  // Catalog products for stock creation dropdown
  const [catalogProducts, setCatalogProducts] = useState<Product[]>([]);

  // Modals state
  const [isCreateWarehouseOpen, setIsCreateWarehouseOpen] = useState<boolean>(false);
  const [createWarehouseLoading, setCreateWarehouseLoading] = useState<boolean>(false);
  const [newWarehouse, setNewWarehouse] = useState<WarehouseCreateInput>({
    code: "",
    name: "",
    description: "",
    address: "",
    city: "",
    state: "",
    country: "United States",
    postal_code: "",
    is_active: true,
  });

  const [editingWarehouse, setEditingWarehouse] = useState<Warehouse | null>(null);
  const [editWarehouseLoading, setEditWarehouseLoading] = useState<boolean>(false);

  // Stock Modals
  const [isSetStockOpen, setIsSetStockOpen] = useState<boolean>(false);
  const [setStockLoading, setSetStockLoading] = useState<boolean>(false);
  const [newStock, setNewStock] = useState<{
    product_id: string;
    quantity: number;
    reserved_quantity: number;
  }>({
    product_id: "",
    quantity: 0,
    reserved_quantity: 0,
  });

  const [adjustingStock, setAdjustingStock] = useState<WarehouseStock | null>(null);
  const [adjustStockLoading, setAdjustStockLoading] = useState<boolean>(false);
  const [adjustedQty, setAdjustedQty] = useState<number>(0);

  // Reserve/Release Modal (Phase 089)
  const [reserveReleaseStock, setReserveReleaseStock] = useState<WarehouseStock | null>(null);
  const [reserveReleaseMode, setReserveReleaseMode] = useState<"reserve" | "release">("reserve");
  const [reserveReleaseQty, setReserveReleaseQty] = useState<number>(1);
  const [reserveReleaseLoading, setReserveReleaseLoading] = useState<boolean>(false);

  // Fulfillment Allocation Simulation Modal (Phases 092, 094, 095)
  const [isAllocationModalOpen, setIsAllocationModalOpen] = useState<boolean>(false);
  const [allocProductId, setAllocProductId] = useState<string>("");
  const [allocQty, setAllocQty] = useState<number>(10);
  const [allocLoading, setAllocLoading] = useState<boolean>(false);
  const [allocResult, setAllocResult] = useState<AllocationResponse | null>(null);
  const [selectionResult, setSelectionResult] = useState<WarehouseSelectionResponse | null>(null);
  const [isReservingAllocation, setIsReservingAllocation] = useState<boolean>(false);

  // ---------------------------------------------------------------------------
  // Data Loading
  // ---------------------------------------------------------------------------
  const loadWarehouses = useCallback(async () => {
    try {
      setError(null);
      const res = await warehousesApi.getAll({
        search: searchQuery.trim() || undefined,
        limit: 50,
      });
      setWarehouses(res.items);
      setTotalWarehouses(res.total);
    } catch (err: any) {
      setError(err.message || "Failed to load warehouses");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [searchQuery]);

  const loadStock = useCallback(
    async (warehouseId: string) => {
      try {
        setIsStockLoading(true);
        const data = await warehousesApi.getStock(warehouseId);
        setStockData(data);
      } catch (err: any) {
        toast.error(err.message || "Failed to load warehouse stock");
      } finally {
        setIsStockLoading(false);
      }
    },
    [toast]
  );

  const loadCatalogProducts = useCallback(async () => {
    try {
      const res = await productsApi.getAll({ limit: 100, is_active: true });
      setCatalogProducts(res.items);
    } catch {
      // Non-blocking
    }
  }, []);

  useEffect(() => {
    if (hasAccess) {
      loadWarehouses();
      loadCatalogProducts();
    }
  }, [hasAccess, loadWarehouses, loadCatalogProducts]);

  useEffect(() => {
    if (selectedWarehouse) {
      loadStock(selectedWarehouse.id);
    }
  }, [selectedWarehouse, loadStock]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    if (selectedWarehouse) {
      loadStock(selectedWarehouse.id);
      loadWarehouses();
    } else {
      loadWarehouses();
    }
  };

  // ---------------------------------------------------------------------------
  // Warehouse CRUD Actions (Phase 086)
  // ---------------------------------------------------------------------------
  const handleCreateWarehouse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWarehouse.code.trim() || !newWarehouse.name.trim()) {
      toast.error("Facility Code and Name are required.");
      return;
    }

    try {
      setCreateWarehouseLoading(true);
      await warehousesApi.create({
        ...newWarehouse,
        code: newWarehouse.code.trim().toUpperCase(),
        name: newWarehouse.name.trim(),
        priority: Number(newWarehouse.priority) || 1,
      });
      toast.success(`Warehouse "${newWarehouse.name}" registered successfully.`);
      setIsCreateWarehouseOpen(false);
      setNewWarehouse({
        code: "",
        name: "",
        description: "",
        address: "",
        city: "",
        state: "",
        country: "United States",
        postal_code: "",
        is_active: true,
        priority: 1,
      });
      loadWarehouses();
    } catch (err: any) {
      toast.error(err.message || "Failed to register warehouse.");
    } finally {
      setCreateWarehouseLoading(false);
    }
  };

  const handleUpdateWarehouse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingWarehouse) return;

    try {
      setEditWarehouseLoading(true);
      await warehousesApi.update(editingWarehouse.id, {
        name: editingWarehouse.name.trim(),
        description: editingWarehouse.description || null,
        address: editingWarehouse.address || null,
        city: editingWarehouse.city || null,
        state: editingWarehouse.state || null,
        country: editingWarehouse.country || null,
        postal_code: editingWarehouse.postal_code || null,
        is_active: editingWarehouse.is_active,
        priority: Number(editingWarehouse.priority) || 1,
      });
      toast.success(`Warehouse "${editingWarehouse.name}" updated successfully.`);
      setEditingWarehouse(null);
      loadWarehouses();
      if (selectedWarehouse && selectedWarehouse.id === editingWarehouse.id) {
        setSelectedWarehouse({ ...editingWarehouse });
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to update warehouse.");
    } finally {
      setEditWarehouseLoading(false);
    }
  };

  const handleDeactivateWarehouse = async (warehouse: Warehouse) => {
    if (!confirm(`Are you sure you want to deactivate warehouse "${warehouse.name}"?`)) return;

    try {
      await warehousesApi.delete(warehouse.id);
      toast.success(`Warehouse "${warehouse.name}" deactivated.`);
      loadWarehouses();
      if (selectedWarehouse && selectedWarehouse.id === warehouse.id) {
        setSelectedWarehouse((prev) => (prev ? { ...prev, is_active: false } : null));
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to deactivate warehouse.");
    }
  };

  // ---------------------------------------------------------------------------
  // Stock Actions (Phases 087, 089, 090)
  // ---------------------------------------------------------------------------
  const handleSetStock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedWarehouse || !newStock.product_id) {
      toast.error("Please select a product.");
      return;
    }

    try {
      setSetStockLoading(true);
      await warehousesApi.setStock(selectedWarehouse.id, {
        product_id: newStock.product_id,
        quantity: Number(newStock.quantity),
        reserved_quantity: Number(newStock.reserved_quantity),
      });
      toast.success("Stock configured successfully.");
      setIsSetStockOpen(false);
      setNewStock({ product_id: "", quantity: 0, reserved_quantity: 0 });
      loadStock(selectedWarehouse.id);
      loadWarehouses();
    } catch (err: any) {
      toast.error(err.message || "Failed to configure stock.");
    } finally {
      setSetStockLoading(false);
    }
  };

  const handleUpdateStockQuantity = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedWarehouse || !adjustingStock) return;

    try {
      setAdjustStockLoading(true);
      await warehousesApi.updateStock(selectedWarehouse.id, adjustingStock.product_id, {
        quantity: Number(adjustedQty),
      });
      toast.success("Physical stock updated successfully.");
      setAdjustingStock(null);
      loadStock(selectedWarehouse.id);
      loadWarehouses();
    } catch (err: any) {
      toast.error(err.message || "Failed to update stock quantity.");
    } finally {
      setAdjustStockLoading(false);
    }
  };

  const handleReserveReleaseStock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedWarehouse || !reserveReleaseStock || reserveReleaseQty <= 0) return;

    try {
      setReserveReleaseLoading(true);
      if (reserveReleaseMode === "reserve") {
        await warehousesApi.reserveStock(selectedWarehouse.id, reserveReleaseStock.product_id, {
          quantity: Number(reserveReleaseQty),
        });
        toast.success(`Successfully reserved ${reserveReleaseQty} units.`);
      } else {
        await warehousesApi.releaseStock(selectedWarehouse.id, reserveReleaseStock.product_id, {
          quantity: Number(reserveReleaseQty),
        });
        toast.success(`Successfully released ${reserveReleaseQty} units.`);
      }
      setReserveReleaseStock(null);
      setReserveReleaseQty(1);
      loadStock(selectedWarehouse.id);
      loadWarehouses();
    } catch (err: any) {
      toast.error(err.message || "Reservation mutation failed.");
    } finally {
      setReserveReleaseLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Table Columns
  // ---------------------------------------------------------------------------
  const warehouseColumns: ColumnDef<Warehouse>[] = [
    {
      id: "code",
      header: "Code",
      accessorKey: "code",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-semibold text-primary px-2 py-0.5 rounded bg-primary/10">
          {row.code}
        </span>
      ),
    },
    {
      id: "priority",
      header: "Priority (Phase 091)",
      accessorKey: "priority",
      sortable: true,
      cell: (row) => (
        <Badge
          variant={row.priority === 1 ? "success" : row.priority === 2 ? "secondary" : "outline"}
          className="font-mono text-xs font-semibold"
        >
          P{row.priority} {row.priority === 1 ? "(Primary)" : ""}
        </Badge>
      ),
    },
    {
      id: "name",
      header: "Warehouse Name",
      accessorKey: "name",
      sortable: true,
      cell: (row) => (
        <div>
          <div className="font-medium text-foreground">{row.name}</div>
          {row.description && (
            <div className="text-xs text-muted truncate max-w-xs">{row.description}</div>
          )}
        </div>
      ),
    },
    {
      id: "location",
      header: "Location",
      cell: (row) => {
        const parts = [row.city, row.state, row.country].filter(Boolean);
        return (
          <span className="text-xs text-slate-600">
            {parts.length > 0 ? parts.join(", ") : "—"}
          </span>
        );
      },
    },
    {
      id: "stock_summary",
      header: "Inventory & ATP Summary",
      cell: (row) => (
        <div className="flex flex-col gap-0.5 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="text-muted">Items:</span>
            <span className="font-semibold text-slate-700">{row.total_stock_items}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-500">
              Phys: <strong className="text-slate-800">{row.total_physical_stock}</strong>
            </span>
            <span className="text-slate-500">
              Res: <strong className="text-amber-700">{row.total_reserved_stock}</strong>
            </span>
            <span className="text-emerald-700 font-semibold">
              ATP: {row.total_atp}
            </span>
          </div>
        </div>
      ),
    },
    {
      id: "is_active",
      header: "Status",
      accessorKey: "is_active",
      sortable: true,
      cell: (row) =>
        row.is_active ? (
          <Badge variant="success">Operational</Badge>
        ) : (
          <Badge variant="secondary">Deactivated</Badge>
        ),
    },
    {
      id: "actions",
      header: <div className="text-right">Actions</div>,
      cell: (row) => (
        <div className="flex items-center justify-end gap-1.5">
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs gap-1"
            onClick={() => setSelectedWarehouse(row)}
          >
            <Boxes className="h-3.5 w-3.5 text-primary" />
            <span>Stock &amp; ATP</span>
          </Button>
          {canMutate && (
            <>
              <Button
                variant="outline"
                size="sm"
                className="h-7 w-7 p-0"
                title="Edit Warehouse"
                onClick={() => setEditingWarehouse(row)}
              >
                <Edit2 className="h-3.5 w-3.5" />
              </Button>
              {row.is_active && (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 w-7 p-0 text-red-600 hover:text-red-700"
                  title="Deactivate Warehouse"
                  onClick={() => handleDeactivateWarehouse(row)}
                >
                  <PowerOff className="h-3.5 w-3.5" />
                </Button>
              )}
            </>
          )}
        </div>
      ),
    },
  ];

  const stockColumns: ColumnDef<WarehouseStock>[] = [
    {
      id: "product",
      header: "Product",
      cell: (row) => (
        <div>
          <div className="font-medium text-foreground">{row.product_name || "Unknown Product"}</div>
          <div className="text-xs font-mono text-muted">{row.product_sku || "—"}</div>
        </div>
      ),
    },
    {
      id: "category",
      header: "Category",
      cell: (row) => (
        <span className="text-xs text-slate-600">{row.category_name || "Uncategorized"}</span>
      ),
    },
    {
      id: "unit",
      header: "Unit",
      cell: (row) => (
        <span className="text-xs uppercase text-muted font-mono">{row.product_unit || "unit"}</span>
      ),
    },
    {
      id: "quantity",
      header: "Physical Stock",
      accessorKey: "quantity",
      sortable: true,
      cell: (row) => (
        <span className="font-semibold text-slate-900">{row.quantity}</span>
      ),
    },
    {
      id: "reserved_quantity",
      header: "Reserved (Phase 089)",
      accessorKey: "reserved_quantity",
      sortable: true,
      cell: (row) => (
        <span className="font-semibold text-amber-700">{row.reserved_quantity}</span>
      ),
    },
    {
      id: "available_to_promise",
      header: "ATP (Phase 090)",
      accessorKey: "available_to_promise",
      sortable: true,
      cell: (row) => (
        <div className="flex items-center gap-1.5">
          <span className="text-base font-bold text-emerald-700">
            {row.available_to_promise}
          </span>
        </div>
      ),
    },
    {
      id: "is_available",
      header: "Availability (Phase 088)",
      cell: (row) => {
        if (row.available_to_promise <= 0) {
          return <Badge variant="destructive">OUT OF STOCK</Badge>;
        } else if (row.available_to_promise <= 10) {
          return <Badge variant="warning">LOW STOCK</Badge>;
        }
        return <Badge variant="success">IN STOCK</Badge>;
      },
    },
    {
      id: "actions",
      header: <div className="text-right">Stock Actions</div>,
      cell: (row) => (
        <div className="flex items-center justify-end gap-1.5">
          {canMutate && (
            <>
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs"
                onClick={() => {
                  setAdjustingStock(row);
                  setAdjustedQty(row.quantity);
                }}
              >
                Adjust Stock
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs gap-1 text-purple-700 border-purple-200 hover:bg-purple-50"
                onClick={() => {
                  setReserveReleaseStock(row);
                  setReserveReleaseMode("reserve");
                  setReserveReleaseQty(1);
                }}
              >
                <Lock className="h-3 w-3" />
                <span>Reserve/Release</span>
              </Button>
            </>
          )}
        </div>
      ),
    },
  ];

  if (!hasAccess) {
    return (
      <ProtectedRoute>
        <UnauthorizedState message="Warehouse and inventory management requires Operations or Administrator privileges." />
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="space-y-6 pb-12">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                Warehouses &amp; Inventory
              </h1>
              <Badge variant="success">G19 Priority &amp; Allocation</Badge>
            </div>
            <p className="text-sm text-muted mt-1">
              Facility priority, deterministic selection, multi-warehouse stock visibility, and sequential fulfillment allocation (Phases 086–095).
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              isLoading={isRefreshing}
              className="gap-1.5"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Refresh</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setIsAllocationModalOpen(true);
                setAllocResult(null);
                setSelectionResult(null);
                if (!allocProductId && catalogProducts.length > 0) {
                  setAllocProductId(catalogProducts[0].id);
                }
              }}
              className="gap-1.5 text-blue-700 border-blue-200 hover:bg-blue-50"
            >
              <Truck className="h-4 w-4" />
              <span>Simulate Allocation</span>
            </Button>
            {canMutate && !selectedWarehouse && (
              <Button
                variant="primary"
                size="sm"
                className="gap-1.5"
                onClick={() => setIsCreateWarehouseOpen(true)}
              >
                <Plus className="h-4 w-4" />
                <span>Add Warehouse</span>
              </Button>
            )}
          </div>
        </div>

        {/* View Switch: Warehouse List or Warehouse Detail/Stock */}
        {selectedWarehouse ? (
          /* ================================================================= */
          /* WAREHOUSE DETAIL & STOCK VIEW (Phases 087, 088, 089, 090)         */
          /* ================================================================= */
          <div className="space-y-6">
            {/* Breadcrumb Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 rounded-xl bg-white border border-border shadow-xs">
              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 gap-1"
                  onClick={() => setSelectedWarehouse(null)}
                >
                  <ArrowLeft className="h-4 w-4" />
                  <span>All Facilities</span>
                </Button>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-primary px-2 py-0.5 rounded bg-primary/10">
                      {selectedWarehouse.code}
                    </span>
                    <h2 className="text-lg font-bold text-foreground">
                      {selectedWarehouse.name}
                    </h2>
                    {selectedWarehouse.is_active ? (
                      <Badge variant="success">Operational</Badge>
                    ) : (
                      <Badge variant="secondary">Deactivated</Badge>
                    )}
                  </div>
                  <div className="text-xs text-muted mt-0.5">
                    {[selectedWarehouse.city, selectedWarehouse.state, selectedWarehouse.country]
                      .filter(Boolean)
                      .join(", ") || "No location recorded"}
                    {selectedWarehouse.address ? ` • ${selectedWarehouse.address}` : ""}
                  </div>
                </div>
              </div>

              {canMutate && (
                <Button
                  variant="primary"
                  size="sm"
                  className="gap-1.5"
                  onClick={() => {
                    setNewStock({ product_id: "", quantity: 0, reserved_quantity: 0 });
                    setIsSetStockOpen(true);
                  }}
                >
                  <Plus className="h-4 w-4" />
                  <span>Configure Product Stock</span>
                </Button>
              )}
            </div>

            {/* ATP KPI Cards (Phase 089, 090) */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Card className="border-border">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs font-semibold text-muted uppercase">
                      Physical Stock On-Hand
                    </CardTitle>
                    <Package className="h-4 w-4 text-blue-600" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-slate-900">
                    {stockData?.total_physical ?? 0}
                  </div>
                  <p className="text-xs text-muted mt-0.5">
                    Total physical units registered across {stockData?.total ?? 0} products
                  </p>
                </CardContent>
              </Card>

              <Card className="border-amber-200/80 bg-amber-50/20">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs font-semibold text-amber-800 uppercase">
                      Reserved Stock (Phase 089)
                    </CardTitle>
                    <Lock className="h-4 w-4 text-amber-600" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-amber-900">
                    {stockData?.total_reserved ?? 0}
                  </div>
                  <p className="text-xs text-amber-700 mt-0.5">
                    Foundational allocated/reserved stock quantity
                  </p>
                </CardContent>
              </Card>

              <Card className="border-emerald-200 bg-emerald-50/30">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs font-semibold text-emerald-800 uppercase">
                      Available to Promise (ATP)
                    </CardTitle>
                    <ShieldCheck className="h-4 w-4 text-emerald-600" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-emerald-700">
                    {stockData?.total_atp ?? 0}
                  </div>
                  <p className="text-xs text-emerald-700 mt-0.5">
                    Deterministic ATP = max(Physical - Reserved, 0)
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Warehouse Stock Records Table */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold">
                  Product Inventory &amp; Availability
                </CardTitle>
                <CardDescription className="text-xs text-muted">
                  Warehouse-level stock quantities, reservations, and Available-to-Promise status
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                {isStockLoading ? (
                  <LoadingState message="Loading inventory records..." />
                ) : !stockData || stockData.items.length === 0 ? (
                  <div className="p-8">
                    <EmptyState
                      icon={Boxes}
                      title="No Inventory Configured"
                      description="No product stock records have been added to this warehouse yet."
                      action={
                        canMutate ? (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => setIsSetStockOpen(true)}
                          >
                            Add Product Stock
                          </Button>
                        ) : undefined
                      }
                    />
                  </div>
                ) : (
                  <DataTable
                    columns={stockColumns}
                    data={stockData.items}
                    keyExtractor={(item) => item.id}
                  />
                )}
              </CardContent>
            </Card>
          </div>
        ) : (
          /* ================================================================= */
          /* WAREHOUSE FACILITIES LIST VIEW (Phase 086)                        */
          /* ================================================================= */
          <div className="space-y-4">
            {/* Search Bar */}
            <div className="p-3.5 rounded-lg bg-white border border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="w-full sm:w-80">
                <Input
                  placeholder="Search code, name, city, state..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div className="text-xs text-muted">
                Showing {warehouses.length} of {totalWarehouses} facilities
              </div>
            </div>

            {/* Main Table */}
            <Card>
              <CardContent className="p-0">
                {isLoading ? (
                  <LoadingState message="Loading warehouse facilities..." />
                ) : error ? (
                  <div className="p-6">
                    <ErrorState
                      title="Error Loading Warehouses"
                      message={error}
                      onRetry={loadWarehouses}
                    />
                  </div>
                ) : warehouses.length === 0 ? (
                  <div className="p-8">
                    <EmptyState
                      icon={WarehouseIcon}
                      title="No Warehouses Found"
                      description={
                        searchQuery
                          ? "No warehouse facilities match the specified search term."
                          : "No warehouse distribution hubs have been configured yet."
                      }
                      action={
                        canMutate && !searchQuery ? (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => setIsCreateWarehouseOpen(true)}
                          >
                            Register Warehouse
                          </Button>
                        ) : undefined
                      }
                    />
                  </div>
                ) : (
                  <DataTable
                    columns={warehouseColumns}
                    data={warehouses}
                    keyExtractor={(item) => item.id}
                  />
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* ================================================================= */}
        {/* MODALS                                                            */}
        {/* ================================================================= */}

        {/* Create Warehouse Modal (Phase 086) */}
        <Modal
          isOpen={isCreateWarehouseOpen}
          onClose={() => setIsCreateWarehouseOpen(false)}
          title="Register Warehouse Facility"
          description="Create a new distribution center or logistics depot under the master company."
          size="md"
        >
          <form onSubmit={handleCreateWarehouse} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <FormItem>
                <FormLabel required>Warehouse Code</FormLabel>
                <Input
                  placeholder="e.g. WH-SOUTH"
                  value={newWarehouse.code}
                  onChange={(e) => setNewWarehouse({ ...newWarehouse, code: e.target.value })}
                  required
                />
              </FormItem>

              <FormItem>
                <FormLabel required>Facility Name</FormLabel>
                <Input
                  placeholder="e.g. South Central Logistics Hub"
                  value={newWarehouse.name}
                  onChange={(e) => setNewWarehouse({ ...newWarehouse, name: e.target.value })}
                  required
                />
              </FormItem>

              <FormItem>
                <FormLabel required>Priority (Phase 091)</FormLabel>
                <Input
                  type="number"
                  min={1}
                  placeholder="1"
                  value={newWarehouse.priority || 1}
                  onChange={(e) => setNewWarehouse({ ...newWarehouse, priority: parseInt(e.target.value) || 1 })}
                  required
                />
              </FormItem>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormItem>
                <FormLabel>City</FormLabel>
                <Input
                  placeholder="Dallas"
                  value={newWarehouse.city || ""}
                  onChange={(e) => setNewWarehouse({ ...newWarehouse, city: e.target.value })}
                />
              </FormItem>

              <FormItem>
                <FormLabel>State / Province</FormLabel>
                <Input
                  placeholder="TX"
                  value={newWarehouse.state || ""}
                  onChange={(e) => setNewWarehouse({ ...newWarehouse, state: e.target.value })}
                />
              </FormItem>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormItem>
                <FormLabel>Country</FormLabel>
                <Input
                  placeholder="United States"
                  value={newWarehouse.country || ""}
                  onChange={(e) => setNewWarehouse({ ...newWarehouse, country: e.target.value })}
                />
              </FormItem>

              <FormItem>
                <FormLabel>Postal Code</FormLabel>
                <Input
                  placeholder="75201"
                  value={newWarehouse.postal_code || ""}
                  onChange={(e) =>
                    setNewWarehouse({ ...newWarehouse, postal_code: e.target.value })
                  }
                />
              </FormItem>
            </div>

            <FormItem>
              <FormLabel>Street Address</FormLabel>
              <Input
                placeholder="400 Enterprise Parkway"
                value={newWarehouse.address || ""}
                onChange={(e) => setNewWarehouse({ ...newWarehouse, address: e.target.value })}
              />
            </FormItem>

            <FormItem>
              <FormLabel>Description</FormLabel>
              <Textarea
                placeholder="Facility capacity, regional delivery scope, dock specifications..."
                value={newWarehouse.description || ""}
                onChange={(e) =>
                  setNewWarehouse({ ...newWarehouse, description: e.target.value })
                }
                rows={2}
              />
            </FormItem>

            <div className="flex justify-end gap-2 pt-4 border-t border-border">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setIsCreateWarehouseOpen(false)}
                disabled={createWarehouseLoading}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" isLoading={createWarehouseLoading}>
                Register Warehouse
              </Button>
            </div>
          </form>
        </Modal>

        {/* Edit Warehouse Modal (Phase 086) */}
        <Modal
          isOpen={Boolean(editingWarehouse)}
          onClose={() => setEditingWarehouse(null)}
          title="Edit Warehouse Facility"
          description="Update warehouse details, address, and status."
          size="md"
        >
          {editingWarehouse && (
            <form onSubmit={handleUpdateWarehouse} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <FormItem>
                  <FormLabel>Warehouse Code</FormLabel>
                  <Input value={editingWarehouse.code} disabled className="bg-slate-50" />
                </FormItem>

                <FormItem>
                  <FormLabel required>Facility Name</FormLabel>
                  <Input
                    value={editingWarehouse.name}
                    onChange={(e) =>
                      setEditingWarehouse({ ...editingWarehouse, name: e.target.value })
                    }
                    required
                  />
                </FormItem>

                <FormItem>
                  <FormLabel required>Priority (Phase 091)</FormLabel>
                  <Input
                    type="number"
                    min={1}
                    value={editingWarehouse.priority || 1}
                    onChange={(e) =>
                      setEditingWarehouse({ ...editingWarehouse, priority: parseInt(e.target.value) || 1 })
                    }
                    required
                  />
                </FormItem>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormItem>
                  <FormLabel>City</FormLabel>
                  <Input
                    value={editingWarehouse.city || ""}
                    onChange={(e) =>
                      setEditingWarehouse({ ...editingWarehouse, city: e.target.value })
                    }
                  />
                </FormItem>

                <FormItem>
                  <FormLabel>State / Province</FormLabel>
                  <Input
                    value={editingWarehouse.state || ""}
                    onChange={(e) =>
                      setEditingWarehouse({ ...editingWarehouse, state: e.target.value })
                    }
                  />
                </FormItem>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormItem>
                  <FormLabel>Country</FormLabel>
                  <Input
                    value={editingWarehouse.country || ""}
                    onChange={(e) =>
                      setEditingWarehouse({ ...editingWarehouse, country: e.target.value })
                    }
                  />
                </FormItem>

                <FormItem>
                  <FormLabel>Postal Code</FormLabel>
                  <Input
                    value={editingWarehouse.postal_code || ""}
                    onChange={(e) =>
                      setEditingWarehouse({ ...editingWarehouse, postal_code: e.target.value })
                    }
                  />
                </FormItem>
              </div>

              <FormItem>
                <FormLabel>Street Address</FormLabel>
                <Input
                  value={editingWarehouse.address || ""}
                  onChange={(e) =>
                    setEditingWarehouse({ ...editingWarehouse, address: e.target.value })
                  }
                />
              </FormItem>

              <FormItem>
                <FormLabel>Description</FormLabel>
                <Textarea
                  value={editingWarehouse.description || ""}
                  onChange={(e) =>
                    setEditingWarehouse({ ...editingWarehouse, description: e.target.value })
                  }
                  rows={2}
                />
              </FormItem>

              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-border">
                <span className="text-sm font-medium text-slate-700">Operational Status</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={editingWarehouse.is_active}
                    onChange={(e) =>
                      setEditingWarehouse({ ...editingWarehouse, is_active: e.target.checked })
                    }
                  />
                  <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-border">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setEditingWarehouse(null)}
                  disabled={editWarehouseLoading}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm" isLoading={editWarehouseLoading}>
                  Save Changes
                </Button>
              </div>
            </form>
          )}
        </Modal>

        {/* Set / Configure Stock Modal (Phase 087) */}
        <Modal
          isOpen={isSetStockOpen}
          onClose={() => setIsSetStockOpen(false)}
          title="Configure Product Stock"
          description={`Add or initialize inventory for a product in warehouse ${selectedWarehouse?.code}.`}
          size="md"
        >
          <form onSubmit={handleSetStock} className="space-y-4">
            <FormItem>
              <FormLabel required>Select Product</FormLabel>
              <Select
                value={newStock.product_id}
                onChange={(e) => setNewStock({ ...newStock, product_id: e.target.value })}
                required
              >
                <option value="">-- Choose catalog product --</option>
                {catalogProducts.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.sku})
                  </option>
                ))}
              </Select>
            </FormItem>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormItem>
                <FormLabel required>Physical Stock Quantity</FormLabel>
                <Input
                  type="number"
                  min="0"
                  step="1"
                  value={newStock.quantity}
                  onChange={(e) =>
                    setNewStock({
                      ...newStock,
                      quantity: Math.max(0, parseInt(e.target.value || "0", 10)),
                    })
                  }
                  required
                />
                <span className="text-xs text-muted">Total units on facility shelves</span>
              </FormItem>

              <FormItem>
                <FormLabel required>Reserved Quantity (Phase 089)</FormLabel>
                <Input
                  type="number"
                  min="0"
                  max={newStock.quantity}
                  step="1"
                  value={newStock.reserved_quantity}
                  onChange={(e) =>
                    setNewStock({
                      ...newStock,
                      reserved_quantity: Math.max(0, parseInt(e.target.value || "0", 10)),
                    })
                  }
                  required
                />
                <span className="text-xs text-muted">Cannot exceed physical stock</span>
              </FormItem>
            </div>

            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-between">
              <span className="text-xs font-semibold text-emerald-900 uppercase">
                Available to Promise (ATP)
              </span>
              <span className="text-lg font-bold text-emerald-700">
                {Math.max(newStock.quantity - newStock.reserved_quantity, 0)} units
              </span>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-border">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setIsSetStockOpen(false)}
                disabled={setStockLoading}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" isLoading={setStockLoading}>
                Save Stock
              </Button>
            </div>
          </form>
        </Modal>

        {/* Adjust Physical Stock Modal (Phase 087) */}
        <Modal
          isOpen={Boolean(adjustingStock)}
          onClose={() => setAdjustingStock(null)}
          title="Adjust Physical Stock"
          description="Update physical on-hand inventory quantity."
          size="sm"
        >
          {adjustingStock && (
            <form onSubmit={handleUpdateStockQuantity} className="space-y-4">
              <div className="p-3 rounded-lg bg-slate-50 border border-border">
                <div className="font-semibold text-sm text-foreground">
                  {adjustingStock.product_name}
                </div>
                <div className="text-xs font-mono text-muted">{adjustingStock.product_sku}</div>
              </div>

              <div className="flex items-center justify-between text-xs px-1">
                <span className="text-muted">Reserved Amount:</span>
                <span className="font-semibold text-amber-700">
                  {adjustingStock.reserved_quantity} units
                </span>
              </div>

              <FormItem>
                <FormLabel required>New Physical Quantity</FormLabel>
                <Input
                  type="number"
                  min={adjustingStock.reserved_quantity}
                  step="1"
                  value={adjustedQty}
                  onChange={(e) =>
                    setAdjustedQty(Math.max(0, parseInt(e.target.value || "0", 10)))
                  }
                  required
                />
                <span className="text-xs text-muted">
                  Must be at least {adjustingStock.reserved_quantity} (currently reserved)
                </span>
              </FormItem>

              <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-900 uppercase">
                  Calculated ATP
                </span>
                <span className="text-lg font-bold text-emerald-700">
                  {Math.max(adjustedQty - adjustingStock.reserved_quantity, 0)}
                </span>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-border">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setAdjustingStock(null)}
                  disabled={adjustStockLoading}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm" isLoading={adjustStockLoading}>
                  Update Physical Stock
                </Button>
              </div>
            </form>
          )}
        </Modal>

        {/* Reserve / Release Stock Modal (Phases 089, 090) */}
        <Modal
          isOpen={Boolean(reserveReleaseStock)}
          onClose={() => setReserveReleaseStock(null)}
          title="Stock Reservation Management"
          description="Foundational reserve and release operations (Phase 089)."
          size="sm"
        >
          {reserveReleaseStock && (
            <form onSubmit={handleReserveReleaseStock} className="space-y-4">
              <div className="p-3 rounded-lg bg-slate-50 border border-border">
                <div className="font-semibold text-sm text-foreground">
                  {reserveReleaseStock.product_name}
                </div>
                <div className="text-xs font-mono text-muted">
                  {reserveReleaseStock.product_sku}
                </div>
                <div className="grid grid-cols-3 gap-2 mt-2 pt-2 border-t border-border text-center">
                  <div>
                    <div className="text-[10px] text-muted uppercase">Physical</div>
                    <div className="font-semibold text-xs text-slate-800">
                      {reserveReleaseStock.quantity}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-amber-700 uppercase">Reserved</div>
                    <div className="font-semibold text-xs text-amber-800">
                      {reserveReleaseStock.reserved_quantity}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-emerald-700 uppercase">Current ATP</div>
                    <div className="font-semibold text-xs text-emerald-800">
                      {reserveReleaseStock.available_to_promise}
                    </div>
                  </div>
                </div>
              </div>

              {/* Mode Toggle */}
              <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-lg">
                <button
                  type="button"
                  onClick={() => setReserveReleaseMode("reserve")}
                  className={`py-1.5 text-xs font-medium rounded-md transition-all ${
                    reserveReleaseMode === "reserve"
                      ? "bg-white text-purple-900 shadow-xs"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Reserve Stock
                </button>
                <button
                  type="button"
                  onClick={() => setReserveReleaseMode("release")}
                  className={`py-1.5 text-xs font-medium rounded-md transition-all ${
                    reserveReleaseMode === "release"
                      ? "bg-white text-purple-900 shadow-xs"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Release Stock
                </button>
              </div>

              <FormItem>
                <FormLabel required>
                  {reserveReleaseMode === "reserve" ? "Quantity to Reserve" : "Quantity to Release"}
                </FormLabel>
                <Input
                  type="number"
                  min="1"
                  max={
                    reserveReleaseMode === "reserve"
                      ? reserveReleaseStock.available_to_promise
                      : reserveReleaseStock.reserved_quantity
                  }
                  step="1"
                  value={reserveReleaseQty}
                  onChange={(e) =>
                    setReserveReleaseQty(Math.max(1, parseInt(e.target.value || "1", 10)))
                  }
                  required
                />
                <span className="text-xs text-muted">
                  {reserveReleaseMode === "reserve"
                    ? `Max available to reserve: ${reserveReleaseStock.available_to_promise}`
                    : `Max available to release: ${reserveReleaseStock.reserved_quantity}`}
                </span>
              </FormItem>

              <div className="p-3 rounded-lg bg-purple-50 border border-purple-200 flex items-center justify-between">
                <span className="text-xs font-semibold text-purple-900 uppercase">
                  Projected ATP
                </span>
                <span className="text-lg font-bold text-purple-700">
                  {reserveReleaseMode === "reserve"
                    ? Math.max(reserveReleaseStock.available_to_promise - reserveReleaseQty, 0)
                    : reserveReleaseStock.available_to_promise + reserveReleaseQty}
                </span>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-border">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setReserveReleaseStock(null)}
                  disabled={reserveReleaseLoading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={reserveReleaseLoading}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  {reserveReleaseMode === "reserve" ? "Confirm Reservation" : "Confirm Release"}
                </Button>
              </div>
            </form>
          )}
        </Modal>

        {/* Fulfillment Allocation Simulation Modal (Phases 092, 094, 095) */}
        <Modal
          isOpen={isAllocationModalOpen}
          onClose={() => setIsAllocationModalOpen(false)}
          title="Fulfillment Allocation & Priority Selection"
          description="Simulate deterministic order allocation across priority-ordered facilities."
          size="lg"
        >
          <div className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="sm:col-span-2">
                <FormItem>
                  <FormLabel required>Select Product</FormLabel>
                  <Select
                    value={allocProductId}
                    onChange={(e) => {
                      setAllocProductId(e.target.value);
                      setAllocResult(null);
                      setSelectionResult(null);
                    }}
                  >
                    <option value="" disabled>Choose a product...</option>
                    {catalogProducts.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.sku} — {p.name}
                      </option>
                    ))}
                  </Select>
                </FormItem>
              </div>

              <div>
                <FormItem>
                  <FormLabel required>Requested Quantity</FormLabel>
                  <Input
                    type="number"
                    min="1"
                    value={allocQty}
                    onChange={(e) => {
                      setAllocQty(Math.max(1, parseInt(e.target.value || "1", 10)));
                      setAllocResult(null);
                      setSelectionResult(null);
                    }}
                  />
                </FormItem>
              </div>
            </div>

            <div className="flex justify-start gap-2">
              <Button
                variant="primary"
                size="sm"
                isLoading={allocLoading}
                disabled={!allocProductId || allocQty <= 0}
                onClick={async () => {
                  if (!allocProductId) return;
                  try {
                    setAllocLoading(true);
                    const [selection, allocation] = await Promise.all([
                      warehousesApi.selectWarehouse(allocProductId, allocQty),
                      warehousesApi.calculateAllocation(allocProductId, allocQty),
                    ]);
                    setSelectionResult(selection);
                    setAllocResult(allocation);
                  } catch (err: any) {
                    toast.error(err.message || "Failed to calculate allocation");
                  } finally {
                    setAllocLoading(false);
                  }
                }}
              >
                Calculate Allocation
              </Button>
            </div>

            {/* Warehouse Selection Banner (Phase 092) */}
            {selectionResult && (
              <div
                className={`p-3 rounded-lg border text-sm ${
                  selectionResult.is_fully_fulfillable
                    ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                    : selectionResult.requires_multi_warehouse
                    ? "bg-amber-50 border-amber-200 text-amber-900"
                    : "bg-red-50 border-red-200 text-red-900"
                }`}
              >
                <div className="font-semibold flex items-center gap-2">
                  <span>Phase 092 Preferred Warehouse:</span>
                  {selectionResult.is_fully_fulfillable ? (
                    <Badge variant="success">
                      {selectionResult.selected_warehouse_code} (P{selectionResult.selected_warehouse_priority})
                    </Badge>
                  ) : selectionResult.requires_multi_warehouse ? (
                    <Badge variant="warning">Multi-Warehouse Required</Badge>
                  ) : (
                    <Badge variant="destructive">Insufficient Total ATP</Badge>
                  )}
                </div>
                <div className="text-xs mt-1">
                  {selectionResult.is_fully_fulfillable
                    ? `Highest priority facility "${selectionResult.selected_warehouse_name}" has sufficient ATP to fulfill all ${allocQty} units.`
                    : selectionResult.requires_multi_warehouse
                    ? `No single facility can fulfill ${allocQty} units; stock must be split across multiple facilities.`
                    : `Total ATP across all active company facilities is insufficient for ${allocQty} units.`}
                </div>
              </div>
            )}

            {/* Allocation Results Breakdown (Phase 094) */}
            {allocResult && (
              <div className="space-y-3 pt-2 border-t border-border">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold text-slate-700 uppercase">
                    Priority-Ordered Allocation Plan (Phase 094)
                  </div>
                  <div className="text-xs">
                    Allocated: <strong className="text-emerald-700">{allocResult.total_allocated}</strong> / {allocResult.requested_quantity}
                    {allocResult.unallocated_quantity > 0 && (
                      <span className="text-red-600 ml-2 font-semibold">
                        (Unallocated: {allocResult.unallocated_quantity})
                      </span>
                    )}
                  </div>
                </div>

                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-xs">
                    <thead className="bg-slate-50 border-b text-slate-600 font-semibold">
                      <tr>
                        <th className="py-2 px-3 text-left">Priority</th>
                        <th className="py-2 px-3 text-left">Facility</th>
                        <th className="py-2 px-3 text-right">Available (ATP)</th>
                        <th className="py-2 px-3 text-right">Allocated Qty</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {allocResult.allocations.map((a) => (
                        <tr key={a.warehouse_id} className={a.allocated_quantity > 0 ? "bg-emerald-50/40" : ""}>
                          <td className="py-2 px-3 font-mono font-semibold text-slate-700">P{a.priority}</td>
                          <td className="py-2 px-3">
                            <span className="font-semibold text-slate-900">{a.warehouse_code}</span> — {a.warehouse_name}
                          </td>
                          <td className="py-2 px-3 text-right font-medium">{a.available_to_promise}</td>
                          <td className="py-2 px-3 text-right font-bold text-emerald-700">
                            {a.allocated_quantity > 0 ? `+${a.allocated_quantity}` : "0"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Phase 095 Reservation Action */}
                {canMutate && allocResult.total_allocated > 0 && (
                  <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200 mt-3">
                    <div className="text-xs text-slate-600">
                      Commit this allocation as atomic multi-warehouse stock reservations (Phase 095).
                    </div>
                    <Button
                      variant="primary"
                      size="sm"
                      isLoading={isReservingAllocation}
                      className="bg-purple-600 hover:bg-purple-700 text-xs"
                      onClick={async () => {
                        try {
                          setIsReservingAllocation(true);
                          const res = await warehousesApi.reserveAllocation(allocProductId, allocQty);
                          toast.success(`Reserved ${res.total_reserved} units across ${res.reservations.length} facilities.`);
                          setIsAllocationModalOpen(false);
                          loadWarehouses();
                          if (selectedWarehouse) {
                            loadStock(selectedWarehouse.id);
                          }
                        } catch (err: any) {
                          toast.error(err.message || "Failed to reserve allocation");
                        } finally {
                          setIsReservingAllocation(false);
                        }
                      }}
                    >
                      <Lock className="h-3 w-3 mr-1" />
                      <span>Reserve Allocation ({allocResult.total_allocated} units)</span>
                    </Button>
                  </div>
                )}
              </div>
            )}

            <div className="flex justify-end pt-3 border-t border-border">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setIsAllocationModalOpen(false)}
              >
                Close
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </ProtectedRoute>
  );
}
