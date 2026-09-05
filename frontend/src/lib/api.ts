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
