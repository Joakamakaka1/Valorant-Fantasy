"use client";

import React, { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/lib/context/auth-context";
import { User } from "@/lib/types";

interface ProvidersProps {
  children: React.ReactNode;
  initialUser: User | null;
}

/**
 * Providers wrapper for client-side context providers.
 *
 * Receives initialUser from server-side session via app/layout.tsx
 * and passes it down to AuthProvider, eliminating the need for
 * an initial client-side fetch.
 */
export default function Providers({ children, initialUser }: ProvidersProps) {
  // Use useState to ensure QueryClient is stable across re-renders
  // but unique per request on the client to avoid hydration issues
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // With SSR, we usually want to set some default staleTime
            // above 0 to avoid refetching immediately on the client
            staleTime: 60 * 1000,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider initialUser={initialUser}>{children}</AuthProvider>
    </QueryClientProvider>
  );
}
