"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  Building2,
  CheckCircle2,
  Edit2,
  Lock,
  Package,
  Percent,
  Plus,
  PowerOff,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Tag,
  UserCheck,
  Users,
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
import { UnauthorizedState } from "@/components/ui/unauthorized-state";
import {
  customersApi,
  discountGovernanceApi,
  productCategoriesApi,
  productsApi,
} from "@/lib/api";
import { Customer } from "@/types/customer";
import { Product, ProductCategory } from "@/types/product";
import {
  CategoryDiscountCeiling,
  CategoryDiscountCeilingCreateInput,
  CustomerDiscountCeiling,
  CustomerDiscountCeilingCreateInput,
  DiscountConfiguration,
  DiscountConfigurationCreateInput,
  ProductDiscountCeiling,
  ProductDiscountCeilingCreateInput,
  SalesRepAuthorityLimit,
  SalesRepAuthorityLimitCreateInput,
} from "@/types/discountGovernance";

export default function DiscountGovernancePage() {
  const { user } = useAuth();
  const toast = useToast();

  const allowedRoles = ["Admin", "Sales Manager", "Finance", "Sales Representative"];
  const hasAccess =
    user?.roles.some((r) => allowedRoles.includes(r)) || user?.roles.includes("Admin");
  const canMutate =
    user?.roles.some((r) => ["Admin", "Sales Manager", "Finance"].includes(r)) ||
    user?.roles.includes("Admin");

  // Tab State
  const [activeTab, setActiveTab] = useState<
    "configurations" | "customers" | "categories" | "products" | "reps"
  >("configurations");

  // Data States
  const [configurations, setConfigurations] = useState<DiscountConfiguration[]>([]);
  const [customerCeilings, setCustomerCeilings] = useState<CustomerDiscountCeiling[]>([]);
  const [categoryCeilings, setCategoryCeilings] = useState<CategoryDiscountCeiling[]>([]);
  const [productCeilings, setProductCeilings] = useState<ProductDiscountCeiling[]>([]);
  const [salesRepLimits, setSalesRepLimits] = useState<SalesRepAuthorityLimit[]>([]);

  // Lookup Reference Data
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [categories, setCategories] = useState<ProductCategory[]>([]);
  const [products, setProducts] = useState<Product[]>([]);

  // Loading / Error
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Search Filters
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Modal States
  const [isConfigModalOpen, setIsConfigModalOpen] = useState<boolean>(false);
  const [isCustModalOpen, setIsCustModalOpen] = useState<boolean>(false);
  const [isCatModalOpen, setIsCatModalOpen] = useState<boolean>(false);
  const [isProdModalOpen, setIsProdModalOpen] = useState<boolean>(false);
  const [isRepModalOpen, setIsRepModalOpen] = useState<boolean>(false);

  // Form States
  const [configForm, setConfigForm] = useState<DiscountConfigurationCreateInput>({
    name: "",
    description: "",
    default_discount_ceiling: 20,
    is_active: true,
  });

  const [custForm, setCustForm] = useState<CustomerDiscountCeilingCreateInput>({
    customer_id: "",
    max_discount_percentage: 15,
    is_active: true,
  });

  const [catForm, setCatForm] = useState<CategoryDiscountCeilingCreateInput>({
    category_id: "",
    max_discount_percentage: 15,
    is_active: true,
  });

  const [prodForm, setProdForm] = useState<ProductDiscountCeilingCreateInput>({
    product_id: "",
    max_discount_percentage: 10,
    is_active: true,
  });

  const [repForm, setRepForm] = useState<SalesRepAuthorityLimitCreateInput>({
    user_id: "",
    max_authorized_discount: 10,
    is_active: true,
  });

  // Edit Mode state
  const [editingId, setEditingId] = useState<string | null>(null);

  // Load All Data
  const loadData = useCallback(async () => {
    try {
      setError(null);
      const [
        cfgRes,
        custCeilRes,
        catCeilRes,
        prodCeilRes,
        repLimRes,
        custRes,
        catRes,
        prodRes,
      ] = await Promise.all([
        discountGovernanceApi.listConfigurations(),
        discountGovernanceApi.listCustomerCeilings(),
        discountGovernanceApi.listCategoryCeilings(),
        discountGovernanceApi.listProductCeilings(),
        discountGovernanceApi.listSalesRepLimits(),
        customersApi.getAll({ limit: 100 }),
        productCategoriesApi.getAll(),
        productsApi.getAll({ limit: 100 }),
      ]);

      setConfigurations(cfgRes.items);
      setCustomerCeilings(custCeilRes.items);
      setCategoryCeilings(catCeilRes.items);
      setProductCeilings(prodCeilRes.items);
      setSalesRepLimits(repLimRes.items);
      setCustomers(custRes.items);
      setCategories(catRes);
      setProducts(prodRes.items);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load discount governance policies";
      setError(msg);
      toast.error(msg);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [toast]);

  useEffect(() => {
    if (hasAccess) {
      loadData();
    }
  }, [hasAccess, loadData]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadData();
  };

  // ---------------------------------------------------------------------------
  // Action Handlers: Configuration (Phase 101)
  // ---------------------------------------------------------------------------
  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        await discountGovernanceApi.updateConfiguration(editingId, configForm);
        toast.success("Discount configuration updated successfully");
      } else {
        await discountGovernanceApi.createConfiguration(configForm);
        toast.success("Discount configuration created successfully");
      }
      setIsConfigModalOpen(false);
      setEditingId(null);
      loadData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save discount configuration");
    }
  };

  const handleToggleActiveConfig = async (cfg: DiscountConfiguration) => {
    try {
      if (cfg.is_active) {
        await discountGovernanceApi.deleteConfiguration(cfg.id);
        toast.success("Configuration deactivated");
      } else {
        await discountGovernanceApi.updateConfiguration(cfg.id, { is_active: true });
        toast.success("Configuration activated");
      }
      loadData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to change active status");
    }
  };

  // ---------------------------------------------------------------------------
  // Action Handlers: Customer Ceiling (Phase 102)
  // ---------------------------------------------------------------------------
  const handleSaveCustCeiling = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        await discountGovernanceApi.updateCustomerCeiling(editingId, {
          max_discount_percentage: custForm.max_discount_percentage,
          is_active: custForm.is_active,
        });
        toast.success("Customer discount ceiling updated");
      } else {
        await discountGovernanceApi.createCustomerCeiling(custForm);
        toast.success("Customer discount ceiling created");
      }
      setIsCustModalOpen(false);
      setEditingId(null);
      loadData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save customer ceiling");
    }
  };

  const handleToggleActiveCustCeiling = async (item: CustomerDiscountCeiling) => {
    try {
      if (item.is_active) {
        await discountGovernanceApi.deleteCustomerCeiling(item.id);
        toast.success("Customer discount ceiling deactivated");
      } else {
        await discountGovernanceApi.updateCustomerCeiling(item.id, { is_active: true });
        toast.success("Customer discount ceiling activated");
      }
      loadData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update ceiling status");
    }
  };

  // ---------------------------------------------------------------------------
  // Action Handlers: Category Ceiling (Phase 103)
  // ---------------------------------------------------------------------------
  const handleSaveCatCeiling = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        await discountGovernanceApi.updateCategoryCeiling(editingId, {
          max_discount_percentage: catForm.max_discount_percentage,
          is_active: catForm.is_active,
        });
        toast.success("Category discount ceiling updated");
      } else {
        await discountGovernanceApi.createCategoryCeiling(catForm);
        toast.success("Category discount ceiling created");
      }
      setIsCatModalOpen(false);
      setEditingId(null);
      loadData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save category ceiling");
    }
  };

  const handleToggleActiveCatCeiling = async (item: CategoryDiscountCeiling) => {
    try {
      if (item.is_active) {
        await discountGovernanceApi.deleteCategoryCeiling(item.id);
        toast.success("Category discount ceiling deactivated");
      } else {
        await discountGovernanceApi.updateCategoryCeiling(item.id, { is_active: true });
        toast.success("Category discount ceiling activated");
      }
      loadData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update category ceiling");
    }
  };

  // ---------------------------------------------------------------------------
  // Action Handlers: Product Ceiling (Phase 104)
  // ---------------------------------------------------------------------------
  const handleSaveProdCeiling = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        await discountGovernanceApi.updateProductCeiling(editingId, {
          max_discount_percentage: prodForm.max_discount_percentage,
          is_active: prodForm.is_active,
        });
        toast.success("Product discount ceiling updated");
      } else {
        await discountGovernanceApi.createProductCeiling(prodForm);
        toast.success("Product discount ceiling created");
      }
      setIsProdModalOpen(false);
      setEditingId(null);
      loadData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save product ceiling");
    }
  };

  const handleToggleActiveProdCeiling = async (item: ProductDiscountCeiling) => {
    try {
      if (item.is_active) {
        await discountGovernanceApi.deleteProductCeiling(item.id);
        toast.success("Product discount ceiling deactivated");
      } else {
        await discountGovernanceApi.updateProductCeiling(item.id, { is_active: true });
        toast.success("Product discount ceiling activated");
      }
      loadData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update product ceiling");
    }
  };

  // ---------------------------------------------------------------------------
  // Action Handlers: Sales Rep Limit (Phase 105)
  // ---------------------------------------------------------------------------
  const handleSaveRepLimit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Phase 105 strict security check: user cannot modify own limit unless Admin
      if (repForm.user_id === user?.id && !user?.roles.includes("Admin")) {
        toast.error("Sales Representatives are forbidden from configuring or escalating their own discount limits.");
        return;
      }

      if (editingId) {
        await discountGovernanceApi.updateSalesRepLimit(editingId, {
          max_authorized_discount: repForm.max_authorized_discount,
          is_active: repForm.is_active,
        });
        toast.success("Sales rep authority limit updated");
      } else {
        await discountGovernanceApi.createSalesRepLimit(repForm);
        toast.success("Sales rep authority limit created");
      }
      setIsRepModalOpen(false);
      setEditingId(null);
      loadData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save sales rep limit");
    }
  };

  const handleToggleActiveRepLimit = async (item: SalesRepAuthorityLimit) => {
    try {
      if (item.user_id === user?.id && !user?.roles.includes("Admin")) {
        toast.error("You cannot modify your own discount authority limit.");
        return;
      }

      if (item.is_active) {
        await discountGovernanceApi.deleteSalesRepLimit(item.id);
        toast.success("Sales rep authority limit deactivated");
      } else {
        await discountGovernanceApi.updateSalesRepLimit(item.id, { is_active: true });
        toast.success("Sales rep authority limit activated");
      }
      loadData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update sales rep limit");
    }
  };

  // ---------------------------------------------------------------------------
  // Data Table Columns
  // ---------------------------------------------------------------------------
  const configColumns: ColumnDef<DiscountConfiguration>[] = [
    {
      id: "name",
      header: "Policy Name",
      accessorKey: "name",
      cell: (row) => (
        <div>
          <div className="font-medium text-foreground">{row.name}</div>
          <div className="text-xs text-muted-foreground">{row.description || "No description"}</div>
        </div>
      ),
    },
    {
      id: "ceiling",
      header: "Default Ceiling",
      cell: (row) => (
        <span className="font-semibold text-foreground">{Number(row.default_discount_ceiling).toFixed(2)}%</span>
      ),
    },
    {
      id: "status",
      header: "Status",
      cell: (row) => (
        <Badge variant={row.is_active ? "success" : "secondary"}>
          {row.is_active ? "Active" : "Inactive"}
        </Badge>
      ),
    },
    {
      id: "effective",
      header: "Effective Window",
      cell: (row) => (
        <span className="text-xs text-muted-foreground">
          {new Date(row.effective_from).toLocaleDateString()}
          {row.effective_until ? ` - ${new Date(row.effective_until).toLocaleDateString()}` : " (Indefinite)"}
        </span>
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: (row) => (
        <div className="flex items-center space-x-2">
          {canMutate && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setEditingId(row.id);
                  setConfigForm({
                    name: row.name,
                    description: row.description || "",
                    default_discount_ceiling: Number(row.default_discount_ceiling),
                    is_active: row.is_active,
                  });
                  setIsConfigModalOpen(true);
                }}
              >
                <Edit2 className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleToggleActiveConfig(row)}
              >
                {row.is_active ? (
                  <PowerOff className="h-4 w-4 text-destructive" />
                ) : (
                  <CheckCircle2 className="h-4 w-4 text-success" />
                )}
              </Button>
            </>
          )}
        </div>
      ),
    },
  ];

  const customerColumns: ColumnDef<CustomerDiscountCeiling>[] = [
    {
      id: "customer",
      header: "Customer Account",
      cell: (row) => {
        const cust = customers.find((c) => c.id === row.customer_id);
        return (
          <div>
            <div className="font-medium text-foreground">{cust?.name || row.customer_id}</div>
            <div className="text-xs text-muted-foreground">{cust?.customer_code || "Account Code"}</div>
          </div>
        );
      },
    },
    {
      id: "ceiling",
      header: "Max Discount Ceiling",
      cell: (row) => (
        <span className="font-semibold text-foreground">{Number(row.max_discount_percentage).toFixed(2)}%</span>
      ),
    },
    {
      id: "status",
      header: "Status",
      cell: (row) => (
        <Badge variant={row.is_active ? "success" : "secondary"}>
          {row.is_active ? "Active" : "Inactive"}
        </Badge>
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: (row) => (
        <div className="flex items-center space-x-2">
          {canMutate && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setEditingId(row.id);
                  setCustForm({
                    customer_id: row.customer_id,
                    max_discount_percentage: Number(row.max_discount_percentage),
                    is_active: row.is_active,
                  });
                  setIsCustModalOpen(true);
                }}
              >
                <Edit2 className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleToggleActiveCustCeiling(row)}
              >
                {row.is_active ? (
                  <PowerOff className="h-4 w-4 text-destructive" />
                ) : (
                  <CheckCircle2 className="h-4 w-4 text-success" />
                )}
              </Button>
            </>
          )}
        </div>
      ),
    },
  ];

  const categoryColumns: ColumnDef<CategoryDiscountCeiling>[] = [
    {
      id: "category",
      header: "Product Category",
      cell: (row) => {
        const cat = categories.find((c) => c.id === row.category_id);
        return (
          <div>
            <div className="font-medium text-foreground">{cat?.name || row.category_id}</div>
            <div className="text-xs text-muted-foreground">{cat?.code || "Category Code"}</div>
          </div>
        );
      },
    },
    {
      id: "ceiling",
      header: "Max Discount Ceiling",
      cell: (row) => (
        <span className="font-semibold text-foreground">{Number(row.max_discount_percentage).toFixed(2)}%</span>
      ),
    },
    {
      id: "status",
      header: "Status",
      cell: (row) => (
        <Badge variant={row.is_active ? "success" : "secondary"}>
          {row.is_active ? "Active" : "Inactive"}
        </Badge>
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: (row) => (
        <div className="flex items-center space-x-2">
          {canMutate && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setEditingId(row.id);
                  setCatForm({
                    category_id: row.category_id,
                    max_discount_percentage: Number(row.max_discount_percentage),
                    is_active: row.is_active,
                  });
                  setIsCatModalOpen(true);
                }}
              >
                <Edit2 className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleToggleActiveCatCeiling(row)}
              >
                {row.is_active ? (
                  <PowerOff className="h-4 w-4 text-destructive" />
                ) : (
                  <CheckCircle2 className="h-4 w-4 text-success" />
                )}
              </Button>
            </>
          )}
        </div>
      ),
    },
  ];

  const productColumns: ColumnDef<ProductDiscountCeiling>[] = [
    {
      id: "product",
      header: "Product / SKU",
      cell: (row) => {
        const prod = products.find((p) => p.id === row.product_id);
        return (
          <div>
            <div className="font-medium text-foreground">{prod?.name || row.product_id}</div>
            <div className="text-xs text-muted-foreground">{prod?.sku || "SKU Code"}</div>
          </div>
        );
      },
    },
    {
      id: "ceiling",
      header: "Max Discount Ceiling",
      cell: (row) => (
        <span className="font-semibold text-foreground">{Number(row.max_discount_percentage).toFixed(2)}%</span>
      ),
    },
    {
      id: "status",
      header: "Status",
      cell: (row) => (
        <Badge variant={row.is_active ? "success" : "secondary"}>
          {row.is_active ? "Active" : "Inactive"}
        </Badge>
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: (row) => (
        <div className="flex items-center space-x-2">
          {canMutate && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setEditingId(row.id);
                  setProdForm({
                    product_id: row.product_id,
                    max_discount_percentage: Number(row.max_discount_percentage),
                    is_active: row.is_active,
                  });
                  setIsProdModalOpen(true);
                }}
              >
                <Edit2 className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleToggleActiveProdCeiling(row)}
              >
                {row.is_active ? (
                  <PowerOff className="h-4 w-4 text-destructive" />
                ) : (
                  <CheckCircle2 className="h-4 w-4 text-success" />
                )}
              </Button>
            </>
          )}
        </div>
      ),
    },
  ];

  const salesRepColumns: ColumnDef<SalesRepAuthorityLimit>[] = [
    {
      id: "user_id",
      header: "User / Rep ID",
      cell: (row) => (
        <div>
          <div className="font-medium text-foreground">{row.user_id}</div>
          <div className="text-xs text-muted-foreground">
            {row.user_id === user?.id ? "Your Authority Limit" : "Sales Representative"}
          </div>
        </div>
      ),
    },
    {
      id: "limit",
      header: "Max Authorized Discount",
      cell: (row) => (
        <span className="font-semibold text-foreground">{Number(row.max_authorized_discount).toFixed(2)}%</span>
      ),
    },
    {
      id: "status",
      header: "Status",
      cell: (row) => (
        <Badge variant={row.is_active ? "success" : "secondary"}>
          {row.is_active ? "Active" : "Inactive"}
        </Badge>
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: (row) => {
        const isSelf = row.user_id === user?.id && !user?.roles.includes("Admin");
        return (
          <div className="flex items-center space-x-2">
            {canMutate && !isSelf && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setEditingId(row.id);
                    setRepForm({
                      user_id: row.user_id,
                      max_authorized_discount: Number(row.max_authorized_discount),
                      is_active: row.is_active,
                    });
                    setIsRepModalOpen(true);
                  }}
                >
                  <Edit2 className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleToggleActiveRepLimit(row)}
                >
                  {row.is_active ? (
                    <PowerOff className="h-4 w-4 text-destructive" />
                  ) : (
                    <CheckCircle2 className="h-4 w-4 text-success" />
                  )}
                </Button>
              </>
            )}
            {isSelf && (
              <span className="text-xs text-muted-foreground flex items-center">
                <Lock className="h-3 w-3 mr-1" /> Self-edit locked
              </span>
            )}
          </div>
        );
      },
    },
  ];

  if (!hasAccess) {
    return (
      <ProtectedRoute>
        <UnauthorizedState message="Discount governance policies are restricted to Sales Representatives, Managers, Finance officers, and Administrators." />
      </ProtectedRoute>
    );
  }

  if (isLoading) {
    return (
      <ProtectedRoute>
        <LoadingState message="Loading discount governance policies..." />
      </ProtectedRoute>
    );
  }

  if (error) {
    return (
      <ProtectedRoute>
        <ErrorState message={error} onRetry={loadData} />
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <Percent className="h-6 w-6 text-primary" />
              Discount Governance
            </h1>
            <p className="text-sm text-muted-foreground">
              Company baseline discount ceilings, category & product caps, and sales rep limits (G21: Phases 101–105).
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isRefreshing}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            {canMutate && activeTab === "configurations" && (
              <Button
                size="sm"
                onClick={() => {
                  setEditingId(null);
                  setConfigForm({
                    name: "",
                    description: "",
                    default_discount_ceiling: 20,
                    is_active: true,
                  });
                  setIsConfigModalOpen(true);
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                New Configuration
              </Button>
            )}
            {canMutate && activeTab === "customers" && (
              <Button
                size="sm"
                onClick={() => {
                  setEditingId(null);
                  setCustForm({
                    customer_id: customers[0]?.id || "",
                    max_discount_percentage: 15,
                    is_active: true,
                  });
                  setIsCustModalOpen(true);
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                Set Customer Ceiling
              </Button>
            )}
            {canMutate && activeTab === "categories" && (
              <Button
                size="sm"
                onClick={() => {
                  setEditingId(null);
                  setCatForm({
                    category_id: categories[0]?.id || "",
                    max_discount_percentage: 15,
                    is_active: true,
                  });
                  setIsCatModalOpen(true);
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                Set Category Ceiling
              </Button>
            )}
            {canMutate && activeTab === "products" && (
              <Button
                size="sm"
                onClick={() => {
                  setEditingId(null);
                  setProdForm({
                    product_id: products[0]?.id || "",
                    max_discount_percentage: 10,
                    is_active: true,
                  });
                  setIsProdModalOpen(true);
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                Set Product Ceiling
              </Button>
            )}
            {canMutate && activeTab === "reps" && (
              <Button
                size="sm"
                onClick={() => {
                  setEditingId(null);
                  setRepForm({
                    user_id: "",
                    max_authorized_discount: 10,
                    is_active: true,
                  });
                  setIsRepModalOpen(true);
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                Set Rep Limit
              </Button>
            )}
          </div>
        </div>

        {/* Phase Summary Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card>
            <CardHeader className="py-3">
              <CardDescription className="flex items-center gap-1.5 text-xs">
                <Building2 className="h-3.5 w-3.5 text-primary" />
                Phase 101: Configurations
              </CardDescription>
              <CardTitle className="text-xl font-bold">{configurations.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="py-3">
              <CardDescription className="flex items-center gap-1.5 text-xs">
                <Users className="h-3.5 w-3.5 text-info" />
                Phase 102: Customer Caps
              </CardDescription>
              <CardTitle className="text-xl font-bold">{customerCeilings.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="py-3">
              <CardDescription className="flex items-center gap-1.5 text-xs">
                <Tag className="h-3.5 w-3.5 text-warning" />
                Phase 103: Category Caps
              </CardDescription>
              <CardTitle className="text-xl font-bold">{categoryCeilings.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="py-3">
              <CardDescription className="flex items-center gap-1.5 text-xs">
                <Package className="h-3.5 w-3.5 text-success" />
                Phase 104: Product Caps
              </CardDescription>
              <CardTitle className="text-xl font-bold">{productCeilings.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="py-3">
              <CardDescription className="flex items-center gap-1.5 text-xs">
                <UserCheck className="h-3.5 w-3.5 text-purple-500" />
                Phase 105: Rep Limits
              </CardDescription>
              <CardTitle className="text-xl font-bold">{salesRepLimits.length}</CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-border space-x-4">
          <button
            onClick={() => setActiveTab("configurations")}
            className={`pb-2 px-1 font-medium text-sm flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === "configurations"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Building2 className="h-4 w-4" />
            Configurations
          </button>
          <button
            onClick={() => setActiveTab("customers")}
            className={`pb-2 px-1 font-medium text-sm flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === "customers"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Users className="h-4 w-4" />
            Customer Ceilings
          </button>
          <button
            onClick={() => setActiveTab("categories")}
            className={`pb-2 px-1 font-medium text-sm flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === "categories"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Tag className="h-4 w-4" />
            Category Ceilings
          </button>
          <button
            onClick={() => setActiveTab("products")}
            className={`pb-2 px-1 font-medium text-sm flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === "products"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Package className="h-4 w-4" />
            Product Ceilings
          </button>
          <button
            onClick={() => setActiveTab("reps")}
            className={`pb-2 px-1 font-medium text-sm flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === "reps"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <UserCheck className="h-4 w-4" />
            Sales Rep Authority
          </button>
        </div>

        {/* Tab 1: Configurations */}
        {activeTab === "configurations" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Company Baseline Configurations</CardTitle>
              <CardDescription>
                Phase 101: Organization-wide default discount ceilings and governance rules.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={configColumns}
                data={configurations}
                keyExtractor={(item) => item.id}
                emptyTitle="No Configurations Found"
                emptyDescription="No company discount configuration exists yet."
              />
            </CardContent>
          </Card>
        )}

        {/* Tab 2: Customer Ceilings */}
        {activeTab === "customers" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Customer-Specific Discount Ceilings</CardTitle>
              <CardDescription>
                Phase 102: Account-specific discount percentage caps. Partial unique index protects single active record.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={customerColumns}
                data={customerCeilings}
                keyExtractor={(item) => item.id}
                emptyTitle="No Customer Ceilings Found"
                emptyDescription="No customer-specific discount caps have been established."
              />
            </CardContent>
          </Card>
        )}

        {/* Tab 3: Category Ceilings */}
        {activeTab === "categories" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Category Discount Ceilings</CardTitle>
              <CardDescription>
                Phase 103: Category-level discount percentage caps. Prevents excessive discounting across product lines.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={categoryColumns}
                data={categoryCeilings}
                keyExtractor={(item) => item.id}
                emptyTitle="No Category Ceilings Found"
                emptyDescription="No product category discount caps have been established."
              />
            </CardContent>
          </Card>
        )}

        {/* Tab 4: Product Ceilings */}
        {activeTab === "products" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Product / SKU Discount Ceilings</CardTitle>
              <CardDescription>
                Phase 104: SKU-level maximum discount limits. Protects margin on high-cost or high-demand hardware.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={productColumns}
                data={productCeilings}
                keyExtractor={(item) => item.id}
                emptyTitle="No Product Ceilings Found"
                emptyDescription="No SKU-specific discount caps have been established."
              />
            </CardContent>
          </Card>
        )}

        {/* Tab 5: Sales Rep Limits */}
        {activeTab === "reps" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Sales Representative Authority Limits</CardTitle>
              <CardDescription>
                Phase 105: User-level maximum discretionary discount limits. Self-modification is strictly forbidden.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={salesRepColumns}
                data={salesRepLimits}
                keyExtractor={(item) => item.id}
                emptyTitle="No Rep Limits Found"
                emptyDescription="No sales rep authority limits have been established."
              />
            </CardContent>
          </Card>
        )}

        {/* Modal 1: Configuration Form */}
        <Modal
          isOpen={isConfigModalOpen}
          onClose={() => setIsConfigModalOpen(false)}
          title={editingId ? "Edit Configuration" : "New Discount Configuration"}
          description="Define default organization discount ceiling percentage."
        >
          <form onSubmit={handleSaveConfig} className="space-y-4">
            <FormItem>
              <FormLabel>Configuration Name</FormLabel>
              <Input
                required
                value={configForm.name}
                onChange={(e) => setConfigForm({ ...configForm, name: e.target.value })}
                placeholder="e.g. Standard Corporate Discount Policy"
              />
            </FormItem>
            <FormItem>
              <FormLabel>Description</FormLabel>
              <Input
                value={configForm.description || ""}
                onChange={(e) => setConfigForm({ ...configForm, description: e.target.value })}
                placeholder="Optional policy scope notes"
              />
            </FormItem>
            <FormItem>
              <FormLabel>Default Ceiling Percentage (0 - 100%)</FormLabel>
              <Input
                required
                type="number"
                min="0"
                max="100"
                step="0.01"
                value={configForm.default_discount_ceiling}
                onChange={(e) =>
                  setConfigForm({ ...configForm, default_discount_ceiling: parseFloat(e.target.value) || 0 })
                }
              />
            </FormItem>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setIsConfigModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Save Policy</Button>
            </div>
          </form>
        </Modal>

        {/* Modal 2: Customer Ceiling Form */}
        <Modal
          isOpen={isCustModalOpen}
          onClose={() => setIsCustModalOpen(false)}
          title={editingId ? "Edit Customer Ceiling" : "New Customer Discount Ceiling"}
          description="Establish specific ceiling percentage for an account."
        >
          <form onSubmit={handleSaveCustCeiling} className="space-y-4">
            {!editingId && (
              <FormItem>
                <FormLabel>Customer Account</FormLabel>
                <Select
                  value={custForm.customer_id}
                  onChange={(e) => setCustForm({ ...custForm, customer_id: e.target.value })}
                >
                  <option value="">Select a Customer...</option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.customer_code})
                    </option>
                  ))}
                </Select>
              </FormItem>
            )}
            <FormItem>
              <FormLabel>Max Discount Percentage (0 - 100%)</FormLabel>
              <Input
                required
                type="number"
                min="0"
                max="100"
                step="0.01"
                value={custForm.max_discount_percentage}
                onChange={(e) =>
                  setCustForm({ ...custForm, max_discount_percentage: parseFloat(e.target.value) || 0 })
                }
              />
            </FormItem>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setIsCustModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Save Ceiling</Button>
            </div>
          </form>
        </Modal>

        {/* Modal 3: Category Ceiling Form */}
        <Modal
          isOpen={isCatModalOpen}
          onClose={() => setIsCatModalOpen(false)}
          title={editingId ? "Edit Category Ceiling" : "New Category Discount Ceiling"}
          description="Establish maximum discount percentage for a product category."
        >
          <form onSubmit={handleSaveCatCeiling} className="space-y-4">
            {!editingId && (
              <FormItem>
                <FormLabel>Product Category</FormLabel>
                <Select
                  value={catForm.category_id}
                  onChange={(e) => setCatForm({ ...catForm, category_id: e.target.value })}
                >
                  <option value="">Select a Category...</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.code})
                    </option>
                  ))}
                </Select>
              </FormItem>
            )}
            <FormItem>
              <FormLabel>Max Discount Percentage (0 - 100%)</FormLabel>
              <Input
                required
                type="number"
                min="0"
                max="100"
                step="0.01"
                value={catForm.max_discount_percentage}
                onChange={(e) =>
                  setCatForm({ ...catForm, max_discount_percentage: parseFloat(e.target.value) || 0 })
                }
              />
            </FormItem>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setIsCatModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Save Ceiling</Button>
            </div>
          </form>
        </Modal>

        {/* Modal 4: Product Ceiling Form */}
        <Modal
          isOpen={isProdModalOpen}
          onClose={() => setIsProdModalOpen(false)}
          title={editingId ? "Edit Product Ceiling" : "New Product Discount Ceiling"}
          description="Establish maximum discount percentage for a specific SKU."
        >
          <form onSubmit={handleSaveProdCeiling} className="space-y-4">
            {!editingId && (
              <FormItem>
                <FormLabel>Product / SKU</FormLabel>
                <Select
                  value={prodForm.product_id}
                  onChange={(e) => setProdForm({ ...prodForm, product_id: e.target.value })}
                >
                  <option value="">Select a Product...</option>
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.sku})
                    </option>
                  ))}
                </Select>
              </FormItem>
            )}
            <FormItem>
              <FormLabel>Max Discount Percentage (0 - 100%)</FormLabel>
              <Input
                required
                type="number"
                min="0"
                max="100"
                step="0.01"
                value={prodForm.max_discount_percentage}
                onChange={(e) =>
                  setProdForm({ ...prodForm, max_discount_percentage: parseFloat(e.target.value) || 0 })
                }
              />
            </FormItem>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setIsProdModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Save Ceiling</Button>
            </div>
          </form>
        </Modal>

        {/* Modal 5: Sales Rep Limit Form */}
        <Modal
          isOpen={isRepModalOpen}
          onClose={() => setIsRepModalOpen(false)}
          title={editingId ? "Edit Sales Rep Limit" : "New Sales Rep Authority Limit"}
          description="Assign maximum discretionary discount authority percentage."
        >
          <form onSubmit={handleSaveRepLimit} className="space-y-4">
            {!editingId && (
              <FormItem>
                <FormLabel>Target User / Sales Rep ID</FormLabel>
                <Input
                  required
                  value={repForm.user_id}
                  onChange={(e) => setRepForm({ ...repForm, user_id: e.target.value })}
                  placeholder="Paste User UUID (e.g. 52034832-7be7-4fe6-...)"
                />
              </FormItem>
            )}
            <FormItem>
              <FormLabel>Max Authorized Discount (0 - 100%)</FormLabel>
              <Input
                required
                type="number"
                min="0"
                max="100"
                step="0.01"
                value={repForm.max_authorized_discount}
                onChange={(e) =>
                  setRepForm({ ...repForm, max_authorized_discount: parseFloat(e.target.value) || 0 })
                }
              />
            </FormItem>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setIsRepModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Save Limit</Button>
            </div>
          </form>
        </Modal>
      </div>
    </ProtectedRoute>
  );
}
