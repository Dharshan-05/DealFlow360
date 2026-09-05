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
  ExternalLink,
} from "lucide-react";

import { useToast } from "@/context/ToastContext";
import { useAuth } from "@/context/AuthContext";
import { productsApi, productCategoriesApi } from "@/lib/api";
import {
  Product,
  ProductCategory,
  ProductCreateInput,
  ProductUpdateInput,
  ProductCategoryCreateInput,
  ProductCategoryUpdateInput,
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

export default function ProductsPage() {
  const { user } = useAuth();
  const toast = useToast();

  // Core Data State
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<ProductCategory[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Active View Tab: "products" | "categories"
  const [activeTab, setActiveTab] = useState<"products" | "categories">("products");

  // Create Product Modal (Phase 071)
  const [isCreateProductOpen, setIsCreateProductOpen] = useState<boolean>(false);
  const [createProductLoading, setCreateProductLoading] = useState<boolean>(false);
  const [newProduct, setNewProduct] = useState<ProductCreateInput>({
    sku: "",
    name: "",
    description: "",
    category_id: "",
    cost: "0.00",
    base_price: "0.00",
    is_active: true,
  });

  // Edit Product Modal (Phase 071)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [editProductLoading, setEditProductLoading] = useState<boolean>(false);

  // Delete Product Modal (Phase 071)
  const [deletingProduct, setDeletingProduct] = useState<Product | null>(null);
  const [deleteProductLoading, setDeleteProductLoading] = useState<boolean>(false);

  // Create Category Modal (Phase 072)
  const [isCreateCategoryOpen, setIsCreateCategoryOpen] = useState<boolean>(false);
  const [createCategoryLoading, setCreateCategoryLoading] = useState<boolean>(false);
  const [newCategory, setNewCategory] = useState<ProductCategoryCreateInput>({
    name: "",
    code: "",
    description: "",
    is_active: true,
  });

  // Edit Category Modal (Phase 072)
  const [editingCategory, setEditingCategory] = useState<ProductCategory | null>(null);
  const [editCategoryLoading, setEditCategoryLoading] = useState<boolean>(false);

  // Delete Category Modal (Phase 072)
  const [deletingCategory, setDeletingCategory] = useState<ProductCategory | null>(null);
  const [deleteCategoryLoading, setDeleteCategoryLoading] = useState<boolean>(false);

  // Load Data
  const loadData = useCallback(async () => {
    try {
      setError(null);
      const [prodRes, catRes] = await Promise.all([
        productsApi.getAll({ limit: 100 }),
        productCategoriesApi.getAll(true),
      ]);
      setProducts(prodRes.items);
      setCategories(catRes);
    } catch (err: any) {
      setError(err.message || "Failed to load product catalog.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadData();
  };

  // Live margin computation helper for create/edit forms
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

  // Create Product Submit
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
        is_active: true,
      });
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to create product.");
    } finally {
      setCreateProductLoading(false);
    }
  };

  // Update Product Submit
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

  // Delete Product Submit
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

  // Create Category Submit (Phase 072)
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
      toast.success(`Category "${newCategory.name}" created successfully.`);
      setIsCreateCategoryOpen(false);
      setNewCategory({
        name: "",
        code: "",
        description: "",
        is_active: true,
      });
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to create category.");
    } finally {
      setCreateCategoryLoading(false);
    }
  };

  // Update Category Submit (Phase 072)
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
      toast.success(`Category "${editingCategory.name}" updated successfully.`);
      setEditingCategory(null);
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Failed to update category.");
    } finally {
      setEditCategoryLoading(false);
    }
  };

  // Delete Category Submit (Phase 072)
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

  // Margin Styling Helper (Phase 075)
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
          <span className="font-mono text-xs font-semibold text-amber-700">
            $0.00
          </span>
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

  // Product Table Columns (Phase 071–075)
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
          <div className="font-semibold text-sm text-foreground">{row.name}</div>
          {row.description && (
            <div className="text-xs text-muted truncate max-w-xs">{row.description}</div>
          )}
        </div>
      ),
    },
    {
      id: "category",
      header: "Category (Phase 072)",
      cell: (row) =>
        row.category ? (
          <Badge variant="secondary" className="gap-1 font-medium">
            <Tags className="h-3 w-3" />
            {row.category.name}
          </Badge>
        ) : (
          <span className="text-xs text-slate-400 italic">Uncategorized</span>
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
      header: "Margin (Phase 075)",
      cell: (row) => renderMarginBadge(row.margin_amount, row.margin_percentage),
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

  // Category Table Columns (Phase 072)
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
          {row.description && (
            <div className="text-xs text-muted truncate max-w-sm">{row.description}</div>
          )}
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

  // Live margins for modals
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
              G15 (Phases 071–075)
            </Badge>
          </div>
          <p className="text-sm text-muted mt-1">
            Maintain catalog offerings, product categories, base pricing, unit costs, and gross margins.
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

          {activeTab === "products" ? (
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsCreateProductOpen(true)}
              className="gap-1.5"
            >
              <Plus className="h-4 w-4" />
              <span>Add Product</span>
            </Button>
          ) : (
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
        </div>
      </div>

      {/* KPI Overview Summary (Phase 071–075) */}
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
            <div className="p-2.5 rounded-lg bg-indigo-50 text-indigo-600">
              <Tags className="h-5 w-5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-muted uppercase tracking-wider">
                Categories
              </div>
              <div className="text-2xl font-bold text-foreground mt-0.5">
                {categories.length}
              </div>
              <div className="text-[11px] text-muted">
                {categories.filter((c) => c.is_active).length} active classifications
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

      {/* Tabs: Products Directory vs Categories */}
      <div className="border-b border-border">
        <div className="flex items-center gap-6">
          <button
            type="button"
            onClick={() => setActiveTab("products")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
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
            onClick={() => setActiveTab("categories")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === "categories"
                ? "border-primary text-primary"
                : "border-transparent text-muted hover:text-foreground"
            }`}
          >
            <Tags className="h-4 w-4" />
            <span>Product Categories (Phase 072) ({categories.length})</span>
          </button>
        </div>
      </div>

      {/* Active Tab View */}
      {activeTab === "products" ? (
        <DataTable
          columns={productColumns}
          data={products}
          keyExtractor={(item) => item.id}
          isLoading={isLoading}
          error={error}
          onRetry={loadData}
          emptyTitle="No products in catalog"
          emptyDescription="Add products with selling prices and unit costs to establish margins."
          emptyAction={
            <Button size="sm" onClick={() => setIsCreateProductOpen(true)} className="gap-1.5 mt-2">
              <Plus className="h-4 w-4" />
              <span>Create First Product</span>
            </Button>
          }
        />
      ) : (
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

      {/* Add Product Modal (Phase 071, 073, 074, 075) */}
      <Modal
        isOpen={isCreateProductOpen}
        onClose={() => setIsCreateProductOpen(false)}
        title="Add Catalog Product"
        description="Register a new product with selling price, unit cost, and live gross margin."
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

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormItem>
              <FormLabel>Product Category (Phase 072)</FormLabel>
              <Select
                value={newProduct.category_id || ""}
                onChange={(e) =>
                  setNewProduct({ ...newProduct, category_id: e.target.value || null })
                }
              >
                <option value="">No Category (Uncategorized)</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.code})
                  </option>
                ))}
              </Select>
            </FormItem>

            <FormItem>
              <FormLabel>Status</FormLabel>
              <Select
                value={newProduct.is_active ? "true" : "false"}
                onChange={(e) =>
                  setNewProduct({ ...newProduct, is_active: e.target.value === "true" })
                }
              >
                <option value="true">Active in Catalog</option>
                <option value="false">Inactive / Draft</option>
              </Select>
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
        description="Update product pricing, cost, and catalog details."
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
                  onChange={(e) =>
                    setEditingProduct({ ...editingProduct, name: e.target.value })
                  }
                  required
                />
              </FormItem>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormItem>
                <FormLabel>Product Category (Phase 072)</FormLabel>
                <Select
                  value={editingProduct.category_id || ""}
                  onChange={(e) =>
                    setEditingProduct({
                      ...editingProduct,
                      category_id: e.target.value || null,
                    })
                  }
                >
                  <option value="">No Category (Uncategorized)</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.code})
                    </option>
                  ))}
                </Select>
              </FormItem>

              <FormItem>
                <FormLabel>Status</FormLabel>
                <Select
                  value={editingProduct.is_active ? "true" : "false"}
                  onChange={(e) =>
                    setEditingProduct({
                      ...editingProduct,
                      is_active: e.target.value === "true",
                    })
                  }
                >
                  <option value="true">Active in Catalog</option>
                  <option value="false">Inactive / Suspended</option>
                </Select>
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
        description={`Are you sure you want to deactivate "${deletingProduct?.name}" (${deletingProduct?.sku})? This will remove it from active quote selection while preserving historical records.`}
        variant="destructive"
        confirmLabel="Deactivate Product"
        onConfirm={handleDeleteProduct}
        isLoading={deleteProductLoading}
      />

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
