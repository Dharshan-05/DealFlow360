"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  Building2,
  Calculator,
  CheckCircle2,
  Edit2,
  Landmark,
  Lock,
  Package,
  Percent,
  Plus,
  PowerOff,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Tag,
  TrendingUp,
  UserCheck,
  Users,
  BarChart3,
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
  CustomerDiscountAnalysisResponse,
  CustomerDiscountCeiling,
  CustomerDiscountCeilingCreateInput,
  DiscountConfiguration,
  DiscountConfigurationCreateInput,
  DiscountPolicyEvaluationResponse,
  DiscountRecommendationRequest,
  DiscountRecommendationResponse,
  DiscountValidationRequest,
  FinanceAuthorityLimit,
  FinanceAuthorityLimitCreateInput,
  HistoricalDiscountAnalysisResponse,
  ManagerAuthorityLimit,
  ManagerAuthorityLimitCreateInput,
  MarginProtectionResponse,
  MaximumSafeDiscountResponse,
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
    | "configurations"
    | "customers"
    | "categories"
    | "products"
    | "reps"
    | "managers"
    | "finance"
    | "validator"
    | "recommendation"
    | "analytics"
  >("configurations");

  // Data States
  const [configurations, setConfigurations] = useState<DiscountConfiguration[]>([]);
  const [customerCeilings, setCustomerCeilings] = useState<CustomerDiscountCeiling[]>([]);
  const [categoryCeilings, setCategoryCeilings] = useState<CategoryDiscountCeiling[]>([]);
  const [productCeilings, setProductCeilings] = useState<ProductDiscountCeiling[]>([]);
  const [salesRepLimits, setSalesRepLimits] = useState<SalesRepAuthorityLimit[]>([]);
  const [managerLimits, setManagerLimits] = useState<ManagerAuthorityLimit[]>([]);
  const [financeLimits, setFinanceLimits] = useState<FinanceAuthorityLimit[]>([]);

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
  const [isMgrModalOpen, setIsMgrModalOpen] = useState<boolean>(false);
  const [isFinModalOpen, setIsFinModalOpen] = useState<boolean>(false);

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

  const [mgrForm, setMgrForm] = useState<ManagerAuthorityLimitCreateInput>({
    user_id: "",
    max_authorized_discount: 25,
    is_active: true,
  });

  const [finForm, setFinForm] = useState<FinanceAuthorityLimitCreateInput>({
    user_id: "",
    max_authorized_discount: 35,
    is_active: true,
  });

  // Validator Simulation State (Phases 108–110)
  const [validationRequest, setValidationRequest] = useState<DiscountValidationRequest>({
    customer_id: "",
    product_id: "",
    proposed_discount: 12,
  });
  const [validationResult, setValidationResult] = useState<DiscountPolicyEvaluationResponse | null>(null);
  const [isValidating, setIsValidating] = useState<boolean>(false);

  // G23 Intelligence States (Phases 111–115)
  const [intelCustomerId, setIntelCustomerId] = useState<string>("");
  const [intelProductId, setIntelProductId] = useState<string>("");
  const [intelMinMargin, setIntelMinMargin] = useState<number>(15);
  const [intelBenchmark, setIntelBenchmark] = useState<number | undefined>(undefined);
  const [recommendationResult, setRecommendationResult] = useState<DiscountRecommendationResponse | null>(null);
  const [isCalculatingRec, setIsCalculatingRec] = useState<boolean>(false);

  // Analytics States (Phases 114 & 115)
  const [historyResult, setHistoryResult] = useState<HistoricalDiscountAnalysisResponse | null>(null);
  const [customerAnalysisResult, setCustomerAnalysisResult] = useState<CustomerDiscountAnalysisResponse | null>(null);
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState<boolean>(false);

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
        mgrLimRes,
        finLimRes,
        custRes,
        catRes,
        prodRes,
      ] = await Promise.all([
        discountGovernanceApi.listConfigurations(),
        discountGovernanceApi.listCustomerCeilings(),
        discountGovernanceApi.listCategoryCeilings(),
        discountGovernanceApi.listProductCeilings(),
        discountGovernanceApi.listSalesRepLimits(),
        discountGovernanceApi.listManagerLimits(),
        discountGovernanceApi.listFinanceLimits(),
        customersApi.getAll({ limit: 100 }),
        productCategoriesApi.getAll(),
        productsApi.getAll({ limit: 100 }),
      ]);

      setConfigurations(cfgRes.items);
      setCustomerCeilings(custCeilRes.items);
      setCategoryCeilings(catCeilRes.items);
      setProductCeilings(prodCeilRes.items);
      setSalesRepLimits(repLimRes.items);
      setManagerLimits(mgrLimRes.items);
      setFinanceLimits(finLimRes.items);
      setCustomers(custRes.items);
      setCategories(catRes);
      setProducts(prodRes.items);

      // Default validation request and intelligence selections
      if (custRes.items.length > 0 && prodRes.items.length > 0) {
        setValidationRequest((prev) => ({
          ...prev,
          customer_id: prev.customer_id || custRes.items[0].id,
          product_id: prev.product_id || prodRes.items[0].id,
        }));
        setIntelCustomerId((prev) => prev || custRes.items[0].id);
        setIntelProductId((prev) => prev || prodRes.items[0].id);
      }
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
  // Action Handlers: Manager Limit (Phase 106)
  // ---------------------------------------------------------------------------
  const handleSaveMgrLimit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (mgrForm.user_id === user?.id && !user?.roles.includes("Admin")) {
        toast.error("Users cannot assign or escalate their own discount limits.");
        return;
      }

      if (editingId) {
        await discountGovernanceApi.updateManagerLimit(editingId, {
          max_authorized_discount: mgrForm.max_authorized_discount,
          is_active: mgrForm.is_active,
        });
        toast.success("Manager authority limit updated");
      } else {
        await discountGovernanceApi.createManagerLimit(mgrForm);
        toast.success("Manager authority limit created");
      }
      setIsMgrModalOpen(false);
      setEditingId(null);
      loadData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save manager limit");
    }
  };

  const handleToggleActiveMgrLimit = async (item: ManagerAuthorityLimit) => {
    try {
      if (item.user_id === user?.id && !user?.roles.includes("Admin")) {
        toast.error("You cannot modify your own discount authority limit.");
        return;
      }

      if (item.is_active) {
        await discountGovernanceApi.deleteManagerLimit(item.id);
        toast.success("Manager authority limit deactivated");
      } else {
        await discountGovernanceApi.updateManagerLimit(item.id, { is_active: true });
        toast.success("Manager authority limit activated");
      }
      loadData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update manager limit");
    }
  };

  // ---------------------------------------------------------------------------
  // Action Handlers: Finance Limit (Phase 107)
  // ---------------------------------------------------------------------------
  const handleSaveFinLimit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (finForm.user_id === user?.id && !user?.roles.includes("Admin")) {
        toast.error("Users cannot assign or escalate their own discount limits.");
        return;
      }

      if (editingId) {
        await discountGovernanceApi.updateFinanceLimit(editingId, {
          max_authorized_discount: finForm.max_authorized_discount,
          is_active: finForm.is_active,
        });
        toast.success("Finance authority limit updated");
      } else {
        await discountGovernanceApi.createFinanceLimit(finForm);
        toast.success("Finance authority limit created");
      }
      setIsFinModalOpen(false);
      setEditingId(null);
      loadData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save finance limit");
    }
  };

  const handleToggleActiveFinLimit = async (item: FinanceAuthorityLimit) => {
    try {
      if (item.user_id === user?.id && !user?.roles.includes("Admin")) {
        toast.error("You cannot modify your own discount authority limit.");
        return;
      }

      if (item.is_active) {
        await discountGovernanceApi.deleteFinanceLimit(item.id);
        toast.success("Finance authority limit deactivated");
      } else {
        await discountGovernanceApi.updateFinanceLimit(item.id, { is_active: true });
        toast.success("Finance authority limit activated");
      }
      loadData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update finance limit");
    }
  };

  // ---------------------------------------------------------------------------
  // Action Handlers: Discount Policy Validator (Phases 108–110)
  // ---------------------------------------------------------------------------
  const handleValidateDiscount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validationRequest.customer_id || !validationRequest.product_id) {
      toast.error("Please select a customer and a product for policy validation.");
      return;
    }
    try {
      setIsValidating(true);
      const res = await discountGovernanceApi.validateDiscount(validationRequest);
      setValidationResult(res);
      if (res.allowed) {
        toast.success("Proposed discount is compliant with all ceilings and authority limits!");
      } else {
        toast.error(`Discount policy violations detected (${res.violations.length} violation${res.violations.length > 1 ? "s" : ""})`);
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Policy validation failed");
    } finally {
      setIsValidating(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Action Handlers: Discount Intelligence & Recommendation (Phases 111–113)
  // ---------------------------------------------------------------------------
  const handleCalculateRecommendation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!intelCustomerId || !intelProductId) {
      toast.error("Please select a customer and product for discount recommendation.");
      return;
    }
    try {
      setIsCalculatingRec(true);
      const res = await discountGovernanceApi.getRecommendedDiscount({
        customer_id: intelCustomerId,
        product_id: intelProductId,
        min_margin_percentage: intelMinMargin,
        benchmark_discount: intelBenchmark || undefined,
      });
      setRecommendationResult(res);
      toast.success(`Recommended Discount: ${Number(res.recommended_discount).toFixed(2)}% (${res.reason_code})`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to calculate recommendation");
    } finally {
      setIsCalculatingRec(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Action Handlers: Historical & Customer Discount Analytics (Phases 114–115)
  // ---------------------------------------------------------------------------
  const handleLoadAnalytics = async () => {
    try {
      setIsLoadingAnalytics(true);
      const [histRes, custRes] = await Promise.all([
        discountGovernanceApi.getHistoricalDiscountAnalysis({
          customer_id: intelCustomerId || undefined,
          product_id: intelProductId || undefined,
        }),
        intelCustomerId
          ? discountGovernanceApi.getCustomerDiscountAnalysis(intelCustomerId)
          : Promise.resolve(null),
      ]);
      setHistoryResult(histRes);
      setCustomerAnalysisResult(custRes);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load discount analytics");
    } finally {
      setIsLoadingAnalytics(false);
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

  const managerColumns: ColumnDef<ManagerAuthorityLimit>[] = [
    {
      id: "user_id",
      header: "User / Manager ID",
      cell: (row) => (
        <div>
          <div className="font-medium text-foreground">{row.user_id}</div>
          <div className="text-xs text-muted-foreground">
            {row.user_id === user?.id ? "Your Authority Limit" : "Sales Manager"}
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
                    setMgrForm({
                      user_id: row.user_id,
                      max_authorized_discount: Number(row.max_authorized_discount),
                      is_active: row.is_active,
                    });
                    setIsMgrModalOpen(true);
                  }}
                >
                  <Edit2 className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleToggleActiveMgrLimit(row)}
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

  const financeColumns: ColumnDef<FinanceAuthorityLimit>[] = [
    {
      id: "user_id",
      header: "User / Finance Officer ID",
      cell: (row) => (
        <div>
          <div className="font-medium text-foreground">{row.user_id}</div>
          <div className="text-xs text-muted-foreground">
            {row.user_id === user?.id ? "Your Authority Limit" : "Finance Officer"}
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
                    setFinForm({
                      user_id: row.user_id,
                      max_authorized_discount: Number(row.max_authorized_discount),
                      is_active: row.is_active,
                    });
                    setIsFinModalOpen(true);
                  }}
                >
                  <Edit2 className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleToggleActiveFinLimit(row)}
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
            {canMutate && activeTab === "managers" && (
              <Button
                size="sm"
                onClick={() => {
                  setEditingId(null);
                  setMgrForm({
                    user_id: "",
                    max_authorized_discount: 25,
                    is_active: true,
                  });
                  setIsMgrModalOpen(true);
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                Set Manager Limit
              </Button>
            )}
            {canMutate && activeTab === "finance" && (
              <Button
                size="sm"
                onClick={() => {
                  setEditingId(null);
                  setFinForm({
                    user_id: "",
                    max_authorized_discount: 35,
                    is_active: true,
                  });
                  setIsFinModalOpen(true);
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                Set Finance Limit
              </Button>
            )}
          </div>
        </div>

        {/* Phase Summary Metric Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          <Card>
            <CardHeader className="py-2.5 px-3">
              <CardDescription className="flex items-center gap-1 text-[11px]">
                <Building2 className="h-3 w-3 text-primary" />
                Baseline Ceilings
              </CardDescription>
              <CardTitle className="text-lg font-bold">{configurations.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="py-2.5 px-3">
              <CardDescription className="flex items-center gap-1 text-[11px]">
                <Users className="h-3 w-3 text-info" />
                Customer Caps
              </CardDescription>
              <CardTitle className="text-lg font-bold">{customerCeilings.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="py-2.5 px-3">
              <CardDescription className="flex items-center gap-1 text-[11px]">
                <Tag className="h-3 w-3 text-warning" />
                Category Caps
              </CardDescription>
              <CardTitle className="text-lg font-bold">{categoryCeilings.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="py-2.5 px-3">
              <CardDescription className="flex items-center gap-1 text-[11px]">
                <Package className="h-3 w-3 text-success" />
                Product Caps
              </CardDescription>
              <CardTitle className="text-lg font-bold">{productCeilings.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="py-2.5 px-3">
              <CardDescription className="flex items-center gap-1 text-[11px]">
                <UserCheck className="h-3 w-3 text-purple-500" />
                Sales Reps
              </CardDescription>
              <CardTitle className="text-lg font-bold">{salesRepLimits.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="py-2.5 px-3">
              <CardDescription className="flex items-center gap-1 text-[11px]">
                <ShieldCheck className="h-3 w-3 text-blue-500" />
                Managers
              </CardDescription>
              <CardTitle className="text-lg font-bold">{managerLimits.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="py-2.5 px-3">
              <CardDescription className="flex items-center gap-1 text-[11px]">
                <Landmark className="h-3 w-3 text-emerald-500" />
                Finance Limits
              </CardDescription>
              <CardTitle className="text-lg font-bold">{financeLimits.length}</CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-border space-x-3 overflow-x-auto">
          <button
            onClick={() => setActiveTab("configurations")}
            className={`pb-2 px-1 font-medium text-sm flex items-center gap-1.5 whitespace-nowrap border-b-2 transition-colors ${
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
            className={`pb-2 px-1 font-medium text-sm flex items-center gap-1.5 whitespace-nowrap border-b-2 transition-colors ${
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
            className={`pb-2 px-1 font-medium text-sm flex items-center gap-1.5 whitespace-nowrap border-b-2 transition-colors ${
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
            className={`pb-2 px-1 font-medium text-sm flex items-center gap-1.5 whitespace-nowrap border-b-2 transition-colors ${
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
            className={`pb-2 px-1 font-medium text-sm flex items-center gap-1.5 whitespace-nowrap border-b-2 transition-colors ${
              activeTab === "reps"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <UserCheck className="h-4 w-4" />
            Rep Authority
          </button>
          <button
            onClick={() => setActiveTab("managers")}
            className={`pb-2 px-1 font-medium text-sm flex items-center gap-1.5 whitespace-nowrap border-b-2 transition-colors ${
              activeTab === "managers"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <ShieldCheck className="h-4 w-4" />
            Manager Authority
          </button>
          <button
            onClick={() => setActiveTab("finance")}
            className={`pb-2 px-1 font-medium text-sm flex items-center gap-1.5 whitespace-nowrap border-b-2 transition-colors ${
              activeTab === "finance"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Landmark className="h-4 w-4" />
            Finance Authority
          </button>
          <button
            onClick={() => setActiveTab("validator")}
            className={`pb-2 px-1 font-medium text-sm flex items-center gap-1.5 whitespace-nowrap border-b-2 transition-colors ${
              activeTab === "validator"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Calculator className="h-4 w-4 text-warning" />
            Policy Engine Validator
          </button>
          <button
            onClick={() => setActiveTab("recommendation")}
            className={`pb-2 px-1 font-medium text-sm flex items-center gap-1.5 whitespace-nowrap border-b-2 transition-colors ${
              activeTab === "recommendation"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Sparkles className="h-4 w-4 text-primary" />
            Discount Intelligence
          </button>
          <button
            onClick={() => {
              setActiveTab("analytics");
              handleLoadAnalytics();
            }}
            className={`pb-2 px-1 font-medium text-sm flex items-center gap-1.5 whitespace-nowrap border-b-2 transition-colors ${
              activeTab === "analytics"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <BarChart3 className="h-4 w-4 text-emerald-500" />
            Historical Analytics
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
              <CardTitle className="text-lg">Customer Discount Ceilings</CardTitle>
              <CardDescription>
                Phase 102: Account-specific discount caps overriding global baselines.
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
                Phase 103: Product family caps to protect low-margin product lines.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={categoryColumns}
                data={categoryCeilings}
                keyExtractor={(item) => item.id}
                emptyTitle="No Category Ceilings Found"
                emptyDescription="No category discount ceilings have been established."
              />
            </CardContent>
          </Card>
        )}

        {/* Tab 4: Product Ceilings */}
        {activeTab === "products" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Product Discount Ceilings</CardTitle>
              <CardDescription>
                Phase 104: SKU-level hard discount limits for high-cost or key items.
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
                Phase 105: User-level maximum discretionary discount limits for Sales Reps.
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

        {/* Tab 6: Manager Authority Limits (Phase 106) */}
        {activeTab === "managers" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Sales Manager Authority Limits</CardTitle>
              <CardDescription>
                Phase 106: Authorized discount approval and granting limits for Sales Managers.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={managerColumns}
                data={managerLimits}
                keyExtractor={(item) => item.id}
                emptyTitle="No Manager Limits Found"
                emptyDescription="No manager authority limits have been established."
              />
            </CardContent>
          </Card>
        )}

        {/* Tab 7: Finance Authority Limits (Phase 107) */}
        {activeTab === "finance" && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Finance Authority Limits</CardTitle>
              <CardDescription>
                Phase 107: Discretionary authority limits for Finance officers. Sales Reps cannot configure these limits.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={financeColumns}
                data={financeLimits}
                keyExtractor={(item) => item.id}
                emptyTitle="No Finance Limits Found"
                emptyDescription="No finance authority limits have been established."
              />
            </CardContent>
          </Card>
        )}

        {/* Tab 8: Discount Policy Engine & Validator (Phases 108–110) */}
        {activeTab === "validator" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Input Simulation Panel */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Calculator className="h-5 w-5 text-primary" />
                  Discount Evaluation Engine
                </CardTitle>
                <CardDescription>
                  Simulate deterministic policy compliance across all active ceilings and your role authority.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleValidateDiscount} className="space-y-4">
                  <FormItem>
                    <FormLabel>Customer Account</FormLabel>
                    <Select
                      value={validationRequest.customer_id}
                      onChange={(e) =>
                        setValidationRequest({ ...validationRequest, customer_id: e.target.value })
                      }
                      required
                    >
                      <option value="">Select Customer...</option>
                      {customers.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name} ({c.customer_code})
                        </option>
                      ))}
                    </Select>
                  </FormItem>

                  <FormItem>
                    <FormLabel>Target Product</FormLabel>
                    <Select
                      value={validationRequest.product_id}
                      onChange={(e) =>
                        setValidationRequest({ ...validationRequest, product_id: e.target.value })
                      }
                      required
                    >
                      <option value="">Select Product...</option>
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({p.sku})
                        </option>
                      ))}
                    </Select>
                  </FormItem>

                  <FormItem>
                    <FormLabel>Proposed Discount (%)</FormLabel>
                    <Input
                      type="number"
                      min="0"
                      max="100"
                      step="0.01"
                      required
                      value={validationRequest.proposed_discount}
                      onChange={(e) =>
                        setValidationRequest({
                          ...validationRequest,
                          proposed_discount: parseFloat(e.target.value) || 0,
                        })
                      }
                    />
                  </FormItem>

                  <Button type="submit" className="w-full" disabled={isValidating}>
                    {isValidating ? "Evaluating..." : "Run Policy Evaluation"}
                  </Button>
                </form>
              </CardContent>
            </Card>

            {/* Results Panel */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="text-base flex items-center justify-between">
                  <span>Policy Compliance Verdict</span>
                  {validationResult && (
                    <Badge variant={validationResult.allowed ? "success" : "destructive"}>
                      {validationResult.allowed ? "COMPLIANT / ALLOWED" : "POLICY VIOLATION DETECTED"}
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription>
                  Real-time deterministic policy breakdown evaluated at unified UTC timestamp.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {!validationResult ? (
                  <div className="text-center py-12 text-muted-foreground text-sm">
                    Select a customer, product, and proposed discount on the left to evaluate policy compliance.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Summary Metrics */}
                    <div className="grid grid-cols-3 gap-3 p-3 bg-muted/40 rounded-lg">
                      <div>
                        <div className="text-xs text-muted-foreground">Proposed Discount</div>
                        <div className="text-lg font-bold text-foreground">
                          {Number(validationResult.proposed_discount).toFixed(2)}%
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground">Governing Ceiling (MIN)</div>
                        <div className="text-lg font-bold text-foreground">
                          {Number(validationResult.effective_ceiling).toFixed(2)}%
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground">
                          Your Limit ({validationResult.actor_role || "User"})
                        </div>
                        <div className="text-lg font-bold text-foreground">
                          {validationResult.actor_authority_limit !== null
                            ? `${Number(validationResult.actor_authority_limit).toFixed(2)}%`
                            : "Unlimited"}
                        </div>
                      </div>
                    </div>

                    {/* Violations List */}
                    {validationResult.violations.length > 0 ? (
                      <div className="space-y-2">
                        <div className="text-xs font-semibold text-destructive uppercase tracking-wider flex items-center gap-1.5">
                          <ShieldAlert className="h-4 w-4 text-destructive" />
                          Violations Identified ({validationResult.violations.length})
                        </div>
                        <div className="space-y-2">
                          {validationResult.violations.map((v, i) => (
                            <div
                              key={i}
                              className="p-3 bg-destructive/10 border border-destructive/20 rounded-md flex items-start justify-between"
                            >
                              <div>
                                <div className="font-semibold text-xs text-destructive flex items-center gap-2">
                                  <span>{v.type}</span>
                                  <Badge variant="outline" className="text-[10px]">
                                    Source: {v.source}
                                  </Badge>
                                </div>
                                <div className="text-sm text-foreground mt-0.5">{v.message}</div>
                              </div>
                              <Badge variant="destructive" className="ml-2 whitespace-nowrap">
                                Cap: {Number(v.limit).toFixed(2)}%
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-md flex items-center gap-3">
                        <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                        <div>
                          <div className="font-semibold text-sm text-emerald-800 dark:text-emerald-400">
                            Zero Violations Detected
                          </div>
                          <div className="text-xs text-muted-foreground">
                            The proposed discount of {Number(validationResult.proposed_discount).toFixed(2)}% complies with all governing ceilings and falls within your authorized limit.
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Evaluated Policies Breakdown */}
                    <div className="pt-2">
                      <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                        Evaluated Active Ceilings Breakdown
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                        {Object.entries(validationResult.evaluated_policies).map(([scope, pol]: [string, any]) => (
                          <div key={scope} className="p-2 border border-border rounded bg-card">
                            <div className="font-medium capitalize text-foreground">{scope}</div>
                            <div className="font-bold text-sm text-primary mt-0.5">
                              {pol.limit !== undefined ? `${Number(pol.limit).toFixed(2)}%` : "None"}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tab 9: Discount Intelligence (Phases 111–113) */}
        {activeTab === "recommendation" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" />
                  Deterministic Discount Recommendation & Safe Boundary Engine
                </CardTitle>
                <CardDescription>
                  Phases 111–113: Intersects product margin protection, active governance ceilings, and customer historical patterns to compute maximum safe discount bounds and optimal recommendations.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <form onSubmit={handleCalculateRecommendation} className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 border border-border rounded-lg bg-muted/20">
                  <FormItem>
                    <FormLabel>Target Customer</FormLabel>
                    <Select
                      value={intelCustomerId}
                      onChange={(e) => setIntelCustomerId(e.target.value)}
                    >
                      {customers.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name} ({c.customer_code})
                        </option>
                      ))}
                    </Select>
                  </FormItem>

                  <FormItem>
                    <FormLabel>Catalog Product</FormLabel>
                    <Select
                      value={intelProductId}
                      onChange={(e) => setIntelProductId(e.target.value)}
                    >
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} (${Number(p.base_price).toFixed(2)})
                        </option>
                      ))}
                    </Select>
                  </FormItem>

                  <FormItem>
                    <FormLabel>Minimum Gross Margin (%)</FormLabel>
                    <Input
                      type="number"
                      min="0"
                      max="100"
                      step="0.1"
                      value={intelMinMargin}
                      onChange={(e) => setIntelMinMargin(parseFloat(e.target.value) || 0)}
                    />
                  </FormItem>

                  <div className="flex items-end">
                    <Button type="submit" disabled={isCalculatingRec} className="w-full">
                      {isCalculatingRec ? "Analyzing..." : "Calculate Recommendation"}
                    </Button>
                  </div>
                </form>

                {recommendationResult && (
                  <div className="space-y-4 pt-2">
                    <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                      <Card className="border-primary/40 bg-primary/5">
                        <CardHeader className="py-3 px-4">
                          <CardDescription className="text-xs font-semibold text-primary">Recommended Discount</CardDescription>
                          <CardTitle className="text-2xl font-black text-primary">
                            {Number(recommendationResult.recommended_discount).toFixed(2)}%
                          </CardTitle>
                          <div className="text-[11px] text-muted-foreground mt-1">
                            Reason: <span className="font-semibold text-foreground">{recommendationResult.reason_code}</span>
                          </div>
                        </CardHeader>
                      </Card>

                      <Card>
                        <CardHeader className="py-3 px-4">
                          <CardDescription className="text-xs">Maximum Safe Discount</CardDescription>
                          <CardTitle className="text-2xl font-bold">
                            {Number(recommendationResult.max_safe_discount).toFixed(2)}%
                          </CardTitle>
                          <div className="text-[11px] text-muted-foreground mt-1">
                            Limiting: <span className="font-semibold text-foreground">{recommendationResult.evaluation_details?.limiting_factor || "N/A"}</span>
                          </div>
                        </CardHeader>
                      </Card>

                      <Card>
                        <CardHeader className="py-3 px-4">
                          <CardDescription className="text-xs">Margin Ceiling Cap</CardDescription>
                          <CardTitle className="text-2xl font-bold text-emerald-600">
                            {Number(recommendationResult.margin_ceiling).toFixed(2)}%
                          </CardTitle>
                          <div className="text-[11px] text-muted-foreground mt-1">
                            Required: {intelMinMargin}% min margin
                          </div>
                        </CardHeader>
                      </Card>

                      <Card>
                        <CardHeader className="py-3 px-4">
                          <CardDescription className="text-xs">Governed Ceiling</CardDescription>
                          <CardTitle className="text-2xl font-bold text-amber-600">
                            {Number(recommendationResult.governed_ceiling).toFixed(2)}%
                          </CardTitle>
                          <div className="text-[11px] text-muted-foreground mt-1">
                            Historical Avg: {recommendationResult.customer_historical_avg !== null ? `${Number(recommendationResult.customer_historical_avg).toFixed(2)}%` : "None"}
                          </div>
                        </CardHeader>
                      </Card>
                    </div>

                    <div className="p-4 rounded-md border border-border bg-card">
                      <div className="text-sm font-semibold text-foreground mb-1">Recommendation Summary & Rationale</div>
                      <p className="text-xs text-muted-foreground">{recommendationResult.reason_summary}</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tab 10: Historical & Customer Analytics (Phases 114–115) */}
        {activeTab === "analytics" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <BarChart3 className="h-5 w-5 text-emerald-500" />
                      Discount Behavioral & Compliance Analytics
                    </CardTitle>
                    <CardDescription>
                      Phases 114–115: Audit trail aggregation and customer discount profile analysis.
                    </CardDescription>
                  </div>
                  <Button variant="outline" size="sm" onClick={handleLoadAnalytics} disabled={isLoadingAnalytics}>
                    <RefreshCw className={`h-4 w-4 mr-2 ${isLoadingAnalytics ? "animate-spin" : ""}`} />
                    Refresh Analytics
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex flex-col sm:flex-row gap-4 p-4 border border-border rounded-lg bg-muted/20">
                  <div className="flex-1">
                    <FormLabel>Filter Customer</FormLabel>
                    <Select
                      value={intelCustomerId}
                      onChange={(e) => {
                        setIntelCustomerId(e.target.value);
                      }}
                    >
                      <option value="">All Customers (Company Wide)</option>
                      {customers.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name} ({c.customer_code})
                        </option>
                      ))}
                    </Select>
                  </div>
                  <div className="flex items-end">
                    <Button onClick={handleLoadAnalytics} disabled={isLoadingAnalytics}>
                      {isLoadingAnalytics ? "Loading..." : "Run Analysis"}
                    </Button>
                  </div>
                </div>

                {historyResult && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                      <Card className="p-3">
                        <div className="text-xs text-muted-foreground">Sample Size</div>
                        <div className="text-xl font-bold mt-1">{historyResult.summary.sample_size} deals</div>
                      </Card>
                      <Card className="p-3">
                        <div className="text-xs text-muted-foreground">Average Discount</div>
                        <div className="text-xl font-bold mt-1 text-primary">
                          {historyResult.summary.average_discount !== null ? `${Number(historyResult.summary.average_discount).toFixed(2)}%` : "N/A"}
                        </div>
                      </Card>
                      <Card className="p-3">
                        <div className="text-xs text-muted-foreground">Min Discount</div>
                        <div className="text-xl font-bold mt-1">
                          {historyResult.summary.min_discount !== null ? `${Number(historyResult.summary.min_discount).toFixed(2)}%` : "N/A"}
                        </div>
                      </Card>
                      <Card className="p-3">
                        <div className="text-xs text-muted-foreground">Max Discount</div>
                        <div className="text-xl font-bold mt-1 text-destructive">
                          {historyResult.summary.max_discount !== null ? `${Number(historyResult.summary.max_discount).toFixed(2)}%` : "N/A"}
                        </div>
                      </Card>
                      <Card className="p-3">
                        <div className="text-xs text-muted-foreground">Total Discount Amount</div>
                        <div className="text-xl font-bold mt-1">
                          ${Number(historyResult.summary.total_discount_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </div>
                      </Card>
                    </div>

                    {customerAnalysisResult && (
                      <Card className="border-border">
                        <CardHeader className="pb-2">
                          <div className="flex items-center justify-between">
                            <CardTitle className="text-sm font-semibold">
                              Customer Profile: {customerAnalysisResult.customer_name} ({customerAnalysisResult.customer_code})
                            </CardTitle>
                            <Badge
                              variant={
                                customerAnalysisResult.compliance_rating === "COMPLIANT"
                                  ? "success"
                                  : customerAnalysisResult.compliance_rating === "HIGH_DISCOUNT_CUSTOMER"
                                  ? "warning"
                                  : "secondary"
                              }
                            >
                              {customerAnalysisResult.compliance_rating}
                            </Badge>
                          </div>
                          <CardDescription className="text-xs">
                            Tier: {customerAnalysisResult.tier_name || "Standard"} | Active Ceiling: {customerAnalysisResult.active_customer_ceiling !== null ? `${Number(customerAnalysisResult.active_customer_ceiling).toFixed(2)}%` : "Standard Company Baseline"}
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="p-3 bg-muted/40 rounded text-xs text-foreground">
                            {customerAnalysisResult.insight_summary}
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
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

        {/* Modal 6: Manager Limit Form (Phase 106) */}
        <Modal
          isOpen={isMgrModalOpen}
          onClose={() => setIsMgrModalOpen(false)}
          title={editingId ? "Edit Manager Limit" : "New Sales Manager Authority Limit"}
          description="Assign maximum authorized discount approval percentage for Sales Managers."
        >
          <form onSubmit={handleSaveMgrLimit} className="space-y-4">
            {!editingId && (
              <FormItem>
                <FormLabel>Target User / Sales Manager ID</FormLabel>
                <Input
                  required
                  value={mgrForm.user_id}
                  onChange={(e) => setMgrForm({ ...mgrForm, user_id: e.target.value })}
                  placeholder="Paste Manager User UUID"
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
                value={mgrForm.max_authorized_discount}
                onChange={(e) =>
                  setMgrForm({ ...mgrForm, max_authorized_discount: parseFloat(e.target.value) || 0 })
                }
              />
            </FormItem>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setIsMgrModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Save Manager Limit</Button>
            </div>
          </form>
        </Modal>

        {/* Modal 7: Finance Limit Form (Phase 107) */}
        <Modal
          isOpen={isFinModalOpen}
          onClose={() => setIsFinModalOpen(false)}
          title={editingId ? "Edit Finance Limit" : "New Finance Authority Limit"}
          description="Assign maximum authorized discount discretionary limit for Finance officers."
        >
          <form onSubmit={handleSaveFinLimit} className="space-y-4">
            {!editingId && (
              <FormItem>
                <FormLabel>Target User / Finance Officer ID</FormLabel>
                <Input
                  required
                  value={finForm.user_id}
                  onChange={(e) => setFinForm({ ...finForm, user_id: e.target.value })}
                  placeholder="Paste Finance User UUID"
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
                value={finForm.max_authorized_discount}
                onChange={(e) =>
                  setFinForm({ ...finForm, max_authorized_discount: parseFloat(e.target.value) || 0 })
                }
              />
            </FormItem>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setIsFinModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Save Finance Limit</Button>
            </div>
          </form>
        </Modal>
      </div>
    </ProtectedRoute>
  );
}
