"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SessionProvider } from "next-auth/react";
import { useEffect, useState, type ReactNode } from "react";
import { AuthProvider, useAuth } from "@/lib/auth-context";
import { setTokenGetter, setTokenRefresher } from "@/lib/api-client";

/** Bridges auth context → api-client so all API calls use the in-memory token. */
function ApiClientBridge() {
  const { accessToken, refreshAccessToken } = useAuth();

  useEffect(() => {
    setTokenGetter(() => accessToken);
    setTokenRefresher(refreshAccessToken);
  }, [accessToken, refreshAccessToken]);

  return null;
}

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 1,
          },
        },
      }),
  );

  return (
    <SessionProvider>
      <AuthProvider>
        <ApiClientBridge />
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      </AuthProvider>
    </SessionProvider>
  );
}
