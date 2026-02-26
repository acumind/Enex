"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { signIn as nextAuthSignIn, useSession } from "next-auth/react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useAuth } from "@/lib/auth-context";
import type { OTPVerifyResponse, GoogleAuthResponse } from "@/lib/types";

// "use client" page — always runs in browser, use proxy path
const API_BASE = "/api/v1";

type OTPStep = "input" | "verify";

export default function LoginPage() {
  return (
    <Suspense>
      <LoginPageInner />
    </Suspense>
  );
}

function LoginPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") || "/dashboard";
  const { login, isAuthenticated } = useAuth();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) router.replace(callbackUrl);
  }, [isAuthenticated, callbackUrl, router]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Welcome to Enex</CardTitle>
          <CardDescription>Sign in to track analyst predictions</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="phone">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="phone">Phone</TabsTrigger>
              <TabsTrigger value="email">Email</TabsTrigger>
              <TabsTrigger value="google">Google</TabsTrigger>
            </TabsList>

            <TabsContent value="phone">
              <OTPForm
                type="phone"
                label="Phone Number"
                placeholder="+91XXXXXXXXXX"
                onSuccess={(token, user) => {
                  login(token, user);
                  router.replace(callbackUrl);
                }}
              />
            </TabsContent>

            <TabsContent value="email">
              <OTPForm
                type="email"
                label="Email Address"
                placeholder="you@example.com"
                onSuccess={(token, user) => {
                  login(token, user);
                  router.replace(callbackUrl);
                }}
              />
            </TabsContent>

            <TabsContent value="google">
              <GoogleLoginForm
                onSuccess={(token, user) => {
                  login(token, user);
                  router.replace(callbackUrl);
                }}
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </main>
  );
}

// ---------------------------------------------------------------------------
// OTP Form
// ---------------------------------------------------------------------------

function OTPForm({
  type,
  label,
  placeholder,
  onSuccess,
}: {
  type: "email" | "phone";
  label: string;
  placeholder: string;
  onSuccess: (token: string, user: OTPVerifyResponse["user"]) => void;
}) {
  const [step, setStep] = useState<OTPStep>("input");
  const [identifier, setIdentifier] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Countdown timer
  useEffect(() => {
    if (countdown <= 0) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }
    timerRef.current = setInterval(() => {
      setCountdown((c) => c - 1);
    }, 1000);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [countdown]);

  const handleSendOTP = useCallback(async () => {
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/otp/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier: identifier.trim(), purpose: "login" }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: "Failed to send code" }));
        setError(data.detail);
        return;
      }
      await res.json();
      setCountdown(60);
      setStep("verify");
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [identifier]);

  const handleVerifyOTP = useCallback(async () => {
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/otp/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          identifier: identifier.trim(),
          code: code.trim(),
          purpose: "login",
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: "Verification failed" }));
        setError(data.detail);
        return;
      }
      const data: OTPVerifyResponse = await res.json();
      onSuccess(data.access_token, data.user);
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [identifier, code, onSuccess]);

  if (step === "input") {
    return (
      <div className="space-y-4 pt-4">
        <div className="space-y-2">
          <Label htmlFor={`${type}-input`}>{label}</Label>
          <Input
            id={`${type}-input`}
            type={type === "email" ? "email" : "tel"}
            placeholder={placeholder}
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSendOTP()}
          />
        </div>
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        <Button className="w-full" onClick={handleSendOTP} disabled={loading || !identifier.trim()}>
          {loading ? "Sending..." : "Send Verification Code"}
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4 pt-4">
      <p className="text-sm text-muted-foreground">
        Code sent to <span className="font-medium">{identifier}</span>
      </p>
      <div className="space-y-2">
        <Label htmlFor={`${type}-code`}>Verification Code</Label>
        <Input
          id={`${type}-code`}
          type="text"
          inputMode="numeric"
          maxLength={6}
          placeholder="000000"
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
          onKeyDown={(e) => e.key === "Enter" && code.length === 6 && handleVerifyOTP()}
          autoFocus
        />
      </div>
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <Button className="w-full" onClick={handleVerifyOTP} disabled={loading || code.length !== 6}>
        {loading ? "Verifying..." : "Verify & Sign In"}
      </Button>
      <div className="flex items-center justify-between text-sm">
        <button
          type="button"
          className="text-muted-foreground hover:underline"
          onClick={() => {
            setStep("input");
            setCode("");
            setError("");
          }}
        >
          Change {type === "email" ? "email" : "number"}
        </button>
        {countdown > 0 ? (
          <span className="text-muted-foreground">Resend in {countdown}s</span>
        ) : (
          <button
            type="button"
            className="text-primary hover:underline"
            onClick={handleSendOTP}
            disabled={loading}
          >
            Resend code
          </button>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Google Login Form
// ---------------------------------------------------------------------------

function GoogleLoginForm({
  onSuccess,
}: {
  onSuccess: (token: string, user: GoogleAuthResponse["user"]) => void;
}) {
  const { data: session } = useSession();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const exchangedRef = useRef(false);

  // When NextAuth session appears with Google tokens, exchange for backend tokens
  useEffect(() => {
    if (exchangedRef.current) return;
    const sess = session as Record<string, unknown> | null;
    const idToken = sess?.id_token as string | undefined;
    const accessToken = sess?.access_token as string | undefined;

    if (!idToken && !accessToken) return;
    exchangedRef.current = true;

    async function exchange() {
      setLoading(true);
      setError("");
      try {
        const res = await fetch(`${API_BASE}/auth/google`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            id_token: idToken || null,
            access_token: accessToken || null,
          }),
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({ detail: "Google login failed" }));
          setError(data.detail);
          return;
        }
        const data: GoogleAuthResponse = await res.json();
        onSuccess(data.access_token, data.user);
      } catch {
        setError("Network error. Please try again.");
      } finally {
        setLoading(false);
      }
    }

    exchange();
  }, [session, onSuccess]);

  return (
    <div className="space-y-4 pt-4">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <Button
        variant="outline"
        className="w-full"
        onClick={() => nextAuthSignIn("google")}
        disabled={loading}
      >
        <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
          <path
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
            fill="#4285F4"
          />
          <path
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            fill="#34A853"
          />
          <path
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            fill="#FBBC05"
          />
          <path
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            fill="#EA4335"
          />
        </svg>
        {loading ? "Signing in..." : "Continue with Google"}
      </Button>
    </div>
  );
}
