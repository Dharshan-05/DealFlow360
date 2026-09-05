"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  Package,
  Plus,
  Edit2,
  Trash2,
  Tags,
  DollarSign,
  TrendingUp,
  Percent,
  RefreshCw,
  FolderPlus,
  Layers,
  Repeat,
  Scale,
  ListTree,
  Sliders,
  CheckCircle,
  XCircle,
  Search,
  Filter,
  RotateCcw,
  AlertTriangle,
  Boxes,
  BarChart3,
  PieChart,
} from "lucide-react";

import { useToast } from "@/context/ToastContext";
import { useAuth } from "@/context/AuthContext";
import {
  productsApi,
  productCategoriesApi,
  productUnitsApi,
  productAttributesApi,
} from "@/lib/api";
import {
  Product,
  ProductCategory,
  ProductCreateInput,
  ProductDashboardData,
  ProductUpdateInput,
  ProductCategoryCreateInput,
  ProductCategoryUpdateInput,
  ProductUnit,
  ProductUnitCreateInput,
  ProductUnitUpdateInput,
  ProductAttribute,
  ProductAttributeCreateInput,
  ProductAttributeUpdateInput,
  ProductAttributeValueCreateInput,
  ProductVariant,
  ProductVariantCreateInput,
  ProductVariantUpdateInput,
  RecurringFrequency,
  InventoryStatus,
} from "@/types/product";
import { DataTable, ColumnDef } from "@/components/ui/data-table";
import { Modal } from "@/components/ui/modal";
import { FormItem, FormLabel } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { BarChart, DonutChart } from "@/components/ui/charts";

