import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const token = request.cookies.get("token")?.value;
  const { pathname, search } = request.nextUrl;

  // 1. API PROXY LOGIC (Cookie -> Bearer Header)
  // Intercept requests to /api/ and forward them to the backend with the Authorization header
  if (pathname.startsWith("/api/")) {
    const backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:8000";

    // Map /api -> /api/v1 for backend compatibility
    const targetPath = pathname.replace(/^\/api/, "/api/v1");
    const destination = new URL(`${targetPath}${search}`, backendUrl);

    // Log only in development
    if (process.env.NODE_ENV === "development") {
      console.log(`[Middleware Proxy] ${pathname} -> ${destination}`);
      if (token) {
        console.log(`[Middleware Proxy] Authorization header added`);
      } else {
        console.warn(`[Middleware Proxy] No token cookie found`);
      }
    }

    const requestHeaders = new Headers(request.headers);
    if (token) {
      requestHeaders.set("Authorization", `Bearer ${token}`);
    }

    return NextResponse.rewrite(destination, {
      request: {
        headers: requestHeaders,
      },
    });
  }

  // 2. ROUTE PROTECTION LOGIC
  const publicPaths = ["/login", "/register", "/"];
  const isPublicPath = publicPaths.some(
    (path) => pathname === path || pathname.startsWith("/_next"),
  );

  // Redirect to login if accessing protected route without token
  if (!token && !isPublicPath) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("from", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Redirect to dashboard if accessing auth pages while logged in
  if (token && (pathname === "/login" || pathname === "/register")) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public (public folder)
     */
    "/((?!_next/static|_next/image|favicon.ico|public).*)",
  ],
};
