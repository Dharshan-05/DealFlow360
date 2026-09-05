"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { AuthContextType, LoginRequest, RegisterRequest, User } from "@/types/auth";
import { authApi, getStoredAccessToken, clearStoredTokens } from "@/lib/api";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const loadCurrentUser = useCallback(async () => {
    const token = getStoredAccessToken();
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const userData = await authApi.getMe();
      setUser(userData);
    } catch {
      clearStoredTokens();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCurrentUser();
  }, [loadCurrentUser]);

  const login = async (credentials: LoginRequest): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      await authApi.login(credentials);
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
      // Automatically log in after registration
      await authApi.login({
        email: data.email,
        password: data.password,
      });
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
      // Ignore network errors on logout, tokens are cleared locally
    } finally {
      setUser(null);
      setError(null);
      setIsLoading(false);
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    login,
    register,
    logout,
    clearError,
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