export default function ProductsPage() {
  const { user } = useAuth();
  const toast = useToast();

  // Core Data State
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<ProductCategory[]>([]);
  const [units, setUnits] = useState<ProductUnit[]>([]);
  const [attributes, setAttributes] = useState<ProductAttribute[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Active View Tab: "products" | "dashboard" | "categories" | "units" | "attributes"
  const [activeTab, setActiveTab] = useState<"products" | "dashboard" | "categories" | "units" | "attributes">("products");

  // Phase 085: Product Dashboard Analytics State
  const [dashboardData, setDashboardData] = useState<ProductDashboardData | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState<boolean>(false);

  // Phase 083 & 084: Search & Composable Filter States
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [debouncedSearch, setDebouncedSearch] = useState<string>("");
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<string>("ALL");
  const [selectedStatusFilter, setSelectedStatusFilter] = useState<string>("ALL");
  const [selectedSubscriptionFilter, setSelectedSubscriptionFilter] = useState<string>("ALL");
  const [selectedInventoryFilter, setSelectedInventoryFilter] = useState<string>("ALL");
  const [isSearching, setIsSearching] = useState<boolean>(false);

  // Debounce search query (~300ms)
  useEffect(() => {
    setIsSearching(true);
    const handler = setTimeout(() => {
      setDebouncedSearch(searchTerm.trim());
      setIsSearching(false);
    }, 300);
    return () => clearTimeout(handler);
  }, [searchTerm]);

  const resetFilters = () => {
    setSearchTerm("");
    setDebouncedSearch("");
    setSelectedCategoryFilter("ALL");
    setSelectedStatusFilter("ALL");
    setSelectedSubscriptionFilter("ALL");
    setSelectedInventoryFilter("ALL");
  };

  const hasActiveFilters =
    Boolean(searchTerm.trim()) ||
    selectedCategoryFilter !== "ALL" ||
    selectedStatusFilter !== "ALL" ||
    selectedSubscriptionFilter !== "ALL" ||
    selectedInventoryFilter !== "ALL";

  // Create Product Modal (Phases 071, 073, 074, 076, 077, 080, 081, 082)
  const [isCreateProductOpen, setIsCreateProductOpen] = useState<boolean>(false);
  const [createProductLoading, setCreateProductLoading] = useState<boolean>(false);
  const [newProduct, setNewProduct] = useState<ProductCreateInput>({
    sku: "",
    name: "",
    description: "",
    category_id: "",
    cost: "0.00",
    base_price: "0.00",
    unit: "unit",
    tax_rate: "0.00",
    is_subscription: false,
    recurring_frequency: "monthly",
    inventory_quantity: 0,
    low_stock_threshold: 5,
    is_active: true,
  });

  // Edit Product Modal (Phases 071, 073, 074, 076, 077, 080, 081, 082)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [editProductLoading, setEditProductLoading] = useState<boolean>(false);

  // Delete Product Modal
  const [deletingProduct, setDeletingProduct] = useState<Product | null>(null);
  const [deleteProductLoading, setDeleteProductLoading] = useState<boolean>(false);

  // Manage Variants Modal (Phase 078)
  const [managingVariantsProduct, setManagingVariantsProduct] = useState<Product | null>(null);
  const [productVariants, setProductVariants] = useState<ProductVariant[]>([]);
  const [loadingVariants, setLoadingVariants] = useState<boolean>(false);
  const [isCreateVariantOpen, setIsCreateVariantOpen] = useState<boolean>(false);
  const [createVariantLoading, setCreateVariantLoading] = useState<boolean>(false);
  const [newVariant, setNewVariant] = useState<ProductVariantCreateInput>({
    sku: "",
    name: "",
    cost: "",
    base_price: "",
    is_active: true,
    attribute_value_ids: [],
  });

  // Category Modals (Phase 072)
  const [isCreateCategoryOpen, setIsCreateCategoryOpen] = useState<boolean>(false);
  const [createCategoryLoading, setCreateCategoryLoading] = useState<boolean>(false);
  const [newCategory, setNewCategory] = useState<ProductCategoryCreateInput>({
    name: "",
    code: "",
    description: "",
    is_active: true,
  });
  const [editingCategory, setEditingCategory] = useState<ProductCategory | null>(null);
  const [editCategoryLoading, setEditCategoryLoading] = useState<boolean>(false);
  const [deletingCategory, setDeletingCategory] = useState<ProductCategory | null>(null);
  const [deleteCategoryLoading, setDeleteCategoryLoading] = useState<boolean>(false);

  // Unit Modals (Phase 077)
  const [isCreateUnitOpen, setIsCreateUnitOpen] = useState<boolean>(false);
  const [createUnitLoading, setCreateUnitLoading] = useState<boolean>(false);
  const [newUnit, setNewUnit] = useState<ProductUnitCreateInput>({
    code: "",
    name: "",
    description: "",
    is_active: true,
  });

  // Attribute Modals (Phase 079)
  const [isCreateAttributeOpen, setIsCreateAttributeOpen] = useState<boolean>(false);
  const [createAttributeLoading, setCreateAttributeLoading] = useState<boolean>(false);
  const [newAttribute, setNewAttribute] = useState<ProductAttributeCreateInput>({
    code: "",
    name: "",
    description: "",
    is_active: true,
  });
  const [selectedAttributeForValue, setSelectedAttributeForValue] = useState<ProductAttribute | null>(null);
  const [newValueInput, setNewValueInput] = useState<string>("");
  const [addValueLoading, setAddValueLoading] = useState<boolean>(false);

  // Load All Data
  const loadData = useCallback(async () => {
    try {
      setError(null);
      const [prodRes, catRes, unitRes, attrRes, dashRes] = await Promise.all([
        productsApi.getAll({
          limit: 100,
          search: debouncedSearch || undefined,
          category_id: selectedCategoryFilter !== "ALL" ? selectedCategoryFilter : undefined,
          is_active:
            selectedStatusFilter === "ACTIVE"
              ? true
              : selectedStatusFilter === "INACTIVE"
              ? false
              : undefined,
          is_subscription:
            selectedSubscriptionFilter === "SUBSCRIPTION"
              ? true
              : selectedSubscriptionFilter === "STANDARD"
              ? false
              : undefined,
          inventory_status: selectedInventoryFilter !== "ALL" ? selectedInventoryFilter : undefined,
        }),
        productCategoriesApi.getAll(true),
        productUnitsApi.getAll(true),
        productAttributesApi.getAll(true),
        productsApi.getDashboard().catch(() => null),
      ]);
      setProducts(prodRes.items);
      setCategories(catRes);
      setUnits(unitRes);
      setAttributes(attrRes);
      if (dashRes) setDashboardData(dashRes);
    } catch (err: any) {
      setError(err.message || "Failed to load product catalog.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [
    debouncedSearch,
    selectedCategoryFilter,
    selectedStatusFilter,
    selectedSubscriptionFilter,
    selectedInventoryFilter,
  ]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadData();
  };

  // Live margin computation helper for create/edit forms (Phase 075)
  const computeLiveMargin = (priceInput: string | number | undefined, costInput: string | number | undefined) => {
    const price = parseFloat(String(priceInput || 0));
    const cost = parseFloat(String(costInput || 0));
    const marginAmount = (price - cost).toFixed(2);
    let marginPct: string | null = null;
    if (price > 0) {
      marginPct = (((price - cost) / price) * 100).toFixed(2);
    }
    return {
      price,
      cost,
      marginAmount,
      marginPct,
    };
  };

  // ---------------------------------------------------------------------------
  // Product Actions (Phases 071, 073, 074, 076, 077, 080)
  // ---------------------------------------------------------------------------
  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProduct.sku.trim() || !newProduct.name.trim()) {
      toast.error("SKU and Product Name are required.");
      return;
    }

    try {
      setCreateProductLoading(true);
      await productsApi.create({
        ...newProduct,
        sku: newProduct.sku.trim().toUpperCase(),
        name: newProduct.name.trim(),
        category_id: newProduct.category_id || null,
        base_price: newProduct.base_price || "0.00",
        cost: newProduct.cost || "0.00",
        unit: newProduct.unit || "unit",
        tax_rate: newProduct.tax_rate || "0.00",
        is_subscription: Boolean(newProduct.is_subscription),
        recurring_frequency: newProduct.is_subscription ? (newProduct.recurring_frequency || "monthly") : null,
        inventory_quantity: Number(newProduct.inventory_quantity ?? 0),
        low_stock_threshold: Number(newProduct.low_stock_threshold ?? 5),
      });
      toast.success(`Product "${newProduct.name}" created successfully.`);
      setIsCreateProductOpen(false);
      setNewProduct({
        sku: "",
        name: "",
        description: "",
        category_id: "",
        cost: "0.00",
        base_price: "0.00",
        unit: "unit",
        tax_rate: "0.00",
        is_subscription: false,
        recurring_frequency: "monthly",
        inventory_quantity: 0,
        low_stock_threshold: 5,
        is_active: true,
      });
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to create product.");
    } finally {
      setCreateProductLoading(false);
    }
  };

  const handleUpdateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProduct) return;

    try {
      setEditProductLoading(true);
      await productsApi.update(editingProduct.id, {
        name: editingProduct.name.trim(),
        description: editingProduct.description || null,
        category_id: editingProduct.category_id || null,
        base_price: editingProduct.base_price,
        cost: editingProduct.cost,
        unit: editingProduct.unit,
        tax_rate: editingProduct.tax_rate,
        is_subscription: editingProduct.is_subscription,
        recurring_frequency: editingProduct.is_subscription ? (editingProduct.recurring_frequency || "monthly") : null,
        inventory_quantity: Number(editingProduct.inventory_quantity ?? 0),
        low_stock_threshold: Number(editingProduct.low_stock_threshold ?? 5),
        is_active: editingProduct.is_active,
      });
      toast.success(`Product "${editingProduct.name}" updated successfully.`);
      setEditingProduct(null);
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to update product.");
    } finally {
      setEditProductLoading(false);
    }
  };

  const handleDeleteProduct = async () => {
    if (!deletingProduct) return;

    try {
      setDeleteProductLoading(true);
      await productsApi.delete(deletingProduct.id, true);
      toast.success(`Product "${deletingProduct.name}" deactivated.`);
      setDeletingProduct(null);
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to deactivate product.");
    } finally {
      setDeleteProductLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Variant Management (Phase 078)
  // ---------------------------------------------------------------------------
  const openVariantsModal = async (product: Product) => {
    setManagingVariantsProduct(product);
    setLoadingVariants(true);
    try {
      const vars = await productsApi.getVariants(product.id, true);
      setProductVariants(vars);
    } catch (err: any) {
      toast.error(err.message || "Failed to load variants.");
    } finally {
      setLoadingVariants(false);
    }
  };

  const handleCreateVariant = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!managingVariantsProduct || !newVariant.sku.trim() || !newVariant.name.trim()) {
      toast.error("Variant SKU and Name are required.");
      return;
    }

    try {
      setCreateVariantLoading(true);
      await productsApi.createVariant(managingVariantsProduct.id, {
        sku: newVariant.sku.trim().toUpperCase(),
        name: newVariant.name.trim(),
        cost: newVariant.cost ? String(newVariant.cost) : null,
        base_price: newVariant.base_price ? String(newVariant.base_price) : null,
        is_active: newVariant.is_active,
        attribute_value_ids: newVariant.attribute_value_ids || [],
      });
      toast.success(`Variant "${newVariant.name}" created.`);
      setIsCreateVariantOpen(false);
      setNewVariant({
        sku: "",
        name: "",
        cost: "",
        base_price: "",
        is_active: true,
        attribute_value_ids: [],
      });
      // Refresh variants
      const vars = await productsApi.getVariants(managingVariantsProduct.id, true);
      setProductVariants(vars);
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to create variant.");
    } finally {
      setCreateVariantLoading(false);
    }
  };

  const handleDeleteVariant = async (variantId: string) => {
    if (!managingVariantsProduct) return;
    try {
      await productsApi.deleteVariant(variantId, true);
      toast.success("Variant deactivated.");
      const vars = await productsApi.getVariants(managingVariantsProduct.id, true);
      setProductVariants(vars);
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to delete variant.");
    }
  };

  // ---------------------------------------------------------------------------
  // Category Actions (Phase 072)
  // ---------------------------------------------------------------------------
  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCategory.code.trim() || !newCategory.name.trim()) {
      toast.error("Category Code and Name are required.");
      return;
    }

    try {
      setCreateCategoryLoading(true);
      await productCategoriesApi.create({
        ...newCategory,
        code: newCategory.code.trim().toUpperCase(),
        name: newCategory.name.trim(),
      });
      toast.success(`Category "${newCategory.name}" created.`);
      setIsCreateCategoryOpen(false);
      setNewCategory({ name: "", code: "", description: "", is_active: true });
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to create category.");
    } finally {
      setCreateCategoryLoading(false);
    }
  };

  const handleUpdateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCategory) return;

    try {
      setEditCategoryLoading(true);
      await productCategoriesApi.update(editingCategory.id, {
        name: editingCategory.name.trim(),
        description: editingCategory.description || null,
        is_active: editingCategory.is_active,
      });
      toast.success(`Category "${editingCategory.name}" updated.`);
      setEditingCategory(null);
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to update category.");
    } finally {
      setEditCategoryLoading(false);
    }
  };

  const handleDeleteCategory = async () => {
    if (!deletingCategory) return;
    try {
      setDeleteCategoryLoading(true);
      await productCategoriesApi.delete(deletingCategory.id, true);
      toast.success(`Category "${deletingCategory.name}" deactivated.`);
      setDeletingCategory(null);
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to deactivate category.");
    } finally {
      setDeleteCategoryLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Unit Actions (Phase 077)
  // ---------------------------------------------------------------------------
  const handleCreateUnit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUnit.code.trim() || !newUnit.name.trim()) {
      toast.error("Unit Code and Name are required.");
      return;
    }

    try {
      setCreateUnitLoading(true);
      await productUnitsApi.create({
        ...newUnit,
        code: newUnit.code.trim().toUpperCase(),
        name: newUnit.name.trim(),
      });
      toast.success(`Unit "${newUnit.name}" created.`);
      setIsCreateUnitOpen(false);
      setNewUnit({ code: "", name: "", description: "", is_active: true });
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to create unit.");
    } finally {
      setCreateUnitLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Attribute Actions (Phase 079)
  // ---------------------------------------------------------------------------
  const handleCreateAttribute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAttribute.code.trim() || !newAttribute.name.trim()) {
      toast.error("Attribute Code and Name are required.");
      return;
    }

    try {
      setCreateAttributeLoading(true);
      await productAttributesApi.create({
        ...newAttribute,
        code: newAttribute.code.trim().toUpperCase(),
        name: newAttribute.name.trim(),
      });
      toast.success(`Attribute "${newAttribute.name}" created.`);
      setIsCreateAttributeOpen(false);
      setNewAttribute({ code: "", name: "", description: "", is_active: true });
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to create attribute.");
    } finally {
      setCreateAttributeLoading(false);
    }
  };

  const handleAddAttributeValue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAttributeForValue || !newValueInput.trim()) return;

    try {
      setAddValueLoading(true);
      await productAttributesApi.addValue(selectedAttributeForValue.id, {
        value: newValueInput.trim(),
      });
      toast.success(`Added option "${newValueInput.trim()}".`);
      setNewValueInput("");
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to add attribute value.");
    } finally {
      setAddValueLoading(false);
    }
  };

  const handleDeleteAttributeValue = async (attributeId: string, valueId: string) => {
    try {
      await productAttributesApi.deleteValue(attributeId, valueId);
      toast.success("Attribute value removed.");
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to delete attribute value.");
    }
  };

  // ---------------------------------------------------------------------------
  // Margin Styling Helper (Phase 075)
  // ---------------------------------------------------------------------------
  const renderMarginBadge = (amount: number | string, pct: number | string | null) => {
    const numAmount = Number(amount);
    const numPct = pct !== null ? Number(pct) : null;

    if (numAmount > 0) {
      return (
        <div className="flex flex-col items-start gap-0.5">
          <span className="font-mono text-xs font-semibold text-emerald-700">
            +${numAmount.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
          {numPct !== null && (
            <Badge variant="success" className="text-[10px] font-mono px-1.5 py-0">
              {numPct.toFixed(1)}%
            </Badge>
          )}
        </div>
      );
    }

    if (numAmount === 0) {
      return (
        <div className="flex flex-col items-start gap-0.5">
          <span className="font-mono text-xs font-semibold text-amber-700">$0.00</span>
          <Badge variant="warning" className="text-[10px] font-mono px-1.5 py-0">
            0.0%
          </Badge>
        </div>
      );
    }

    return (
      <div className="flex flex-col items-start gap-0.5">
        <span className="font-mono text-xs font-semibold text-rose-700">
          -${Math.abs(numAmount).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
        {numPct !== null && (
          <Badge variant="destructive" className="text-[10px] font-mono px-1.5 py-0">
            {numPct.toFixed(1)}%
          </Badge>
        )}
      </div>
    );
  };

  // ---------------------------------------------------------------------------
  // Data Table Columns
  // ---------------------------------------------------------------------------
  const productColumns: ColumnDef<Product>[] = [
    {
      id: "sku",
      header: "SKU / Code",
      accessorKey: "sku",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-semibold text-slate-800 bg-slate-100 px-2 py-1 rounded">
          {row.sku}
        </span>
      ),
    },
    {
      id: "name",
      header: "Product Name",
      accessorKey: "name",
      sortable: true,
      cell: (row) => (
        <div>
          <div className="font-semibold text-sm text-foreground flex items-center gap-1.5 flex-wrap">
            <span>{row.name}</span>
            {row.is_subscription && (
              <Badge variant="secondary" className="text-[10px] bg-purple-50 text-purple-700 border-purple-200">
                <Repeat className="h-2.5 w-2.5 mr-0.5" />
                <span>Subscription ({row.recurring_frequency || "monthly"})</span>
              </Badge>
            )}
          </div>
          {row.description && <div className="text-xs text-muted truncate max-w-xs">{row.description}</div>}
        </div>
      ),
    },
    {
      id: "inventory",
      header: "Stock Level (082)",
      accessorKey: "inventory_quantity",
      sortable: true,
      cell: (row) => {
        if (row.inventory_status === "OUT_OF_STOCK" || Number(row.inventory_quantity) <= 0) {
          return (
            <Badge variant="destructive" className="gap-1 font-mono text-[11px]">
              <AlertTriangle className="h-3 w-3" />
              <span>Out of Stock (0)</span>
            </Badge>
          );
        }
        if (
          row.inventory_status === "LOW_STOCK" ||
          Number(row.inventory_quantity) <= Number(row.low_stock_threshold)
        ) {
          return (
            <Badge variant="warning" className="gap-1 font-mono text-[11px] bg-amber-50 text-amber-800 border-amber-300">
              <AlertTriangle className="h-3 w-3" />
              <span>Low: {row.inventory_quantity} (min {row.low_stock_threshold})</span>
            </Badge>
          );
        }
        return (
          <Badge variant="success" className="gap-1 font-mono text-[11px] bg-emerald-50 text-emerald-800 border-emerald-300">
            <Boxes className="h-3 w-3" />
            <span>{row.inventory_quantity} in stock</span>
          </Badge>
        );
      },
    },
    {
      id: "unit",
      header: "Unit (077)",
      cell: (row) => (
        <span className="text-xs font-medium uppercase text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
          {row.unit || "unit"}
        </span>
      ),
    },
    {
      id: "tax_rate",
      header: "Tax (076)",
      cell: (row) => (
        <span className="font-mono text-xs text-slate-600">
          {Number(row.tax_rate).toFixed(2)}%
        </span>
      ),
    },
    {
      id: "base_price",
      header: "Selling Price (073)",
      accessorKey: "base_price",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-semibold text-slate-900">
          ${Number(row.base_price).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      id: "cost",
      header: "Cost (074)",
      accessorKey: "cost",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-semibold text-slate-600">
          ${Number(row.cost).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      id: "margin",
      header: "Margin (075)",
      cell: (row) => renderMarginBadge(row.margin_amount, row.margin_percentage),
    },
    {
      id: "variants",
      header: "Variants (078)",
      cell: (row) => (
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-xs gap-1"
          onClick={() => openVariantsModal(row)}
        >
          <ListTree className="h-3 w-3" />
          <span>{row.variants?.length || 0} Variants</span>
        </Button>
      ),
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
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2 text-slate-600 hover:text-foreground"
            onClick={() => setEditingProduct(row)}
            title="Edit Product"
          >
            <Edit2 className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2 text-rose-600 hover:bg-rose-50"
            onClick={() => setDeletingProduct(row)}
            title="Deactivate Product"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  const categoryColumns: ColumnDef<ProductCategory>[] = [
    {
      id: "code",
      header: "Code",
      accessorKey: "code",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-semibold text-slate-800 bg-slate-100 px-2 py-1 rounded">
          {row.code}
        </span>
      ),
    },
    {
      id: "name",
      header: "Category Name",
      accessorKey: "name",
      sortable: true,
      cell: (row) => (
        <div>
          <div className="font-semibold text-sm text-foreground">{row.name}</div>
          {row.description && <div className="text-xs text-muted truncate max-w-sm">{row.description}</div>}
        </div>
      ),
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
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2 text-slate-600 hover:text-foreground"
            onClick={() => setEditingCategory(row)}
            title="Edit Category"
          >
            <Edit2 className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2 text-rose-600 hover:bg-rose-50"
            onClick={() => setDeletingCategory(row)}
            title="Deactivate Category"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  const unitColumns: ColumnDef<ProductUnit>[] = [
    {
      id: "code",
      header: "Unit Code",
      accessorKey: "code",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-semibold text-slate-800 bg-slate-100 px-2 py-1 rounded">
          {row.code}
        </span>
      ),
    },
    {
      id: "name",
      header: "Display Name",
      accessorKey: "name",
      sortable: true,
      cell: (row) => <span className="font-medium text-sm text-foreground">{row.name}</span>,
    },
    {
      id: "description",
      header: "Description",
      cell: (row) => <span className="text-xs text-muted">{row.description || "—"}</span>,
    },
    {
      id: "status",
      header: "Status",
      cell: (row) => (row.is_active ? <Badge variant="success">Active</Badge> : <Badge variant="outline">Inactive</Badge>),
    },
  ];

  const attributeColumns: ColumnDef<ProductAttribute>[] = [
    {
      id: "code",
      header: "Attribute Code",
      accessorKey: "code",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-semibold text-slate-800 bg-slate-100 px-2 py-1 rounded">
          {row.code}
        </span>
      ),
    },
    {
      id: "name",
      header: "Attribute Name",
      accessorKey: "name",
      sortable: true,
      cell: (row) => <span className="font-medium text-sm text-foreground">{row.name}</span>,
    },
    {
      id: "values",
      header: "Options / Values (Phase 079)",
      cell: (row) => (
        <div className="flex flex-wrap items-center gap-1.5 max-w-md">
          {row.values?.map((v) => (
            <Badge key={v.id} variant="secondary" className="gap-1 text-xs">
              <span>{v.value}</span>
              <button
                type="button"
                onClick={() => handleDeleteAttributeValue(row.id, v.id)}
                className="hover:text-rose-600 text-slate-400 ml-1"
                title="Remove option"
              >
                ×
              </button>
            </Badge>
          ))}
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-1.5 text-xs text-primary"
            onClick={() => setSelectedAttributeForValue(row)}
          >
            + Add Option
          </Button>
        </div>
      ),
    },
  ];

  // Computed margins for active modals
  const newProductMargin = useMemo(
    () => computeLiveMargin(newProduct.base_price, newProduct.cost),
    [newProduct.base_price, newProduct.cost]
  );

  const editProductMargin = useMemo(
    () => (editingProduct ? computeLiveMargin(editingProduct.base_price, editingProduct.cost) : null),
    [editingProduct?.base_price, editingProduct?.cost]
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Product &amp; Pricing Management
            </h1>
            <Badge variant="primary" className="font-mono text-[11px]">
              G16 (Phases 076–080)
            </Badge>
          </div>
          <p className="text-sm text-muted mt-1">
            Maintain product catalog, tax rates, units of measure, parent-child variants, attributes, and subscription items.
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

          {activeTab === "products" && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsCreateProductOpen(true)}
              className="gap-1.5"
            >
              <Plus className="h-4 w-4" />
              <span>Add Product</span>
            </Button>
          )}

          {activeTab === "categories" && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsCreateCategoryOpen(true)}
              className="gap-1.5"
            >
              <FolderPlus className="h-4 w-4" />
              <span>Add Category</span>
            </Button>
          )}

          {activeTab === "units" && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsCreateUnitOpen(true)}
              className="gap-1.5"
            >
              <Scale className="h-4 w-4" />
              <span>Add Unit</span>
            </Button>
          )}

          {activeTab === "attributes" && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsCreateAttributeOpen(true)}
              className="gap-1.5"
            >
              <Sliders className="h-4 w-4" />
              <span>Add Attribute</span>
            </Button>
          )}
        </div>
      </div>

      {/* KPI Overview Summary (Phases 071–080) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-card border-border shadow-xs">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-blue-50 text-blue-600">
              <Package className="h-5 w-5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-muted uppercase tracking-wider">
                Total Products
              </div>
              <div className="text-2xl font-bold text-foreground mt-0.5">
                {products.length}
              </div>
              <div className="text-[11px] text-muted">
                {products.filter((p) => p.is_active).length} active in catalog
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-card border-border shadow-xs">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-purple-50 text-purple-600">
              <Repeat className="h-5 w-5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-muted uppercase tracking-wider">
                Subscriptions (Phase 080)
              </div>
              <div className="text-2xl font-bold text-foreground mt-0.5">
                {products.filter((p) => p.is_subscription).length}
              </div>
              <div className="text-[11px] text-muted">
                Recurring product offerings
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-card border-border shadow-xs">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-600">
              <DollarSign className="h-5 w-5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-muted uppercase tracking-wider">
                Catalog Value
              </div>
              <div className="text-2xl font-bold text-emerald-700 mt-0.5">
                ${products.reduce((acc, p) => acc + Number(p.base_price), 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className="text-[11px] text-muted">
                Cumulative list price baseline
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-card border-border shadow-xs">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-amber-50 text-amber-600">
              <TrendingUp className="h-5 w-5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-muted uppercase tracking-wider">
                Gross Profit Potential
              </div>
              <div className="text-2xl font-bold text-foreground mt-0.5">
                ${products.reduce((acc, p) => acc + Number(p.margin_amount), 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className="text-[11px] text-muted">
                Aggregate list margin amount
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Navigation Tabs (Phases 071–085) */}
      <div className="border-b border-border">
        <div className="flex items-center gap-6 overflow-x-auto">
          <button
            type="button"
            onClick={() => setActiveTab("products")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 whitespace-nowrap ${
              activeTab === "products"
                ? "border-primary text-primary"
                : "border-transparent text-muted hover:text-foreground"
            }`}
          >
            <Package className="h-4 w-4" />
            <span>Product Catalog ({products.length})</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("dashboard")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 whitespace-nowrap ${
              activeTab === "dashboard"
                ? "border-primary text-primary"
                : "border-transparent text-muted hover:text-foreground"
            }`}
          >
            <BarChart3 className="h-4 w-4" />
            <span>Dashboard (Phase 085)</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("categories")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 whitespace-nowrap ${
              activeTab === "categories"
                ? "border-primary text-primary"
                : "border-transparent text-muted hover:text-foreground"
            }`}
          >
            <Tags className="h-4 w-4" />
            <span>Categories (072) ({categories.length})</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("units")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 whitespace-nowrap ${
              activeTab === "units"
                ? "border-primary text-primary"
                : "border-transparent text-muted hover:text-foreground"
            }`}
          >
            <Scale className="h-4 w-4" />
            <span>Units of Measure (077) ({units.length})</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("attributes")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 whitespace-nowrap ${
              activeTab === "attributes"
                ? "border-primary text-primary"
                : "border-transparent text-muted hover:text-foreground"
            }`}
          >
            <Sliders className="h-4 w-4" />
            <span>Attributes &amp; Options (079) ({attributes.length})</span>
          </button>
        </div>
      </div>

      {/* Active Tab View */}
      {activeTab === "products" && (
        <div className="space-y-4">
          {/* Phase 083 & 084: Search & Composable Filter Bar */}
          <div className="p-4 rounded-xl border border-border bg-card shadow-xs space-y-3">
            <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
              {/* Search Input (Phase 083) */}
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted" />
                <Input
                  type="text"
                  placeholder="Search products by SKU, name, or category..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 pr-9"
                />
                {isSearching ? (
                  <RefreshCw className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted animate-spin" />
                ) : searchTerm ? (
                  <button
                    type="button"
                    onClick={() => setSearchTerm("")}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-foreground text-sm px-1"
                  >
                    ×
                  </button>
                ) : null}
              </div>

              {/* Composable Filter Selects (Phase 084) */}
              <div className="flex flex-wrap items-center gap-2">
                <Select
                  value={selectedCategoryFilter}
                  onChange={(e) => setSelectedCategoryFilter(e.target.value)}
                  className="w-40 text-xs"
                >
                  <option value="ALL">All Categories</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </Select>

                <Select
                  value={selectedInventoryFilter}
                  onChange={(e) => setSelectedInventoryFilter(e.target.value)}
                  className="w-36 text-xs"
                >
                  <option value="ALL">All Stock Levels</option>
                  <option value="IN_STOCK">In Stock</option>
                  <option value="LOW_STOCK">Low Stock</option>
                  <option value="OUT_OF_STOCK">Out of Stock</option>
                </Select>

                <Select
                  value={selectedSubscriptionFilter}
                  onChange={(e) => setSelectedSubscriptionFilter(e.target.value)}
                  className="w-36 text-xs"
                >
                  <option value="ALL">All Product Types</option>
                  <option value="SUBSCRIPTION">Subscription Only</option>
                  <option value="STANDARD">Standard Only</option>
                </Select>

                <Select
                  value={selectedStatusFilter}
                  onChange={(e) => setSelectedStatusFilter(e.target.value)}
                  className="w-32 text-xs"
                >
                  <option value="ALL">All Status</option>
                  <option value="ACTIVE">Active</option>
                  <option value="INACTIVE">Inactive</option>
                </Select>

                {hasActiveFilters && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={resetFilters}
                    className="text-xs h-9 gap-1 text-slate-600 hover:text-foreground"
                    title="Reset all filters"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                    <span>Reset</span>
                  </Button>
                )}
              </div>
            </div>

            {hasActiveFilters && (
              <div className="flex items-center gap-2 text-xs text-muted pt-1 border-t border-border/50">
                <Filter className="h-3.5 w-3.5 text-primary" />
                <span>
                  Filtering active — showing {products.length} product{products.length !== 1 ? "s" : ""}.
                </span>
              </div>
            )}
          </div>

          <DataTable
            columns={productColumns}
            data={products}
            keyExtractor={(item) => item.id}
            isLoading={isLoading}
            error={error}
            onRetry={loadData}
            emptyTitle={hasActiveFilters ? "No products match current filters" : "No products in catalog"}
            emptyDescription={
              hasActiveFilters
                ? "Try adjusting your search keywords or resetting active filter criteria."
                : "Add products with selling prices, tax rates, units, and subscription options."
            }
            emptyAction={
              hasActiveFilters ? (
                <Button size="sm" variant="outline" onClick={resetFilters} className="gap-1.5 mt-2">
                  <RotateCcw className="h-4 w-4" />
                  <span>Reset Filters</span>
                </Button>
              ) : (
                <Button size="sm" onClick={() => setIsCreateProductOpen(true)} className="gap-1.5 mt-2">
                  <Plus className="h-4 w-4" />
                  <span>Create First Product</span>
                </Button>
              )
            }
          />
        </div>
      )}

      {/* Phase 085: Product Dashboard View */}
      {activeTab === "dashboard" && (
        <div className="space-y-6">
          {/* Top KPI Metrics Cards (Phase 085) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <Card className="p-4 bg-card border-border shadow-xs">
              <div className="text-xs font-semibold text-muted uppercase tracking-wider">Total Catalog</div>
              <div className="text-2xl font-bold text-foreground mt-1">
                {dashboardData?.total_products ?? products.length}
              </div>
              <div className="text-[11px] text-muted mt-0.5">Total managed products</div>
            </Card>

            <Card className="p-4 bg-card border-border shadow-xs">
              <div className="text-xs font-semibold text-muted uppercase tracking-wider">Active Products</div>
              <div className="text-2xl font-bold text-emerald-700 mt-1">
                {dashboardData?.active_products ?? products.filter((p) => p.is_active).length}
              </div>
              <div className="text-[11px] text-muted mt-0.5">Available for quotes</div>
            </Card>

            <Card className="p-4 bg-card border-border shadow-xs">
              <div className="text-xs font-semibold text-muted uppercase tracking-wider">In Stock (082)</div>
              <div className="text-2xl font-bold text-blue-700 mt-1">
                {dashboardData?.in_stock_products ?? products.filter((p) => p.inventory_status === "IN_STOCK").length}
              </div>
              <div className="text-[11px] text-muted mt-0.5">Quantity above threshold</div>
            </Card>

            <Card className="p-4 bg-card border-border shadow-xs">
              <div className="text-xs font-semibold text-muted uppercase tracking-wider">Low Stock (082)</div>
              <div className="text-2xl font-bold text-amber-700 mt-1">
                {dashboardData?.low_stock_products ?? products.filter((p) => p.inventory_status === "LOW_STOCK").length}
              </div>
              <div className="text-[11px] text-muted mt-0.5">Approaching minimum level</div>
            </Card>

            <Card className="p-4 bg-card border-border shadow-xs">
              <div className="text-xs font-semibold text-muted uppercase tracking-wider">Out of Stock (082)</div>
              <div className="text-2xl font-bold text-rose-700 mt-1">
                {dashboardData?.out_of_stock_products ?? products.filter((p) => p.inventory_status === "OUT_OF_STOCK").length}
              </div>
              <div className="text-[11px] text-muted mt-0.5">Zero inventory remaining</div>
            </Card>
          </div>

          {/* Row 1: Stock Status Distribution & Products by Category */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <DonutChart
              title="Inventory Stock Status (Phase 082)"
              description="Real-time breakdown across stock availability states"
              data={[
                {
                  label: "In Stock",
                  value: dashboardData?.inventory_distribution?.IN_STOCK ?? 0,
                  color: "#10b981",
                },
                {
                  label: "Low Stock",
                  value: dashboardData?.inventory_distribution?.LOW_STOCK ?? 0,
                  color: "#f59e0b",
                },
                {
                  label: "Out of Stock",
                  value: dashboardData?.inventory_distribution?.OUT_OF_STOCK ?? 0,
                  color: "#ef4444",
                },
              ]}
              isLoading={dashboardLoading}
            />

            <BarChart
              title="Products by Category (Phase 072)"
              description="Catalog distribution across product categories"
              data={
                (dashboardData?.category_distribution || []).map((cat, idx) => ({
                  label: cat.category_name,
                  value: cat.count,
                  color: ["#3b82f6", "#8b5cf6", "#ec4899", "#14b8a6"][idx % 4],
                }))
              }
              isLoading={dashboardLoading}
            />
          </div>

          {/* Row 2: Subscriptions & Billing Cycles */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <DonutChart
              title="Subscription vs Standard Products (Phase 080)"
              description="Product offering breakdown by pricing model"
              data={[
                {
                  label: "Subscriptions",
                  value: dashboardData?.subscription_distribution?.subscription ?? 0,
                  color: "#8b5cf6",
                },
                {
                  label: "Standard Items",
                  value: dashboardData?.subscription_distribution?.standard ?? 0,
                  color: "#64748b",
                },
              ]}
              isLoading={dashboardLoading}
            />

            <BarChart
              title="Recurring Billing Cycles (Phase 081)"
              description="Distribution of subscription recurring frequencies"
              data={[
                {
                  label: "Monthly",
                  value: dashboardData?.frequency_distribution?.monthly ?? 0,
                  color: "#06b6d4",
                },
                {
                  label: "Quarterly",
                  value: dashboardData?.frequency_distribution?.quarterly ?? 0,
                  color: "#3b82f6",
                },
                {
                  label: "Yearly",
                  value: dashboardData?.frequency_distribution?.yearly ?? 0,
                  color: "#6366f1",
                },
              ]}
              isLoading={dashboardLoading}
            />
          </div>
        </div>
      )}

      {activeTab === "categories" && (
        <DataTable
          columns={categoryColumns}
          data={categories}
          keyExtractor={(item) => item.id}
          isLoading={isLoading}
          error={error}
          onRetry={loadData}
          emptyTitle="No product categories"
          emptyDescription="Create categories to organize your product offerings."
          emptyAction={
            <Button size="sm" onClick={() => setIsCreateCategoryOpen(true)} className="gap-1.5 mt-2">
              <FolderPlus className="h-4 w-4" />
              <span>Create First Category</span>
            </Button>
          }
        />
      )}

      {activeTab === "units" && (
        <DataTable
          columns={unitColumns}
          data={units}
          keyExtractor={(item) => item.id}
          isLoading={isLoading}
          error={error}
          onRetry={loadData}
          emptyTitle="No units configured"
          emptyDescription="Add standard units of measure (e.g., UNIT, LICENSE, BOX, KG)."
          emptyAction={
            <Button size="sm" onClick={() => setIsCreateUnitOpen(true)} className="gap-1.5 mt-2">
              <Scale className="h-4 w-4" />
              <span>Create First Unit</span>
            </Button>
          }
        />
      )}

      {activeTab === "attributes" && (
        <DataTable
          columns={attributeColumns}
          data={attributes}
          keyExtractor={(item) => item.id}
          isLoading={isLoading}
          error={error}
          onRetry={loadData}
          emptyTitle="No attributes defined"
          emptyDescription="Create product attribute definitions (e.g., Color, Size, Storage) and configure options."
          emptyAction={
            <Button size="sm" onClick={() => setIsCreateAttributeOpen(true)} className="gap-1.5 mt-2">
              <Sliders className="h-4 w-4" />
              <span>Create First Attribute</span>
            </Button>
          }
        />
      )}

      {/* Add Product Modal (Phases 071, 073, 074, 075, 076, 077, 080) */}
      <Modal
        isOpen={isCreateProductOpen}
        onClose={() => setIsCreateProductOpen(false)}
        title="Add Catalog Product"
        description="Register a new product with selling price, unit cost, tax rate, unit of measure, and subscription status."
        size="lg"
      >
        <form onSubmit={handleCreateProduct} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormItem>
              <FormLabel required>Product SKU / Code</FormLabel>
              <Input
                placeholder="e.g. HW-SRV-001"
                value={newProduct.sku}
                onChange={(e) => setNewProduct({ ...newProduct, sku: e.target.value })}
                required
              />
            </FormItem>

            <FormItem>
              <FormLabel required>Product Name</FormLabel>
              <Input
                placeholder="Enterprise Server R750"
                value={newProduct.name}
                onChange={(e) => setNewProduct({ ...newProduct, name: e.target.value })}
                required
              />
            </FormItem>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <FormItem>
              <FormLabel>Category (Phase 072)</FormLabel>
              <Select
                value={newProduct.category_id || ""}
                onChange={(e) =>
                  setNewProduct({ ...newProduct, category_id: e.target.value || null })
                }
              >
                <option value="">No Category</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.code})
                  </option>
                ))}
              </Select>
            </FormItem>

            <FormItem>
              <FormLabel required>Unit of Measure (Phase 077)</FormLabel>
              <Select
                value={newProduct.unit || "unit"}
                onChange={(e) => setNewProduct({ ...newProduct, unit: e.target.value })}
              >
                {units.length > 0 ? (
                  units.map((u) => (
                    <option key={u.id} value={u.code.toLowerCase()}>
                      {u.name} ({u.code})
                    </option>
                  ))
                ) : (
                  <>
                    <option value="unit">Standard Unit</option>
                    <option value="license">Software License</option>
                    <option value="package">Package</option>
                    <option value="year">Annual Term</option>
                    <option value="month">Monthly Term</option>
                    <option value="hour">Hourly</option>
                  </>
                )}
              </Select>
            </FormItem>

            <FormItem>
              <FormLabel required>Tax Rate % (Phase 076)</FormLabel>
              <Input
                type="number"
                step="0.01"
                min="0"
                placeholder="0.00"
                value={newProduct.tax_rate}
                onChange={(e) => setNewProduct({ ...newProduct, tax_rate: e.target.value })}
                required
              />
            </FormItem>
          </div>

          {/* Subscription Toggle (Phase 080) */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-purple-50/50 border border-purple-100">
            <div>
              <div className="text-sm font-semibold text-purple-900">Subscription Product (Phase 080)</div>
              <div className="text-xs text-purple-700">
                Designate product as an ongoing subscription or recurring service.
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                className="sr-only peer"
                checked={Boolean(newProduct.is_subscription)}
                onChange={(e) =>
                  setNewProduct({ ...newProduct, is_subscription: e.target.checked })
                }
              />
              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>

          {/* Recurring Frequency Selector (Phase 081) */}
          {newProduct.is_subscription && (
            <div className="p-3.5 rounded-lg bg-purple-50 border border-purple-200">
              <FormItem>
                <FormLabel required>Recurring Billing Frequency (Phase 081)</FormLabel>
                <Select
                  value={newProduct.recurring_frequency || "monthly"}
                  onChange={(e) =>
                    setNewProduct({
                      ...newProduct,
                      recurring_frequency: e.target.value as "monthly" | "quarterly" | "yearly",
                    })
                  }
                >
                  <option value="monthly">Monthly Billing Cycle</option>
                  <option value="quarterly">Quarterly Billing Cycle</option>
                  <option value="yearly">Yearly Billing Cycle</option>
                </Select>
                <span className="text-xs text-purple-700 mt-1 block">
                  Defines customer recurring charge cadence for subscription-based items.
                </span>
              </FormItem>
            </div>
          )}

          {/* Inventory Controls (Phase 082) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-3.5 rounded-lg bg-slate-50 border border-border">
            <FormItem>
              <FormLabel required>Inventory Quantity (Phase 082)</FormLabel>
              <Input
                type="number"
                min="0"
                step="1"
                placeholder="0"
                value={newProduct.inventory_quantity ?? 0}
                onChange={(e) =>
                  setNewProduct({
                    ...newProduct,
                    inventory_quantity: Math.max(0, parseInt(e.target.value || "0", 10)),
                  })
                }
                required
              />
              <span className="text-xs text-muted">Current on-hand available units</span>
            </FormItem>

            <FormItem>
              <FormLabel required>Low Stock Threshold (Phase 082)</FormLabel>
              <Input
                type="number"
                min="0"
                step="1"
                placeholder="5"
                value={newProduct.low_stock_threshold ?? 5}
                onChange={(e) =>
                  setNewProduct({
                    ...newProduct,
                    low_stock_threshold: Math.max(0, parseInt(e.target.value || "0", 10)),
                  })
                }
                required
              />
              <span className="text-xs text-muted">Alert trigger when stock &le; threshold</span>
            </FormItem>
          </div>

          {/* Pricing, Cost & Margin Row (Phases 073, 074, 075) */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-3.5 rounded-lg bg-slate-50 border border-border">
            <FormItem>
              <FormLabel required>Selling Price (Phase 073)</FormLabel>
              <Input
                type="number"
                step="0.01"
                min="0"
                placeholder="0.00"
                value={newProduct.base_price}
                onChange={(e) => setNewProduct({ ...newProduct, base_price: e.target.value })}
                required
              />
            </FormItem>

            <FormItem>
              <FormLabel required>Product Cost (Phase 074)</FormLabel>
              <Input
                type="number"
                step="0.01"
                min="0"
                placeholder="0.00"
                value={newProduct.cost}
                onChange={(e) => setNewProduct({ ...newProduct, cost: e.target.value })}
                required
              />
            </FormItem>

            <div className="flex flex-col justify-center">
              <span className="text-xs font-semibold text-muted uppercase">
                Gross Margin (Phase 075)
              </span>
              <div className="mt-1">
                {renderMarginBadge(newProductMargin.marginAmount, newProductMargin.marginPct)}
              </div>
            </div>
          </div>

          <FormItem>
            <FormLabel>Product Description</FormLabel>
            <Textarea
              placeholder="Technical specifications, components, or catalog overview..."
              value={newProduct.description || ""}
              onChange={(e) => setNewProduct({ ...newProduct, description: e.target.value })}
              rows={3}
            />
          </FormItem>

          <div className="flex justify-end gap-2 pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsCreateProductOpen(false)}
              disabled={createProductLoading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={createProductLoading}>
              Create Product
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Product Modal */}
      <Modal
        isOpen={Boolean(editingProduct)}
        onClose={() => setEditingProduct(null)}
        title="Edit Product"
        description="Update product pricing, cost, tax rate, unit, and subscription status."
        size="lg"
      >
        {editingProduct && (
          <form onSubmit={handleUpdateProduct} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormItem>
                <FormLabel>Product SKU</FormLabel>
                <Input value={editingProduct.sku} disabled className="bg-slate-50" />
              </FormItem>

              <FormItem>
                <FormLabel required>Product Name</FormLabel>
                <Input
                  value={editingProduct.name}
                  onChange={(e) => setEditingProduct({ ...editingProduct, name: e.target.value })}
                  required
                />
              </FormItem>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <FormItem>
                <FormLabel>Category (Phase 072)</FormLabel>
                <Select
                  value={editingProduct.category_id || ""}
                  onChange={(e) =>
                    setEditingProduct({
                      ...editingProduct,
                      category_id: e.target.value || null,
                    })
                  }
                >
                  <option value="">No Category</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.code})
                    </option>
                  ))}
                </Select>
              </FormItem>

              <FormItem>
                <FormLabel required>Unit of Measure (Phase 077)</FormLabel>
                <Select
                  value={editingProduct.unit || "unit"}
                  onChange={(e) => setEditingProduct({ ...editingProduct, unit: e.target.value })}
                >
                  {units.map((u) => (
                    <option key={u.id} value={u.code.toLowerCase()}>
                      {u.name} ({u.code})
                    </option>
                  ))}
                </Select>
              </FormItem>

              <FormItem>
                <FormLabel required>Tax Rate % (Phase 076)</FormLabel>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={editingProduct.tax_rate}
                  onChange={(e) =>
                    setEditingProduct({ ...editingProduct, tax_rate: e.target.value })
                  }
                  required
                />
              </FormItem>
            </div>

            {/* Subscription Toggle (Phase 080) */}
            <div className="flex items-center justify-between p-3 rounded-lg bg-purple-50/50 border border-purple-100">
              <div>
                <div className="text-sm font-semibold text-purple-900">Subscription Product (Phase 080)</div>
                <div className="text-xs text-purple-700">
                  Designate product as an ongoing subscription or recurring service.
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={Boolean(editingProduct.is_subscription)}
                  onChange={(e) =>
                    setEditingProduct({ ...editingProduct, is_subscription: e.target.checked })
                  }
                />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>

            {/* Recurring Frequency Selector (Phase 081) */}
            {editingProduct.is_subscription && (
              <div className="p-3.5 rounded-lg bg-purple-50 border border-purple-200">
                <FormItem>
                  <FormLabel required>Recurring Billing Frequency (Phase 081)</FormLabel>
                  <Select
                    value={editingProduct.recurring_frequency || "monthly"}
                    onChange={(e) =>
                      setEditingProduct({
                        ...editingProduct,
                        recurring_frequency: e.target.value as "monthly" | "quarterly" | "yearly",
                      })
                    }
                  >
                    <option value="monthly">Monthly Billing Cycle</option>
                    <option value="quarterly">Quarterly Billing Cycle</option>
                    <option value="yearly">Yearly Billing Cycle</option>
                  </Select>
                  <span className="text-xs text-purple-700 mt-1 block">
                    Defines customer recurring charge cadence for subscription-based items.
                  </span>
                </FormItem>
              </div>
            )}

            {/* Inventory Controls (Phase 082) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-3.5 rounded-lg bg-slate-50 border border-border">
              <FormItem>
                <FormLabel required>Inventory Quantity (Phase 082)</FormLabel>
                <Input
                  type="number"
                  min="0"
                  step="1"
                  placeholder="0"
                  value={editingProduct.inventory_quantity ?? 0}
                  onChange={(e) =>
                    setEditingProduct({
                      ...editingProduct,
                      inventory_quantity: Math.max(0, parseInt(e.target.value || "0", 10)),
                    })
                  }
                  required
                />
                <span className="text-xs text-muted">Current on-hand available units</span>
              </FormItem>

              <FormItem>
                <FormLabel required>Low Stock Threshold (Phase 082)</FormLabel>
                <Input
                  type="number"
                  min="0"
                  step="1"
                  placeholder="5"
                  value={editingProduct.low_stock_threshold ?? 5}
                  onChange={(e) =>
                    setEditingProduct({
                      ...editingProduct,
                      low_stock_threshold: Math.max(0, parseInt(e.target.value || "0", 10)),
                    })
                  }
                  required
                />
                <span className="text-xs text-muted">Alert trigger when stock &le; threshold</span>
              </FormItem>
            </div>

            {/* Pricing, Cost & Margin Row */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-3.5 rounded-lg bg-slate-50 border border-border">
              <FormItem>
                <FormLabel required>Selling Price (Phase 073)</FormLabel>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={editingProduct.base_price}
                  onChange={(e) =>
                    setEditingProduct({ ...editingProduct, base_price: e.target.value })
                  }
                  required
                />
              </FormItem>

              <FormItem>
                <FormLabel required>Product Cost (Phase 074)</FormLabel>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={editingProduct.cost}
                  onChange={(e) =>
                    setEditingProduct({ ...editingProduct, cost: e.target.value })
                  }
                  required
                />
              </FormItem>

              <div className="flex flex-col justify-center">
                <span className="text-xs font-semibold text-muted uppercase">
                  Gross Margin (Phase 075)
                </span>
                <div className="mt-1">
                  {editProductMargin &&
                    renderMarginBadge(editProductMargin.marginAmount, editProductMargin.marginPct)}
                </div>
              </div>
            </div>

            <FormItem>
              <FormLabel>Product Description</FormLabel>
              <Textarea
                value={editingProduct.description || ""}
                onChange={(e) =>
                  setEditingProduct({ ...editingProduct, description: e.target.value })
                }
                rows={3}
              />
            </FormItem>

            <div className="flex justify-end gap-2 pt-4 border-t border-border">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setEditingProduct(null)}
                disabled={editProductLoading}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" isLoading={editProductLoading}>
                Save Changes
              </Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Delete Product Confirmation Modal */}
      <Modal
        isOpen={Boolean(deletingProduct)}
        onClose={() => setDeletingProduct(null)}
        title="Deactivate Product"
        description={`Are you sure you want to deactivate "${deletingProduct?.name}" (${deletingProduct?.sku})?`}
        variant="destructive"
        confirmLabel="Deactivate Product"
        onConfirm={handleDeleteProduct}
        isLoading={deleteProductLoading}
      />

      {/* Product Variants Management Modal (Phase 078) */}
      <Modal
        isOpen={Boolean(managingVariantsProduct)}
        onClose={() => setManagingVariantsProduct(null)}
        title={`Variants: ${managingVariantsProduct?.name}`}
        description={`Parent SKU: ${managingVariantsProduct?.sku} | Base Price: $${Number(managingVariantsProduct?.base_price || 0).toFixed(2)}`}
        size="xl"
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground">
              Configured Product Variants ({productVariants.length})
            </h3>
            <Button
              size="sm"
              variant="primary"
              onClick={() => setIsCreateVariantOpen(true)}
              className="gap-1.5"
            >
              <Plus className="h-4 w-4" />
              <span>Add Variant</span>
            </Button>
          </div>

          {loadingVariants ? (
            <div className="py-8 text-center text-sm text-muted">Loading variants...</div>
          ) : productVariants.length === 0 ? (
            <div className="py-8 text-center text-sm text-muted border border-dashed rounded-lg">
              No variants configured for this product.
            </div>
          ) : (
            <div className="overflow-x-auto border border-border rounded-lg">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 border-b border-border text-slate-700 font-semibold uppercase">
                  <tr>
                    <th className="px-3 py-2">Variant SKU</th>
                    <th className="px-3 py-2">Variant Name</th>
                    <th className="px-3 py-2">Selling Price Override</th>
                    <th className="px-3 py-2">Cost Override</th>
                    <th className="px-3 py-2">Attributes</th>
                    <th className="px-3 py-2 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {productVariants.map((v) => (
                    <tr key={v.id} className="hover:bg-slate-50/50">
                      <td className="px-3 py-2 font-mono font-semibold text-slate-800">{v.sku}</td>
                      <td className="px-3 py-2 font-medium">{v.name}</td>
                      <td className="px-3 py-2 font-mono">
                        {v.base_price ? `$${Number(v.base_price).toFixed(2)}` : <span className="text-slate-400 italic">Inherited</span>}
                      </td>
                      <td className="px-3 py-2 font-mono">
                        {v.cost ? `$${Number(v.cost).toFixed(2)}` : <span className="text-slate-400 italic">Inherited</span>}
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex flex-wrap gap-1">
                          {v.attribute_values?.map((av) => (
                            <Badge key={av.id} variant="secondary" className="text-[10px]">
                              {av.value}
                            </Badge>
                          ))}
                        </div>
                      </td>
                      <td className="px-3 py-2 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 px-2 text-rose-600 hover:bg-rose-50"
                          onClick={() => handleDeleteVariant(v.id)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </Modal>

      {/* Add Variant Modal (Phase 078) */}
      <Modal
        isOpen={isCreateVariantOpen}
        onClose={() => setIsCreateVariantOpen(false)}
        title="Add Product Variant"
        description={`Add variation under ${managingVariantsProduct?.name}`}
        size="md"
      >
        <form onSubmit={handleCreateVariant} className="space-y-4">
          <FormItem>
            <FormLabel required>Variant SKU</FormLabel>
            <Input
              placeholder="e.g. HW-SRV-001-64G"
              value={newVariant.sku}
              onChange={(e) => setNewVariant({ ...newVariant, sku: e.target.value })}
              required
            />
          </FormItem>

          <FormItem>
            <FormLabel required>Variant Name</FormLabel>
            <Input
              placeholder="Enterprise Server (64GB RAM Edition)"
              value={newVariant.name}
              onChange={(e) => setNewVariant({ ...newVariant, name: e.target.value })}
              required
            />
          </FormItem>

          <div className="grid grid-cols-2 gap-4">
            <FormItem>
              <FormLabel>Selling Price Override</FormLabel>
              <Input
                type="number"
                step="0.01"
                min="0"
                placeholder="Leave blank to inherit"
                value={newVariant.base_price || ""}
                onChange={(e) => setNewVariant({ ...newVariant, base_price: e.target.value })}
              />
            </FormItem>

            <FormItem>
              <FormLabel>Cost Override</FormLabel>
              <Input
                type="number"
                step="0.01"
                min="0"
                placeholder="Leave blank to inherit"
                value={newVariant.cost || ""}
                onChange={(e) => setNewVariant({ ...newVariant, cost: e.target.value })}
              />
            </FormItem>
          </div>

          {/* Select Attribute Values (Phase 079) */}
          {attributes.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-border">
              <FormLabel>Select Attributes &amp; Options</FormLabel>
              <div className="space-y-2 max-h-40 overflow-y-auto p-2 bg-slate-50 rounded border border-border">
                {attributes.map((attr) => (
                  <div key={attr.id} className="text-xs">
                    <span className="font-semibold text-slate-700">{attr.name}:</span>
                    <div className="flex flex-wrap gap-1.5 mt-1">
                      {attr.values?.map((val) => {
                        const isSelected = newVariant.attribute_value_ids?.includes(val.id);
                        return (
                          <button
                            key={val.id}
                            type="button"
                            onClick={() => {
                              const current = newVariant.attribute_value_ids || [];
                              if (isSelected) {
                                setNewVariant({
                                  ...newVariant,
                                  attribute_value_ids: current.filter((id) => id !== val.id),
                                });
                              } else {
                                setNewVariant({
                                  ...newVariant,
                                  attribute_value_ids: [...current, val.id],
                                });
                              }
                            }}
                            className={`px-2 py-0.5 rounded border text-[11px] transition-colors ${
                              isSelected
                                ? "bg-primary text-primary-foreground border-primary font-medium"
                                : "bg-white text-slate-700 border-slate-200 hover:border-slate-300"
                            }`}
                          >
                            {val.value}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsCreateVariantOpen(false)}
              disabled={createVariantLoading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={createVariantLoading}>
              Save Variant
            </Button>
          </div>
        </form>
      </Modal>

      {/* Add Unit Modal (Phase 077) */}
      <Modal
        isOpen={isCreateUnitOpen}
        onClose={() => setIsCreateUnitOpen(false)}
        title="Add Unit of Measure"
        description="Register a standardized unit of measure (e.g., BOX, KG, LICENSE)."
        size="md"
      >
        <form onSubmit={handleCreateUnit} className="space-y-4">
          <FormItem>
            <FormLabel required>Unit Code</FormLabel>
            <Input
              placeholder="e.g. PACK"
              value={newUnit.code}
              onChange={(e) => setNewUnit({ ...newUnit, code: e.target.value })}
              required
            />
          </FormItem>

          <FormItem>
            <FormLabel required>Display Name</FormLabel>
            <Input
              placeholder="e.g. Multi-Pack Box"
              value={newUnit.name}
              onChange={(e) => setNewUnit({ ...newUnit, name: e.target.value })}
              required
            />
          </FormItem>

          <FormItem>
            <FormLabel>Description</FormLabel>
            <Input
              placeholder="Description of the measurement standard"
              value={newUnit.description || ""}
              onChange={(e) => setNewUnit({ ...newUnit, description: e.target.value })}
            />
          </FormItem>

          <div className="flex justify-end gap-2 pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsCreateUnitOpen(false)}
              disabled={createUnitLoading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={createUnitLoading}>
              Create Unit
            </Button>
          </div>
        </form>
      </Modal>

      {/* Add Attribute Modal (Phase 079) */}
      <Modal
        isOpen={isCreateAttributeOpen}
        onClose={() => setIsCreateAttributeOpen(false)}
        title="Add Product Attribute"
        description="Define a reusable attribute category (e.g. Color, Storage, Size)."
        size="md"
      >
        <form onSubmit={handleCreateAttribute} className="space-y-4">
          <FormItem>
            <FormLabel required>Attribute Code</FormLabel>
            <Input
              placeholder="e.g. STORAGE_SIZE"
              value={newAttribute.code}
              onChange={(e) => setNewAttribute({ ...newAttribute, code: e.target.value })}
              required
            />
          </FormItem>

          <FormItem>
            <FormLabel required>Attribute Name</FormLabel>
            <Input
              placeholder="e.g. Storage Capacity"
              value={newAttribute.name}
              onChange={(e) => setNewAttribute({ ...newAttribute, name: e.target.value })}
              required
            />
          </FormItem>

          <FormItem>
            <FormLabel>Description</FormLabel>
            <Input
              placeholder="Attribute description..."
              value={newAttribute.description || ""}
              onChange={(e) => setNewAttribute({ ...newAttribute, description: e.target.value })}
            />
          </FormItem>

          <div className="flex justify-end gap-2 pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsCreateAttributeOpen(false)}
              disabled={createAttributeLoading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={createAttributeLoading}>
              Create Attribute
            </Button>
          </div>
        </form>
      </Modal>

      {/* Add Attribute Value Modal (Phase 079) */}
      <Modal
        isOpen={Boolean(selectedAttributeForValue)}
        onClose={() => setSelectedAttributeForValue(null)}
        title={`Add Option: ${selectedAttributeForValue?.name}`}
        description={`Add a choice or value for attribute ${selectedAttributeForValue?.code}`}
        size="sm"
      >
        <form onSubmit={handleAddAttributeValue} className="space-y-4">
          <FormItem>
            <FormLabel required>Option Value</FormLabel>
            <Input
              placeholder="e.g. 512GB, Red, Large..."
              value={newValueInput}
              onChange={(e) => setNewValueInput(e.target.value)}
              required
            />
          </FormItem>

          <div className="flex justify-end gap-2 pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setSelectedAttributeForValue(null)}
              disabled={addValueLoading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={addValueLoading}>
              Add Option
            </Button>
          </div>
        </form>
      </Modal>

      {/* Add Category Modal (Phase 072) */}
      <Modal
        isOpen={isCreateCategoryOpen}
        onClose={() => setIsCreateCategoryOpen(false)}
        title="Add Product Category"
        description="Create a product classification grouping."
        size="md"
      >
        <form onSubmit={handleCreateCategory} className="space-y-4">
          <FormItem>
            <FormLabel required>Category Code</FormLabel>
            <Input
              placeholder="e.g. CAT-NET"
              value={newCategory.code}
              onChange={(e) => setNewCategory({ ...newCategory, code: e.target.value })}
              required
            />
          </FormItem>

          <FormItem>
            <FormLabel required>Category Name</FormLabel>
            <Input
              placeholder="Networking & Hardware"
              value={newCategory.name}
              onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })}
              required
            />
          </FormItem>

          <FormItem>
            <FormLabel>Description</FormLabel>
            <Input
              placeholder="Switches, routers, gateways..."
              value={newCategory.description || ""}
              onChange={(e) => setNewCategory({ ...newCategory, description: e.target.value })}
            />
          </FormItem>

          <div className="flex justify-end gap-2 pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsCreateCategoryOpen(false)}
              disabled={createCategoryLoading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={createCategoryLoading}>
              Create Category
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Category Modal (Phase 072) */}
      <Modal
        isOpen={Boolean(editingCategory)}
        onClose={() => setEditingCategory(null)}
        title="Edit Product Category"
        description="Update category name and status."
        size="md"
      >
        {editingCategory && (
          <form onSubmit={handleUpdateCategory} className="space-y-4">
            <FormItem>
              <FormLabel>Category Code</FormLabel>
              <Input value={editingCategory.code} disabled className="bg-slate-50" />
            </FormItem>

            <FormItem>
              <FormLabel required>Category Name</FormLabel>
              <Input
                value={editingCategory.name}
                onChange={(e) =>
                  setEditingCategory({ ...editingCategory, name: e.target.value })
                }
                required
              />
            </FormItem>

            <FormItem>
              <FormLabel>Description</FormLabel>
              <Input
                value={editingCategory.description || ""}
                onChange={(e) =>
                  setEditingCategory({ ...editingCategory, description: e.target.value })
                }
              />
            </FormItem>

            <FormItem>
              <FormLabel>Category Status</FormLabel>
              <Select
                value={editingCategory.is_active ? "true" : "false"}
                onChange={(e) =>
                  setEditingCategory({
                    ...editingCategory,
                    is_active: e.target.value === "true",
                  })
                }
              >
                <option value="true">Active Category</option>
                <option value="false">Inactive / Hidden</option>
              </Select>
            </FormItem>

            <div className="flex justify-end gap-2 pt-4 border-t border-border">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setEditingCategory(null)}
                disabled={editCategoryLoading}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" isLoading={editCategoryLoading}>
                Save Changes
              </Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Delete Category Confirmation Modal */}
      <Modal
        isOpen={Boolean(deletingCategory)}
        onClose={() => setDeletingCategory(null)}
        title="Deactivate Category"
        description={`Are you sure you want to deactivate "${deletingCategory?.name}" (${deletingCategory?.code})?`}
        variant="destructive"
        confirmLabel="Deactivate Category"
        onConfirm={handleDeleteCategory}
        isLoading={deleteCategoryLoading}
      />
    </div>
  );
}
