import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PROTECTED_PATHS = ["/dashboard", "/submit", "/suggest", "/admin", "/profile"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if path is protected
  const isProtected = PROTECTED_PATHS.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );

  if (!isProtected) return NextResponse.next();

  // Check for refresh_token cookie (presence indicates a session exists)
  const refreshToken = request.cookies.get("refresh_token");

  if (!refreshToken) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("callbackUrl", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/submit/:path*",
    "/suggest/:path*",
    "/admin/:path*",
    "/profile/:path*",
  ],
};
