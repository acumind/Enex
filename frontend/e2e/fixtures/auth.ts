import type { BrowserContext } from "@playwright/test";

/** Add a refresh_token cookie so Next.js middleware considers the user authenticated. */
export async function setAuthCookie(context: BrowserContext) {
  await context.addCookies([
    {
      name: "refresh_token",
      value: "mock-refresh-token",
      domain: "localhost",
      path: "/",
      httpOnly: true,
      secure: false,
      sameSite: "Lax",
    },
  ]);
}

/** Clear auth-related cookies. */
export async function clearAuthCookies(context: BrowserContext) {
  await context.clearCookies({ name: "refresh_token" });
}
