/**
 * Centralized API client for DealFlow360 frontend (G08 Security Hardening).
 * 
 * Security Architecture:
 * - Access token is kept strictly in-memory (never in localStorage or sessionStorage) to mitigate XSS risks.
 * - Refresh token is stored in a Secure, HttpOnly cookie managed by the browser.
 * - API requests automatically attach the in-memory Bearer access token and use credentials: "include".
 * - Automatic 401 refresh interceptor handles silent token rotation without infinite loops.
 */
import { ApiResponse } from "@/types/api";
import { LoginRequest, RegisterRequest, TokenResponse, User } from "@/types/auth";
import {
  Customer,
  CustomerAnalyticsSummary,
  CustomerCreateInput,
  CustomerDashboardResponse,
  CustomerDealHistory,
  CustomerDiscountHistory,
  CustomerFinancialIntelligence,
  CustomerListResponse,
  CustomerPaymentHistory,
  CustomerPurchaseHistory,
  CustomerSegmentationSummary,
  CustomerTier,
  CustomerUpdateInput,
  DealHistoryCreateInput,
  DiscountHistoryCreateInput,
  PaymentHistoryCreateInput,
  PurchaseHistoryCreateInput,
} from "@/types/customer";
import {
  Product,
  ProductAttribute,
  ProductAttributeCreateInput,
  ProductAttributeUpdateInput,
  ProductAttributeValue,
  ProductAttributeValueCreateInput,
  ProductCategory,
  ProductCategoryCreateInput,
  ProductCategoryUpdateInput,
  ProductCreateInput,
  ProductDashboardData,
  ProductListResponse,
  ProductUnit,
  ProductUnitCreateInput,
  ProductUnitUpdateInput,
  ProductUpdateInput,
  ProductVariant,
  ProductVariantCreateInput,
  ProductVariantUpdateInput,
} from "@/types/product";
import {
  AllocationResponse,
  ATPData,
  MultiWarehouseReleaseResponse,
  MultiWarehouseReservationResponse,
  MultiWarehouseStockResponse,
  StockAvailability,
  StockReserveReleaseInput,
  Warehouse,
  WarehouseCreateInput,
  WarehouseListResponse,
  WarehouseReleaseItem,
  WarehouseSelectionResponse,
  WarehouseStock,
  WarehouseStockCreateInput,
  WarehouseStockListResponse,
  WarehouseStockUpdateInput,
  WarehouseUpdateInput,
} from "@/types/warehouse";
import {
  Backorder,
  BackorderCreateInput,
  BackorderListResponse,
  Fulfillment,
  FulfillmentCreateInput,
  FulfillmentDeliveryStatusUpdateInput,
  FulfillmentListResponse,
  InventoryAlert,
  InventoryAlertListResponse,
  InventoryAlertScanResponse,
  InventoryDashboardResponse,
} from "@/types/inventory";
import {
  CategoryDiscountCeiling,
  CategoryDiscountCeilingCreateInput,
  CategoryDiscountCeilingListResponse,
  CategoryDiscountCeilingUpdateInput,
  CustomerDiscountCeiling,
  CustomerDiscountCeilingCreateInput,
  CustomerDiscountCeilingListResponse,
  CustomerDiscountCeilingUpdateInput,
  DiscountConfiguration,
  DiscountConfigurationCreateInput,
  DiscountConfigurationListResponse,
  DiscountConfigurationUpdateInput,
  DiscountPolicyEvaluationResponse,
  DiscountValidationRequest,
  FinanceAuthorityLimit,
  FinanceAuthorityLimitCreateInput,
  FinanceAuthorityLimitListResponse,
  FinanceAuthorityLimitUpdateInput,
  ManagerAuthorityLimit,
  ManagerAuthorityLimitCreateInput,
  ManagerAuthorityLimitListResponse,
  ManagerAuthorityLimitUpdateInput,
  ProductDiscountCeiling,
  ProductDiscountCeilingCreateInput,
  ProductDiscountCeilingListResponse,
  ProductDiscountCeilingUpdateInput,
  SalesRepAuthorityLimit,
  SalesRepAuthorityLimitCreateInput,
  SalesRepAuthorityLimitListResponse,
  SalesRepAuthorityLimitUpdateInput,
} from "@/types/discountGovernance";


const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// IN-MEMORY ACCESS TOKEN (XSS-resilient: not accessible via persistent browser storage)
let inMemoryAccessToken: string | null = null;

export function getAccessToken(): string | null {
  return inMemoryAccessToken;
}

export function setAccessToken(token: string | null): void {
  inMemoryAccessToken = token;
}

interface CustomRequestInit extends RequestInit {
  _isRetry?: boolean;
}

// Single-flight refresh deduplication promise
let refreshPromise: Promise<TokenResponse> | null = null;

