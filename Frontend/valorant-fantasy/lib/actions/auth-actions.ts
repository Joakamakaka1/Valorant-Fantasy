"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { LoginData, RegisterData, TokenResponse, User } from "@/lib/types";

// We'll use the backend URL directly since we are on the server
// Prefer BACKEND_URL for docker/production compatibility, fallback to localhost
const API_BASE_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000/api/v1";

export async function loginAction(data: LoginData) {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || "Error al iniciar sesión");
    }

    const rawData = await res.json();

    // Handle Backend Wrapper { success: true, data: ... }
    let tokenData = rawData;
    if (rawData && typeof rawData === "object" && "data" in rawData) {
      tokenData = rawData.data;
    }

    if (!tokenData.access_token) {
      throw new Error("Respuesta inválida del servidor (Falta access_token)");
    }

    // Set HttpOnly Cookie
    const cookieStore = await cookies();
    cookieStore.set("token", tokenData.access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24 * 7, // 1 week
      path: "/",
    });

    // Return the user data so the client can update its state immediately
    return { success: true, user: tokenData.user };
  } catch (error: any) {
    return { success: false, error: error.message };
  }
}

export async function logoutAction() {
  const cookieStore = await cookies();
  cookieStore.delete("token");
  redirect("/login");
}

export async function registerAction(data: RegisterData) {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || "Error al registrarse");
    }

    return { success: true };
  } catch (error: any) {
    return { success: false, error: error.message };
  }
}

/**
 * Get the current user session from the server.
 *
 * This function reads the token from cookies and validates it with the backend.
 * Returns null if no token exists or if validation fails.
 *
 * @returns User object or null
 */
export async function getSession(): Promise<User | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;

  if (!token) return null;

  try {
    // Verify token with backend /me endpoint
    const res = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store", // Don't cache session checks
    });

    if (!res.ok) return null;

    const data = await res.json();

    // Handle wrapped response { success: true, data: {...} }
    if (data && typeof data === "object" && "data" in data) {
      return data.data as User;
    }

    return data as User;
  } catch (error) {
    // Silent fail - just return null if session check fails
    return null;
  }
}
