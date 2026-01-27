"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { User, LoginData, RegisterData } from "@/lib/types";
import { authApi } from "@/lib/api";
import { useRouter } from "next/navigation";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    async function loadUser() {
      const token = localStorage.getItem("token");
      if (token) {
        console.log("AuthProvider: Found token, fetching user...");
        try {
          const userData = await authApi.getMe();
          setUser(userData);
          localStorage.setItem("user", JSON.stringify(userData));
          console.log("AuthProvider: User loaded successfully.");
        } catch (error: any) {
          console.error(
            "AuthProvider: Failed to load user via getMe.",
            error.response?.status,
            error.message,
          );
          // If it's a 401, the interceptor will have already cleared the token,
          // but we logout here to ensure the state is clean.
          if (error.response?.status === 401) {
            console.warn("AuthProvider: 401 detected, resetting user state.");
            setUser(null);
          }
        }
      } else {
        console.log("AuthProvider: No token found.");
      }
      setLoading(false);
    }
    loadUser();
  }, []);

  const login = async (data: LoginData) => {
    const response = await authApi.login(data);
    localStorage.setItem("token", response.access_token);
    localStorage.setItem("user", JSON.stringify(response.user));
    setUser(response.user);
    router.push("/dashboard");
  };

  const register = async (data: RegisterData) => {
    await authApi.register(data);
    // After register, we could auto-login or redirect to login
    router.push("/login");
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
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
