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
  ProductListResponse,
  ProductUnit,
  ProductUnitCreateInput,
  ProductUnitUpdateInput,
  ProductUpdateInput,
  ProductVariant,
  ProductVariantCreateInput,
  ProductVariantUpdateInput,
} from "@/types/product";

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
    category_id?: string;
    is_active?: boolean;
  } = {}): Promise<ProductListResponse> {
    const query = new URLSearchParams();
    if (params.skip !== undefined) query.set("skip", String(params.skip));
    if (params.limit !== undefined) query.set("limit", String(params.limit));
    if (params.category_id) query.set("category_id", params.category_id);
    if (params.is_active !== undefined) query.set("is_active", String(params.is_active));

    const qs = query.toString() ? `?${query.toString()}` : "";
    const res = await request<ApiResponse<ProductListResponse>>(`/products${qs}`);
    if (!res.data) throw new Error("Failed to load products list");
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

