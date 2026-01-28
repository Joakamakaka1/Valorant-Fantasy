"use client";

import React, { createContext, useContext, useState } from "react";
import { User, LoginData, RegisterData } from "@/lib/types";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import {
  loginAction,
  registerAction,
  logoutAction,
} from "@/lib/actions/auth-actions";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
  initialUser: User | null;
}

/**
 * AuthProvider manages authentication state.
 *
 * IMPORTANT: Receives initialUser from server-side session (app/layout.tsx).
 * This eliminates the need for an initial client-side fetch, improving performance
 * and avoiding waterfall requests.
 */
export function AuthProvider({ children, initialUser }: AuthProviderProps) {
  const queryClient = useQueryClient();
  const router = useRouter();

  // Initialize state with server-provided user
  const [user, setUser] = useState<User | null>(initialUser);
  const [isLoading, setIsLoading] = useState(false);

  // Login Handler - Sets cookie via Server Action
  const login = async (data: LoginData) => {
    setIsLoading(true);
    try {
      const result = await loginAction(data);

      if (result.success && result.user) {
        // Update client state immediately
        setUser(result.user);
        queryClient.setQueryData(["user"], result.user);
        router.push("/dashboard");
        router.refresh(); // Refresh server components
      } else {
        throw new Error(result.error || "Login failed");
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Register Handler
  const register = async (data: RegisterData) => {
    setIsLoading(true);
    try {
      const result = await registerAction(data);
      if (result.success) {
        router.push("/login");
      } else {
        throw new Error(result.error || "Registration failed");
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Logout Handler - Clears cookie via Server Action
  const logout = async () => {
    setIsLoading(true);
    try {
      await logoutAction();
      setUser(null);
      queryClient.setQueryData(["user"], null);
      queryClient.clear();
      router.push("/login");
      router.refresh(); // Refresh server components
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
