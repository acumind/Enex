/** Typed fetch wrapper with in-memory JWT injection, refresh-on-401, and error handling. */

import type { ApiError } from "./types";

const API_BASE =
  typeof window !== "undefined"
    ? "/api/v1"
    : process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

type TokenGetter = () => string | null;
type TokenRefresher = () => Promise<string | null>;

let _getAccessToken: TokenGetter = () => null;
let _refreshToken: TokenRefresher = async () => null;

/** Called by the AuthProvider bridge to wire up token access. */
export function setTokenGetter(getter: TokenGetter) {
  _getAccessToken = getter;
}

/** Called by the AuthProvider bridge to wire up token refresh. */
export function setTokenRefresher(refresher: TokenRefresher) {
  _refreshToken = refresher;
}

class ApiClient {
  private async request<T>(
    path: string,
    options: RequestInit = {},
    _isRetry = false,
  ): Promise<T> {
    const token = _getAccessToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      credentials: "include",
    });

    // Auto-refresh on 401 (once)
    if (response.status === 401 && !_isRetry) {
      const newToken = await _refreshToken();
      if (newToken) {
        return this.request<T>(path, options, true);
      }
    }

    if (!response.ok) {
      const error: ApiError = await response
        .json()
        .catch(() => ({ detail: `Request failed with status ${response.status}` }));
      throw new ApiClientError(error.detail, response.status);
    }

    return response.json();
  }

  async get<T>(path: string, params?: Record<string, string>): Promise<T> {
    const searchParams = params ? `?${new URLSearchParams(params)}` : "";
    return this.request<T>(`${path}${searchParams}`);
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async put<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async patch<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async delete<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: "DELETE" });
  }

  async download(path: string, filename: string): Promise<void> {
    const token = _getAccessToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const response = await fetch(`${API_BASE}${path}`, {
      headers,
      credentials: "include",
    });
    if (!response.ok) {
      throw new ApiClientError(
        `Download failed with status ${response.status}`,
        response.status,
      );
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
}

export class ApiClientError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

export const api = new ApiClient();