export async function request<T>(
  endpoint: string,
  options: CustomRequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const token = getAccessToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const url = `${API_BASE_URL}${endpoint}`;
  let response: Response;

  try {
    response = await fetch(url, {
      ...options,
      headers,
      credentials: "include", // Ensure HttpOnly cookies are transported securely
    });
  } catch (netErr: any) {
    throw new Error(netErr?.message || "Network request failed. Please check your connection.");
  }

  // Handle 401 Unauthorized with single-flight automatic token refresh
  if (
    response.status === 401 &&
    !options._isRetry &&
    endpoint !== "/auth/login" &&
    endpoint !== "/auth/refresh"
  ) {
    try {
      if (!refreshPromise) {
        refreshPromise = authApi.refresh().finally(() => {
          refreshPromise = null;
        });
      }
      const newTokens = await refreshPromise;
      if (newTokens?.access_token) {
        setAccessToken(newTokens.access_token);
        headers.set("Authorization", `Bearer ${newTokens.access_token}`);
        return await request<T>(endpoint, {
          ...options,
          headers,
          _isRetry: true, // Prevent infinite refresh loop
        });
      }
    } catch {
      setAccessToken(null);
    }
  }

  let body: any = null;
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    try {
      body = await response.json();
    } catch {
      body = null;
    }
  } else {
    try {
      body = { message: await response.text() };
    } catch {
      body = null;
    }
  }

  if (!response.ok) {
    let errorMessage = "An unexpected error occurred.";
    if (body) {
      if (body.error && body.error.message) {
        errorMessage = body.error.message;
      } else if (body.detail) {
        errorMessage = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      } else if (body.message) {
        errorMessage = body.message;
      }
    }
    throw new Error(errorMessage);
  }

  return body as T;
}

export const authApi = {
  async register(data: RegisterRequest): Promise<User> {
    const res = await request<ApiResponse<User>>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Missing user data in registration response");
    return res.data;
  },

  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const res = await request<ApiResponse<TokenResponse>>("/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
    if (!res.data) throw new Error("Missing token data in login response");
    setAccessToken(res.data.access_token);
    return res.data;
  },

  async refresh(): Promise<TokenResponse> {
    const res = await request<ApiResponse<TokenResponse>>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({}), // Refresh token is read from HttpOnly cookie
    });
    if (!res.data) throw new Error("Failed to refresh session");
    setAccessToken(res.data.access_token);
    return res.data;
  },

  async getMe(): Promise<User> {
    const res = await request<ApiResponse<User>>("/auth/me", {
      method: "GET",
    });
    if (!res.data) throw new Error("Failed to load user profile");
    return res.data;
  },

  async logout(): Promise<void> {
    try {
      await request<ApiResponse<{ logged_out: boolean }>>("/auth/logout", {
        method: "POST",
        body: JSON.stringify({}), // Refresh token read and cleared from HttpOnly cookie
      });
    } finally {
      setAccessToken(null);
    }
  },
};

