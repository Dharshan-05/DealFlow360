/**
 * Centralized API client for DealFlow360 frontend (Phase 040).
 * Handles authentication headers, token storage, and API response parsing.
 */
import { ApiResponse, ApiErrorResponse } from "@/types/api";
import { LoginRequest, RegisterRequest, TokenResponse, User } from "@/types/auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const ACCESS_TOKEN_KEY = "dealflow360_access_token";
const REFRESH_TOKEN_KEY = "dealflow360_refresh_token";

export function getStoredAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getStoredRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function storeTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearStoredTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const token = getStoredAccessToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const url = `${API_BASE_URL}${endpoint}`;
  let response = await fetch(url, {
    ...options,
    headers,
  });

  // Automatic token refresh on 401 Unauthorized
  if (response.status === 401 && endpoint !== "/auth/login" && endpoint !== "/auth/refresh") {
    const refreshToken = getStoredRefreshToken();
    if (refreshToken) {
      try {
        const refreshResponse = await fetch(`${API_BASE_URL}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (refreshResponse.ok) {
          const refreshData: ApiResponse<TokenResponse> = await refreshResponse.json();
          if (refreshData.data) {
            storeTokens(refreshData.data.access_token, refreshData.data.refresh_token);
            headers.set("Authorization", `Bearer ${refreshData.data.access_token}`);
            response = await fetch(url, {
              ...options,
              headers,
            });
          }
        } else {
          clearStoredTokens();
        }
      } catch {
        clearStoredTokens();
      }
    }
  }

  let body: any = null;
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    body = await response.json();
  } else {
    body = { message: await response.text() };
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
    storeTokens(res.data.access_token, res.data.refresh_token);
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
    const refreshToken = getStoredRefreshToken();
    try {
      if (refreshToken) {
        await request<ApiResponse<{ logged_out: boolean }>>("/auth/logout", {
          method: "POST",
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      }
    } finally {
      clearStoredTokens();
    }
  },
};
