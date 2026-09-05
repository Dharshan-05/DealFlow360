"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { AuthContextType, LoginRequest, RegisterRequest, User } from "@/types/auth";
import { authApi, getAccessToken, setAccessToken } from "@/lib/api";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessTokenState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Bootstrap session restoration via HttpOnly refresh cookie on application startup
  const refreshSession = useCallback(async () => {
    try {
      const tokenData = await authApi.refresh();
      if (tokenData?.access_token) {
        setAccessTokenState(tokenData.access_token);
        const userData = await authApi.getMe();
        setUser(userData);
      } else {
        setUser(null);
        setAccessToken(null);
        setAccessTokenState(null);
      }
    } catch {
      // No active refresh session or cookie expired
      setUser(null);
      setAccessToken(null);
      setAccessTokenState(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshSession();
  }, [refreshSession]);

  const login = async (credentials: LoginRequest): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      const tokenData = await authApi.login(credentials);
      setAccessTokenState(tokenData.access_token);
      const userData = await authApi.getMe();
      setUser(userData);
    } catch (err: any) {
      const message = err?.message || "Failed to log in. Please verify your credentials.";
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterRequest): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      await authApi.register(data);
      // Automatically log in to establish the HttpOnly cookie session
      const tokenData = await authApi.login({
        email: data.email,
        password: data.password,
      });
      setAccessTokenState(tokenData.access_token);
      const userData = await authApi.getMe();
      setUser(userData);
    } catch (err: any) {
      const message = err?.message || "Registration failed. Please check your details.";
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    setIsLoading(true);
    try {
      await authApi.logout();
    } catch {
      // Ignore network errors on logout, tokens are cleared
    } finally {
      setAccessToken(null);
      setAccessTokenState(null);
      setUser(null);
      setError(null);
      setIsLoading(false);
    }
  };

  const value: AuthContextType = {
    user,
    accessToken,
    isAuthenticated: !!user,
    isLoading,
    error,
    login,
    register,
    logout,
    clearError,
    refreshSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