export const customersApi = {
  async getAll(params: {
    skip?: number;
    limit?: number;
    search?: string;
    tier_id?: string;
    is_active?: boolean;
  } = {}): Promise<CustomerListResponse> {
    const query = new URLSearchParams();
    if (params.skip !== undefined) query.set("skip", String(params.skip));
    if (params.limit !== undefined) query.set("limit", String(params.limit));
    if (params.search) query.set("search", params.search);
    if (params.tier_id) query.set("tier_id", params.tier_id);
    if (params.is_active !== undefined) query.set("is_active", String(params.is_active));

    const qs = query.toString() ? `?${query.toString()}` : "";
    const res = await request<ApiResponse<CustomerListResponse>>(`/customers${qs}`);
    if (!res.data) throw new Error("Failed to load customers list");
    return res.data;
  },

  async getById(id: string): Promise<Customer> {
    const res = await request<ApiResponse<Customer>>(`/customers/${id}`);
    if (!res.data) throw new Error("Failed to load customer profile");
    return res.data;
  },

  async create(data: CustomerCreateInput): Promise<Customer> {
    const res = await request<ApiResponse<Customer>>("/customers", {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to create customer");
    return res.data;
  },

  async update(id: string, data: CustomerUpdateInput): Promise<Customer> {
    const res = await request<ApiResponse<Customer>>(`/customers/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to update customer");
    return res.data;
  },

  async updateTier(id: string, tierId: string | null): Promise<Customer> {
    const res = await request<ApiResponse<Customer>>(`/customers/${id}/tier`, {
      method: "PATCH",
      body: JSON.stringify({ tier_id: tierId }),
    });
    if (!res.data) throw new Error("Failed to update customer tier");
    return res.data;
  },

  async delete(id: string, soft: boolean = true): Promise<void> {
    await request<ApiResponse<any>>(`/customers/${id}?soft=${soft}`, {
      method: "DELETE",
    });
  },

  async getPurchaseHistory(id: string): Promise<CustomerPurchaseHistory[]> {
    const res = await request<ApiResponse<CustomerPurchaseHistory[]>>(`/customers/${id}/purchase-history`);
    return res.data || [];
  },

  async createPurchaseHistory(
    id: string,
    data: PurchaseHistoryCreateInput
  ): Promise<CustomerPurchaseHistory> {
    const res = await request<ApiResponse<CustomerPurchaseHistory>>(`/customers/${id}/purchase-history`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to record purchase history");
    return res.data;
  },

  async getDealHistory(id: string): Promise<CustomerDealHistory[]> {
    const res = await request<ApiResponse<CustomerDealHistory[]>>(`/customers/${id}/deal-history`);
    return res.data || [];
  },

  async createDealHistory(
    id: string,
    data: DealHistoryCreateInput
  ): Promise<CustomerDealHistory> {
    const res = await request<ApiResponse<CustomerDealHistory>>(`/customers/${id}/deal-history`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to record deal history");
    return res.data;
  },

  async getDiscountHistory(id: string): Promise<CustomerDiscountHistory[]> {
    const res = await request<ApiResponse<CustomerDiscountHistory[]>>(`/customers/${id}/discount-history`);
    return res.data || [];
  },

  async createDiscountHistory(
    id: string,
    data: DiscountHistoryCreateInput
  ): Promise<CustomerDiscountHistory> {
    const res = await request<ApiResponse<CustomerDiscountHistory>>(`/customers/${id}/discount-history`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to record discount history");
    return res.data;
  },

  async getPaymentHistory(id: string): Promise<CustomerPaymentHistory[]> {
    const res = await request<ApiResponse<CustomerPaymentHistory[]>>(`/customers/${id}/payment-history`);
    return res.data || [];
  },

  async createPaymentHistory(
    id: string,
    data: PaymentHistoryCreateInput
  ): Promise<CustomerPaymentHistory> {
    const res = await request<ApiResponse<CustomerPaymentHistory>>(`/customers/${id}/payment-history`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to record payment history");
    return res.data;
  },

  async getFinancialIntelligence(id: string): Promise<CustomerFinancialIntelligence> {
    const res = await request<ApiResponse<CustomerFinancialIntelligence>>(`/customers/${id}/financial-intelligence`);
    if (!res.data) throw new Error("Failed to load customer financial intelligence");
    return res.data;
  },

  // Phases 066, 069, 070: Customer Analytics, Segmentation & Dashboard
  async getAnalytics(): Promise<CustomerAnalyticsSummary> {
    const res = await request<ApiResponse<CustomerAnalyticsSummary>>("/customers/analytics");
    if (!res.data) throw new Error("Failed to load customer analytics");
    return res.data;
  },

  async getSegmentation(): Promise<CustomerSegmentationSummary> {
    const res = await request<ApiResponse<CustomerSegmentationSummary>>("/customers/segmentation");
    if (!res.data) throw new Error("Failed to load customer segmentation");
    return res.data;
  },

  async getDashboard(): Promise<CustomerDashboardResponse> {
    const res = await request<ApiResponse<CustomerDashboardResponse>>("/customers/dashboard");
    if (!res.data) throw new Error("Failed to load customer dashboard");
    return res.data;
  },
};

export const customerTiersApi = {
  async getAll(): Promise<CustomerTier[]> {
    const res = await request<ApiResponse<CustomerTier[]>>("/customer-tiers");
    return res.data || [];
  },
};

// ===========================================================================
// Phases 071–075: Product & Category Management
// ===========================================================================

export const productCategoriesApi = {
  async getAll(includeInactive: boolean = false): Promise<ProductCategory[]> {
    const res = await request<ApiResponse<ProductCategory[]>>(
      `/product-categories?include_inactive=${includeInactive}`
    );
    return res.data || [];
  },

  async getById(id: string): Promise<ProductCategory> {
    const res = await request<ApiResponse<ProductCategory>>(`/product-categories/${id}`);
    if (!res.data) throw new Error("Failed to load category details");
    return res.data;
  },

  async create(data: ProductCategoryCreateInput): Promise<ProductCategory> {
    const res = await request<ApiResponse<ProductCategory>>("/product-categories", {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to create product category");
    return res.data;
  },

  async update(id: string, data: ProductCategoryUpdateInput): Promise<ProductCategory> {
    const res = await request<ApiResponse<ProductCategory>>(`/product-categories/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to update product category");
    return res.data;
  },

  async delete(id: string, soft: boolean = true): Promise<void> {
    await request<ApiResponse<any>>(`/product-categories/${id}?soft=${soft}`, {
      method: "DELETE",
    });
  },
};

export const productsApi = {
  async getAll(params: {
    skip?: number;
    limit?: number;
    search?: string;
    category_id?: string;
    is_subscription?: boolean;
    is_active?: boolean;
    inventory_status?: string;
  } = {}): Promise<ProductListResponse> {
    const query = new URLSearchParams();
    if (params.skip !== undefined) query.set("skip", String(params.skip));
    if (params.limit !== undefined) query.set("limit", String(params.limit));
    if (params.search) query.set("search", params.search);
    if (params.category_id) query.set("category_id", params.category_id);
    if (params.is_subscription !== undefined) query.set("is_subscription", String(params.is_subscription));
    if (params.is_active !== undefined) query.set("is_active", String(params.is_active));
    if (params.inventory_status) query.set("inventory_status", params.inventory_status);

    const qs = query.toString() ? `?${query.toString()}` : "";
    const res = await request<ApiResponse<ProductListResponse>>(`/products${qs}`);
    if (!res.data) throw new Error("Failed to load products list");
    return res.data;
  },

  async getDashboard(): Promise<ProductDashboardData> {
    const res = await request<ApiResponse<ProductDashboardData>>("/products/dashboard");
    if (!res.data) throw new Error("Failed to load product dashboard analytics");
    return res.data;
  },

  async getById(id: string): Promise<Product> {
    const res = await request<ApiResponse<Product>>(`/products/${id}`);
    if (!res.data) throw new Error("Failed to load product details");
    return res.data;
  },

  async create(data: ProductCreateInput): Promise<Product> {
    const res = await request<ApiResponse<Product>>("/products", {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to create product");
    return res.data;
  },

  async update(id: string, data: ProductUpdateInput): Promise<Product> {
    const res = await request<ApiResponse<Product>>(`/products/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to update product");
    return res.data;
  },

  async delete(id: string, soft: boolean = true): Promise<void> {
    await request<ApiResponse<any>>(`/products/${id}?soft=${soft}`, {
      method: "DELETE",
    });
  },

  // Phase 078: Product Variants API
  async getVariants(productId: string, includeInactive: boolean = false): Promise<ProductVariant[]> {
    const res = await request<ApiResponse<ProductVariant[]>>(
      `/products/${productId}/variants?include_inactive=${includeInactive}`
    );
    return res.data || [];
  },

  async createVariant(productId: string, data: ProductVariantCreateInput): Promise<ProductVariant> {
    const res = await request<ApiResponse<ProductVariant>>(`/products/${productId}/variants`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to create product variant");
    return res.data;
  },

  async updateVariant(variantId: string, data: ProductVariantUpdateInput): Promise<ProductVariant> {
    const res = await request<ApiResponse<ProductVariant>>(`/products/variants/${variantId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to update product variant");
    return res.data;
  },

  async deleteVariant(variantId: string, soft: boolean = true): Promise<void> {
    await request<ApiResponse<any>>(`/products/variants/${variantId}?soft=${soft}`, {
      method: "DELETE",
    });
  },
};

// Phase 077: Product Units API
export const productUnitsApi = {
  async getAll(includeInactive: boolean = false): Promise<ProductUnit[]> {
    const res = await request<ApiResponse<ProductUnit[]>>(
      `/product-units?include_inactive=${includeInactive}`
    );
    return res.data || [];
  },

  async getById(id: string): Promise<ProductUnit> {
    const res = await request<ApiResponse<ProductUnit>>(`/product-units/${id}`);
    if (!res.data) throw new Error("Failed to load product unit");
    return res.data;
  },

  async create(data: ProductUnitCreateInput): Promise<ProductUnit> {
    const res = await request<ApiResponse<ProductUnit>>("/product-units", {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to create product unit");
    return res.data;
  },

  async update(id: string, data: ProductUnitUpdateInput): Promise<ProductUnit> {
    const res = await request<ApiResponse<ProductUnit>>(`/product-units/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to update product unit");
    return res.data;
  },

  async delete(id: string, soft: boolean = true): Promise<void> {
    await request<ApiResponse<any>>(`/product-units/${id}?soft=${soft}`, {
      method: "DELETE",
    });
  },
};

// Phase 079: Product Attributes API
export const productAttributesApi = {
  async getAll(includeInactive: boolean = false): Promise<ProductAttribute[]> {
    const res = await request<ApiResponse<ProductAttribute[]>>(
      `/product-attributes?include_inactive=${includeInactive}`
    );
    return res.data || [];
  },

  async getById(id: string): Promise<ProductAttribute> {
    const res = await request<ApiResponse<ProductAttribute>>(`/product-attributes/${id}`);
    if (!res.data) throw new Error("Failed to load product attribute");
    return res.data;
  },

  async create(data: ProductAttributeCreateInput): Promise<ProductAttribute> {
    const res = await request<ApiResponse<ProductAttribute>>("/product-attributes", {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to create product attribute");
    return res.data;
  },

  async update(id: string, data: ProductAttributeUpdateInput): Promise<ProductAttribute> {
    const res = await request<ApiResponse<ProductAttribute>>(`/product-attributes/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to update product attribute");
    return res.data;
  },

  async delete(id: string): Promise<void> {
    await request<ApiResponse<any>>(`/product-attributes/${id}`, {
      method: "DELETE",
    });
  },

  async addValue(attributeId: string, data: ProductAttributeValueCreateInput): Promise<ProductAttributeValue> {
    const res = await request<ApiResponse<ProductAttributeValue>>(`/product-attributes/${attributeId}/values`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to add attribute value");
    return res.data;
  },

  async deleteValue(attributeId: string, valueId: string): Promise<void> {
    await request<ApiResponse<any>>(`/product-attributes/${attributeId}/values/${valueId}`, {
      method: "DELETE",
    });
  },
};

export const warehousesApi = {
  async getAll(params: {
    skip?: number;
    limit?: number;
    search?: string;
    is_active?: boolean;
  } = {}): Promise<WarehouseListResponse> {
    const query = new URLSearchParams();
    if (params.skip !== undefined) query.set("skip", String(params.skip));
    if (params.limit !== undefined) query.set("limit", String(params.limit));
    if (params.search) query.set("search", params.search);
    if (params.is_active !== undefined) query.set("is_active", String(params.is_active));

    const qs = query.toString() ? `?${query.toString()}` : "";
    const res = await request<ApiResponse<WarehouseListResponse>>(`/warehouses${qs}`);
    if (!res.data) throw new Error("Failed to load warehouses");
    return res.data;
  },

  async getById(id: string): Promise<Warehouse> {
    const res = await request<ApiResponse<Warehouse>>(`/warehouses/${id}`);
    if (!res.data) throw new Error("Failed to load warehouse details");
    return res.data;
  },

  async create(data: WarehouseCreateInput): Promise<Warehouse> {
    const res = await request<ApiResponse<Warehouse>>("/warehouses", {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to create warehouse");
    return res.data;
  },

  async update(id: string, data: WarehouseUpdateInput): Promise<Warehouse> {
    const res = await request<ApiResponse<Warehouse>>(`/warehouses/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to update warehouse");
    return res.data;
  },

  async delete(id: string): Promise<void> {
    await request<ApiResponse<any>>(`/warehouses/${id}`, {
      method: "DELETE",
    });
  },

  async getStock(warehouseId: string): Promise<WarehouseStockListResponse> {
    const res = await request<ApiResponse<WarehouseStockListResponse>>(`/warehouses/${warehouseId}/stock`);
    if (!res.data) throw new Error("Failed to load warehouse stock");
    return res.data;
  },

  async setStock(warehouseId: string, data: WarehouseStockCreateInput): Promise<WarehouseStock> {
    const res = await request<ApiResponse<WarehouseStock>>(`/warehouses/${warehouseId}/stock`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.data) throw new Error("Failed to configure stock");
    return res.data;
  },

  async updateStock(
    warehouseId: string,
    productId: string,
    data: WarehouseStockUpdateInput
  ): Promise<WarehouseStock> {
    const res = await request<ApiResponse<WarehouseStock>>(
      `/warehouses/${warehouseId}/stock/${productId}`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      }
    );
    if (!res.data) throw new Error("Failed to update stock quantity");
    return res.data;
  },

  async getAvailability(warehouseId: string, productId: string): Promise<StockAvailability> {
    const res = await request<ApiResponse<StockAvailability>>(
      `/warehouses/${warehouseId}/stock/${productId}/availability`
    );
    if (!res.data) throw new Error("Failed to check stock availability");
    return res.data;
  },

  async reserveStock(
    warehouseId: string,
    productId: string,
    data: StockReserveReleaseInput
  ): Promise<WarehouseStock> {
    const res = await request<ApiResponse<WarehouseStock>>(
      `/warehouses/${warehouseId}/stock/${productId}/reserve`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
    if (!res.data) throw new Error("Failed to reserve stock");
    return res.data;
  },

  async releaseStock(
    warehouseId: string,
    productId: string,
    data: StockReserveReleaseInput
  ): Promise<WarehouseStock> {
    const res = await request<ApiResponse<WarehouseStock>>(
      `/warehouses/${warehouseId}/stock/${productId}/release`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
    if (!res.data) throw new Error("Failed to release stock");
    return res.data;
  },

  async getATP(warehouseId: string, productId: string): Promise<ATPData> {
    const res = await request<ApiResponse<ATPData>>(
      `/warehouses/${warehouseId}/stock/${productId}/atp`
    );
    if (!res.data) throw new Error("Failed to calculate ATP");
    return res.data;
  },

  // Phase 092: Warehouse Selection API
  async selectWarehouse(productId: string, quantity: number): Promise<WarehouseSelectionResponse> {
    const res = await request<ApiResponse<WarehouseSelectionResponse>>(
      `/warehouses/selection/product/${productId}?quantity=${quantity}`
    );
    if (!res.data) throw new Error("Failed to evaluate warehouse selection");
    return res.data;
  },

  // Phase 093: Multi-Warehouse Stock Breakdown
  async getMultiWarehouseStock(productId: string): Promise<MultiWarehouseStockResponse> {
    const res = await request<ApiResponse<MultiWarehouseStockResponse>>(
      `/warehouses/multi-stock/product/${productId}`
    );
    if (!res.data) throw new Error("Failed to load multi-warehouse stock");
    return res.data;
  },

  // Phase 094: Fulfillment Allocation Simulation
  async calculateAllocation(productId: string, requestedQuantity: number): Promise<AllocationResponse> {
    const res = await request<ApiResponse<AllocationResponse>>(
      `/warehouses/allocation/product/${productId}`,
      {
        method: "POST",
        body: JSON.stringify({ requested_quantity: requestedQuantity }),
      }
    );
    if (!res.data) throw new Error("Failed to calculate fulfillment allocation");
    return res.data;
  },

  // Phase 095: Multi-Warehouse Stock Reservation & Release
  async reserveAllocation(productId: string, requestedQuantity: number): Promise<MultiWarehouseReservationResponse> {
    const res = await request<ApiResponse<MultiWarehouseReservationResponse>>(
      `/warehouses/reservation/product/${productId}`,
      {
        method: "POST",
        body: JSON.stringify({ requested_quantity: requestedQuantity }),
      }
    );
    if (!res.data) throw new Error("Failed to reserve stock across warehouses");
    return res.data;
  },

  async releaseAllocation(productId: string, releases: WarehouseReleaseItem[]): Promise<MultiWarehouseReleaseResponse> {
    const res = await request<ApiResponse<MultiWarehouseReleaseResponse>>(
      `/warehouses/release/product/${productId}`,
      {
        method: "POST",
        body: JSON.stringify({ releases }),
      }
    );
    if (!res.data) throw new Error("Failed to release warehouse reservations");
    return res.data;
  },
};

// ==============================================================================
// G20: Backorders API (Phase 096)
// ==============================================================================
export const backordersApi = {
  async listBackorders(params?: {
    product_id?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }): Promise<BackorderListResponse> {
    const query = new URLSearchParams();
    if (params?.product_id) query.append("product_id", params.product_id);
    if (params?.status) query.append("status", params.status);
    if (params?.skip !== undefined) query.append("skip", params.skip.toString());
    if (params?.limit !== undefined) query.append("limit", params.limit.toString());

    const queryString = query.toString() ? `?${query.toString()}` : "";
    return request<BackorderListResponse>(`/backorders${queryString}`);
  },

  async createBackorder(data: BackorderCreateInput): Promise<Backorder> {
    return request<Backorder>("/backorders", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getBackorder(id: string): Promise<Backorder> {
    return request<Backorder>(`/backorders/${id}`);
  },

  async cancelBackorder(id: string, notes?: string): Promise<Backorder> {
    return request<Backorder>(`/backorders/${id}/cancel`, {
      method: "POST",
      body: JSON.stringify({ notes }),
    });
  },
};

// ==============================================================================
// G20: Fulfillments API (Phases 097 & 098)
// ==============================================================================
export const fulfillmentsApi = {
  async listFulfillments(params?: {
    product_id?: string;
    status?: string;
    delivery_status?: string;
    skip?: number;
    limit?: number;
  }): Promise<FulfillmentListResponse> {
    const query = new URLSearchParams();
    if (params?.product_id) query.append("product_id", params.product_id);
    if (params?.status) query.append("status", params.status);
    if (params?.delivery_status) query.append("delivery_status", params.delivery_status);
    if (params?.skip !== undefined) query.append("skip", params.skip.toString());
    if (params?.limit !== undefined) query.append("limit", params.limit.toString());

    const queryString = query.toString() ? `?${query.toString()}` : "";
    return request<FulfillmentListResponse>(`/fulfillments${queryString}`);
  },

  async createFulfillment(data: FulfillmentCreateInput): Promise<Fulfillment> {
    return request<Fulfillment>("/fulfillments", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getFulfillment(id: string): Promise<Fulfillment> {
    return request<Fulfillment>(`/fulfillments/${id}`);
  },

  async updateDeliveryStatus(id: string, data: FulfillmentDeliveryStatusUpdateInput): Promise<Fulfillment> {
    return request<Fulfillment>(`/fulfillments/${id}/delivery-status`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },
};

// ==============================================================================
// G20: Inventory Operations & Dashboard API (Phases 099 & 100)
// ==============================================================================
export const inventoryApi = {
  async getDashboard(): Promise<InventoryDashboardResponse> {
    return request<InventoryDashboardResponse>("/inventory/dashboard");
  },

  async listAlerts(params?: {
    is_active?: boolean;
    severity?: string;
    alert_type?: string;
    skip?: number;
    limit?: number;
  }): Promise<InventoryAlertListResponse> {
    const query = new URLSearchParams();
    if (params?.is_active !== undefined) query.append("is_active", params.is_active.toString());
    if (params?.severity) query.append("severity", params.severity);
    if (params?.alert_type) query.append("alert_type", params.alert_type);
    if (params?.skip !== undefined) query.append("skip", params.skip.toString());
    if (params?.limit !== undefined) query.append("limit", params.limit.toString());

    const queryString = query.toString() ? `?${query.toString()}` : "";
    return request<InventoryAlertListResponse>(`/inventory/alerts${queryString}`);
  },

  async scanAlerts(threshold: number = 10): Promise<InventoryAlertScanResponse> {
    return request<InventoryAlertScanResponse>(`/inventory/alerts/scan?threshold=${threshold}`, {
      method: "POST",
    });
  },

  async resolveAlert(id: string, notes?: string): Promise<InventoryAlert> {
    return request<InventoryAlert>(`/inventory/alerts/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify({ notes }),
    });
  },
};

// ==============================================================================
// G21: Discount Governance Foundation API (Phases 101–105)
// ==============================================================================
export const discountGovernanceApi = {
  // Phase 101: Discount Configurations
  async listConfigurations(params?: { is_active?: boolean; skip?: number; limit?: number }): Promise<DiscountConfigurationListResponse> {
    const query = new URLSearchParams();
    if (params?.is_active !== undefined) query.append("is_active", params.is_active.toString());
    if (params?.skip !== undefined) query.append("skip", params.skip.toString());
    if (params?.limit !== undefined) query.append("limit", params.limit.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<DiscountConfigurationListResponse>(`/governance/discounts/configurations${qs}`);
  },

  async createConfiguration(input: DiscountConfigurationCreateInput): Promise<DiscountConfiguration> {
    return request<DiscountConfiguration>("/governance/discounts/configurations", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  async updateConfiguration(id: string, input: DiscountConfigurationUpdateInput): Promise<DiscountConfiguration> {
    return request<DiscountConfiguration>(`/governance/discounts/configurations/${id}`, {
      method: "PUT",
      body: JSON.stringify(input),
    });
  },

  async deleteConfiguration(id: string): Promise<void> {
    return request<void>(`/governance/discounts/configurations/${id}`, {
      method: "DELETE",
    });
  },

  // Phase 102: Customer Discount Ceilings
  async listCustomerCeilings(params?: { customer_id?: string; is_active?: boolean; skip?: number; limit?: number }): Promise<CustomerDiscountCeilingListResponse> {
    const query = new URLSearchParams();
    if (params?.customer_id) query.append("customer_id", params.customer_id);
    if (params?.is_active !== undefined) query.append("is_active", params.is_active.toString());
    if (params?.skip !== undefined) query.append("skip", params.skip.toString());
    if (params?.limit !== undefined) query.append("limit", params.limit.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<CustomerDiscountCeilingListResponse>(`/governance/discounts/customer-ceilings${qs}`);
  },

  async createCustomerCeiling(input: CustomerDiscountCeilingCreateInput): Promise<CustomerDiscountCeiling> {
    return request<CustomerDiscountCeiling>("/governance/discounts/customer-ceilings", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  async updateCustomerCeiling(id: string, input: CustomerDiscountCeilingUpdateInput): Promise<CustomerDiscountCeiling> {
    return request<CustomerDiscountCeiling>(`/governance/discounts/customer-ceilings/${id}`, {
      method: "PUT",
      body: JSON.stringify(input),
    });
  },

  async deleteCustomerCeiling(id: string): Promise<void> {
    return request<void>(`/governance/discounts/customer-ceilings/${id}`, {
      method: "DELETE",
    });
  },

  // Phase 103: Category Discount Ceilings
  async listCategoryCeilings(params?: { category_id?: string; is_active?: boolean; skip?: number; limit?: number }): Promise<CategoryDiscountCeilingListResponse> {
    const query = new URLSearchParams();
    if (params?.category_id) query.append("category_id", params.category_id);
    if (params?.is_active !== undefined) query.append("is_active", params.is_active.toString());
    if (params?.skip !== undefined) query.append("skip", params.skip.toString());
    if (params?.limit !== undefined) query.append("limit", params.limit.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<CategoryDiscountCeilingListResponse>(`/governance/discounts/category-ceilings${qs}`);
  },

  async createCategoryCeiling(input: CategoryDiscountCeilingCreateInput): Promise<CategoryDiscountCeiling> {
    return request<CategoryDiscountCeiling>("/governance/discounts/category-ceilings", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  async updateCategoryCeiling(id: string, input: CategoryDiscountCeilingUpdateInput): Promise<CategoryDiscountCeiling> {
    return request<CategoryDiscountCeiling>(`/governance/discounts/category-ceilings/${id}`, {
      method: "PUT",
      body: JSON.stringify(input),
    });
  },

  async deleteCategoryCeiling(id: string): Promise<void> {
    return request<void>(`/governance/discounts/category-ceilings/${id}`, {
      method: "DELETE",
    });
  },

  // Phase 104: Product Discount Ceilings
  async listProductCeilings(params?: { product_id?: string; is_active?: boolean; skip?: number; limit?: number }): Promise<ProductDiscountCeilingListResponse> {
    const query = new URLSearchParams();
    if (params?.product_id) query.append("product_id", params.product_id);
    if (params?.is_active !== undefined) query.append("is_active", params.is_active.toString());
    if (params?.skip !== undefined) query.append("skip", params.skip.toString());
    if (params?.limit !== undefined) query.append("limit", params.limit.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<ProductDiscountCeilingListResponse>(`/governance/discounts/product-ceilings${qs}`);
  },

  async createProductCeiling(input: ProductDiscountCeilingCreateInput): Promise<ProductDiscountCeiling> {
    return request<ProductDiscountCeiling>("/governance/discounts/product-ceilings", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  async updateProductCeiling(id: string, input: ProductDiscountCeilingUpdateInput): Promise<ProductDiscountCeiling> {
    return request<ProductDiscountCeiling>(`/governance/discounts/product-ceilings/${id}`, {
      method: "PUT",
      body: JSON.stringify(input),
    });
  },

  async deleteProductCeiling(id: string): Promise<void> {
    return request<void>(`/governance/discounts/product-ceilings/${id}`, {
      method: "DELETE",
    });
  },

  // Phase 105: Sales Rep Authority Limits
  async listSalesRepLimits(params?: { user_id?: string; is_active?: boolean; skip?: number; limit?: number }): Promise<SalesRepAuthorityLimitListResponse> {
    const query = new URLSearchParams();
    if (params?.user_id) query.append("user_id", params.user_id);
    if (params?.is_active !== undefined) query.append("is_active", params.is_active.toString());
    if (params?.skip !== undefined) query.append("skip", params.skip.toString());
    if (params?.limit !== undefined) query.append("limit", params.limit.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<SalesRepAuthorityLimitListResponse>(`/governance/discounts/sales-rep-limits${qs}`);
  },

  async createSalesRepLimit(input: SalesRepAuthorityLimitCreateInput): Promise<SalesRepAuthorityLimit> {
    return request<SalesRepAuthorityLimit>("/governance/discounts/sales-rep-limits", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  async updateSalesRepLimit(id: string, input: SalesRepAuthorityLimitUpdateInput): Promise<SalesRepAuthorityLimit> {
    return request<SalesRepAuthorityLimit>(`/governance/discounts/sales-rep-limits/${id}`, {
      method: "PUT",
      body: JSON.stringify(input),
    });
  },

  async deleteSalesRepLimit(id: string): Promise<void> {
    return request<void>(`/governance/discounts/sales-rep-limits/${id}`, {
      method: "DELETE",
    });
  },

  // Phase 106: Manager Authority Limits
  async listManagerLimits(params?: { user_id?: string; is_active?: boolean; skip?: number; limit?: number }): Promise<ManagerAuthorityLimitListResponse> {
    const query = new URLSearchParams();
    if (params?.user_id) query.append("user_id", params.user_id);
    if (params?.is_active !== undefined) query.append("is_active", params.is_active.toString());
    if (params?.skip !== undefined) query.append("skip", params.skip.toString());
    if (params?.limit !== undefined) query.append("limit", params.limit.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<ManagerAuthorityLimitListResponse>(`/governance/discounts/manager-limits${qs}`);
  },

  async createManagerLimit(input: ManagerAuthorityLimitCreateInput): Promise<ManagerAuthorityLimit> {
    return request<ManagerAuthorityLimit>("/governance/discounts/manager-limits", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  async updateManagerLimit(id: string, input: ManagerAuthorityLimitUpdateInput): Promise<ManagerAuthorityLimit> {
    return request<ManagerAuthorityLimit>(`/governance/discounts/manager-limits/${id}`, {
      method: "PUT",
      body: JSON.stringify(input),
    });
  },

  async deleteManagerLimit(id: string): Promise<void> {
    return request<void>(`/governance/discounts/manager-limits/${id}`, {
      method: "DELETE",
    });
  },

  // Phase 107: Finance Authority Limits
  async listFinanceLimits(params?: { user_id?: string; is_active?: boolean; skip?: number; limit?: number }): Promise<FinanceAuthorityLimitListResponse> {
    const query = new URLSearchParams();
    if (params?.user_id) query.append("user_id", params.user_id);
    if (params?.is_active !== undefined) query.append("is_active", params.is_active.toString());
    if (params?.skip !== undefined) query.append("skip", params.skip.toString());
    if (params?.limit !== undefined) query.append("limit", params.limit.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<FinanceAuthorityLimitListResponse>(`/governance/discounts/finance-limits${qs}`);
  },

  async createFinanceLimit(input: FinanceAuthorityLimitCreateInput): Promise<FinanceAuthorityLimit> {
    return request<FinanceAuthorityLimit>("/governance/discounts/finance-limits", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  async updateFinanceLimit(id: string, input: FinanceAuthorityLimitUpdateInput): Promise<FinanceAuthorityLimit> {
    return request<FinanceAuthorityLimit>(`/governance/discounts/finance-limits/${id}`, {
      method: "PUT",
      body: JSON.stringify(input),
    });
  },

  async deleteFinanceLimit(id: string): Promise<void> {
    return request<void>(`/governance/discounts/finance-limits/${id}`, {
      method: "DELETE",
    });
  },

  // Phases 108–110: Discount Policy Validation & Violation Detection
  async validateDiscount(input: DiscountValidationRequest): Promise<DiscountPolicyEvaluationResponse> {
    return request<DiscountPolicyEvaluationResponse>("/governance/discounts/validate", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  // ============================================================================
  // G23: Discount Intelligence Foundation (Phases 111–115)
  // ============================================================================

  // Phase 113: Margin Protection
  async calculateMarginProtection(input: import("@/types/discountGovernance").MarginProtectionRequest): Promise<import("@/types/discountGovernance").MarginProtectionResponse> {
    return request<import("@/types/discountGovernance").MarginProtectionResponse>("/governance/discounts/intelligence/margin-protection", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  // Phase 112: Maximum Safe Discount
  async calculateMaximumSafeDiscount(input: import("@/types/discountGovernance").MaximumSafeDiscountRequest): Promise<import("@/types/discountGovernance").MaximumSafeDiscountResponse> {
    return request<import("@/types/discountGovernance").MaximumSafeDiscountResponse>("/governance/discounts/intelligence/maximum-safe", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  // Phase 114: Historical Discount Analysis
  async getHistoricalDiscountAnalysis(params?: { customer_id?: string; product_id?: string }): Promise<import("@/types/discountGovernance").HistoricalDiscountAnalysisResponse> {
    const query = new URLSearchParams();
    if (params?.customer_id) query.append("customer_id", params.customer_id);
    if (params?.product_id) query.append("product_id", params.product_id);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return request<import("@/types/discountGovernance").HistoricalDiscountAnalysisResponse>(`/governance/discounts/intelligence/history${qs}`);
  },

  // Phase 115: Customer Discount Analysis
  async getCustomerDiscountAnalysis(customerId: string): Promise<import("@/types/discountGovernance").CustomerDiscountAnalysisResponse> {
    return request<import("@/types/discountGovernance").CustomerDiscountAnalysisResponse>(`/governance/discounts/intelligence/customer/${customerId}`);
  },

  // Phase 111: Recommended Discount Engine
  async getRecommendedDiscount(input: import("@/types/discountGovernance").DiscountRecommendationRequest): Promise<import("@/types/discountGovernance").DiscountRecommendationResponse> {
    return request<import("@/types/discountGovernance").DiscountRecommendationResponse>("/governance/discounts/intelligence/recommend", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },
};




