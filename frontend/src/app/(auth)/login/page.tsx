/*
 * Login page: supports two authentication modes:
 *   1. Email OTP (default) - sends a one-time code to the user's email
 *   2. Password-based login - traditional username/email/password form
 *
 * After successful login, redirects to a "redirect" query param (if present),
 * the admin dashboard (for admin users), or the home page.
 * Wrapped in Suspense because it reads searchParams via useSearchParams().
 */

"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Mail, User, Lock, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useAuthStore } from "@/store/auth";
import { emailOtpApi } from "@/lib/api";

// Union type for the two login modes
type LoginMode = "email-otp" | "password";

function LoginContent() {
  const searchParams = useSearchParams();
  // Optional redirect URL from the query string (e.g., after a protected route redirect)
  const redirectTo = searchParams.get("redirect");
  // Auth store provides login functions, loading state, and error handling
  const { login, loginWithEmailOTP, isLoading, error, clearError } = useAuthStore();

  // Determine where to redirect after login based on user role
  const getRedirectUrl = (role?: string) => {
    if (role === "admin") return "/admin";
    return redirectTo || "/";
  };

  // Track which login mode is active (email OTP vs password)
  const [loginMode, setLoginMode] = useState<LoginMode>("email-otp");

  // Password login state
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Email OTP state: tracks email, OTP code, sent status, loading, error, and resend cooldown
  const [emailForOtp, setEmailForOtp] = useState("");
  const [emailOtpCode, setEmailOtpCode] = useState("");
  const [emailOtpSent, setEmailOtpSent] = useState(false);
  const [emailOtpLoading, setEmailOtpLoading] = useState(false);
  const [emailOtpError, setEmailOtpError] = useState("");
  const [emailResendCountdown, setEmailResendCountdown] = useState(0);

  // Start a 30-second countdown timer before the user can resend the OTP
  const startResendCountdown = () => {
    setEmailResendCountdown(30);
    const interval = setInterval(() => {
      setEmailResendCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  // ==================== Email OTP handlers ====================

  // Validate email and send an OTP code to the user's email address
  const handleSendEmailOTP = async () => {
    if (!emailForOtp.trim()) {
      setEmailOtpError("Email is required");
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailForOtp)) {
      setEmailOtpError("Enter a valid email address");
      return;
    }

    setEmailOtpLoading(true);
    setEmailOtpError("");
    try {
      await emailOtpApi.sendOTP(emailForOtp);
      setEmailOtpSent(true);
      startResendCountdown();
    } catch (err: unknown) {
      setEmailOtpError(err instanceof Error ? err.message : "Failed to send verification code");
    } finally {
      setEmailOtpLoading(false);
    }
  };

  // Resend the OTP code to the same email address
  const handleResendEmailOTP = async () => {
    setEmailOtpLoading(true);
    setEmailOtpError("");
    try {
      await emailOtpApi.sendOTP(emailForOtp);
      startResendCountdown();
    } catch (err: unknown) {
      setEmailOtpError(err instanceof Error ? err.message : "Failed to resend verification code");
    } finally {
      setEmailOtpLoading(false);
    }
  };

  // Submit the OTP code for verification and log the user in
  const handleEmailOTPSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!emailOtpCode.trim() || emailOtpCode.length < 4) {
      setEmailOtpError("Enter a valid verification code");
      return;
    }

    try {
      await loginWithEmailOTP(emailForOtp, emailOtpCode);
      const user = useAuthStore.getState().user;
      window.location.href = getRedirectUrl(user?.role);
    } catch {
      // Error is handled by the store
    }
  };

  // ==================== Password login handlers ====================

  // Client-side validation for the password login form fields
  const validatePasswordForm = () => {
    const errors: Record<string, string> = {};
    if (!formData.username.trim()) errors.username = "Username is required";
    if (!formData.email.trim()) {
      errors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = "Invalid email address";
    }
    if (!formData.password) errors.password = "Password is required";
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Submit the password-based login form
  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    if (!validatePasswordForm()) return;

    try {
      await login(formData.username, formData.email, formData.password);
      const user = useAuthStore.getState().user;
      window.location.href = getRedirectUrl(user?.role);
    } catch {
      // Error is handled by the store
    }
  };

  // Generic input change handler that also clears per-field errors on edit
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (formErrors[name]) {
      setFormErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  // Switch between email-OTP and password login modes, clearing all errors
  const switchMode = (mode: LoginMode) => {
    clearError();
    setFormErrors({});
    setEmailOtpError("");
    setLoginMode(mode);
  };

  return (
    <Card className="border-border/50 shadow-card-hover">
      <CardHeader className="text-center pb-2">
        <CardTitle className="text-2xl tracking-tight">Welcome back</CardTitle>
        <CardDescription>Sign in to your ZONIQ account</CardDescription>
      </CardHeader>
      <CardContent>
        {/* Login mode tabs: toggle between Email OTP and Password authentication */}
        <div className="flex mb-6 p-1 bg-background-elevated rounded-xl">
          <button
            type="button"
            onClick={() => switchMode("email-otp")}
            className={`flex-1 py-2.5 text-sm font-semibold rounded-lg transition-all duration-200 ${
              loginMode === "email-otp"
                ? "bg-primary text-white shadow-glow-sm"
                : "text-foreground-muted hover:text-foreground"
            }`}
          >
            Email
          </button>
          <button
            type="button"
            onClick={() => switchMode("password")}
            className={`flex-1 py-2.5 text-sm font-semibold rounded-lg transition-all duration-200 ${
              loginMode === "password"
                ? "bg-primary text-white shadow-glow-sm"
                : "text-foreground-muted hover:text-foreground"
            }`}
          >
            Password
          </button>
        </div>

        {/* Global error banner from the auth store */}
        {error && (
          <div className="flex items-center gap-2.5 p-3.5 rounded-xl bg-error/5 border border-error/10 text-error text-sm mb-5">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Email OTP Login Form (Default) */}
        {loginMode === "email-otp" && (
          <form onSubmit={handleEmailOTPSubmit} className="space-y-4">
            {/* Email input with "Get Code" / "Change" button */}
            <div className="space-y-2">
              <div className="flex gap-2">
                <div className="flex-1">
                  <Input
                    label="Email Address"
                    name="emailOtp"
                    type="email"
                    placeholder="Enter your email"
                    value={emailForOtp}
                    onChange={(e) => {
                      setEmailForOtp(e.target.value);
                      setEmailOtpError("");
                      if (emailOtpSent) {
                        setEmailOtpSent(false);
                        setEmailOtpCode("");
                      }
                    }}
                    leftIcon={<Mail className="h-4 w-4" />}
                    autoComplete="email"
                    disabled={emailOtpSent}
                  />
                </div>
                <div className="flex items-end pb-1">
                  {!emailOtpSent ? (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={handleSendEmailOTP}
                      disabled={emailOtpLoading || !emailForOtp.trim()}
                      className="whitespace-nowrap h-11"
                    >
                      {emailOtpLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        "Get Code"
                      )}
                    </Button>
                  ) : (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setEmailOtpSent(false);
                        setEmailOtpCode("");
                        setEmailOtpError("");
                      }}
                      className="whitespace-nowrap h-11 text-foreground-muted"
                    >
                      Change
                    </Button>
                  )}
                </div>
              </div>
            </div>

            {/* OTP code entry: shown after OTP has been sent */}
            {emailOtpSent && (
              <div className="space-y-4 animate-fade-in">
                <Input
                  label="Verification Code"
                  name="emailOtpCode"
                  placeholder="Enter 6-digit code"
                  value={emailOtpCode}
                  onChange={(e) => {
                    setEmailOtpCode(e.target.value);
                    setEmailOtpError("");
                  }}
                  maxLength={6}
                  className="text-center tracking-[0.3em] text-lg font-mono"
                  autoFocus
                />

                {/* Inline OTP-specific error message */}
                {emailOtpError && (
                  <p className="text-xs text-error font-medium">{emailOtpError}</p>
                )}

                {/* Resend OTP link with countdown timer */}
                <div className="flex items-center justify-between">
                  <button
                    type="button"
                    onClick={handleResendEmailOTP}
                    disabled={emailOtpLoading || emailResendCountdown > 0}
                    className="text-sm text-primary hover:underline disabled:text-foreground-subtle disabled:no-underline transition-colors"
                  >
                    {emailResendCountdown > 0
                      ? `Resend code in ${emailResendCountdown}s`
                      : "Resend code"}
                  </button>
                </div>

                {/* Submit OTP to log in */}
                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  isLoading={isLoading}
                  disabled={emailOtpCode.length < 4}
                >
                  Continue
                </Button>
              </div>
            )}

            {/* Informational text shown before OTP is sent */}
            {!emailOtpSent && (
              <p className="text-xs text-foreground-subtle text-center leading-relaxed">
                We&apos;ll send a verification code to your email. No password needed — new users are automatically registered.
              </p>
            )}
          </form>
        )}

        {/* Password Login Form */}
        {loginMode === "password" && (
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <Input
              label="Username"
              name="username"
              placeholder="Enter your username"
              value={formData.username}
              onChange={handleChange}
              error={formErrors.username}
              leftIcon={<User className="h-4 w-4" />}
              autoComplete="username"
            />

            <Input
              label="Email"
              name="email"
              type="email"
              placeholder="Enter your email"
              value={formData.email}
              onChange={handleChange}
              error={formErrors.email}
              leftIcon={<Mail className="h-4 w-4" />}
              autoComplete="email"
            />

            <Input
              label="Password"
              name="password"
              type="password"
              placeholder="Enter your password"
              value={formData.password}
              onChange={handleChange}
              error={formErrors.password}
              leftIcon={<Lock className="h-4 w-4" />}
              autoComplete="current-password"
            />

            <div className="flex items-center justify-end">
              <Link
                href="/forgot-password"
                className="text-sm text-primary hover:underline"
              >
                Forgot password?
              </Link>
            </div>

            <Button type="submit" className="w-full" size="lg" isLoading={isLoading}>
              Sign In
            </Button>
          </form>
        )}

        {/* Link to the signup page for users who want password-based accounts */}
        <div className="text-center text-sm text-foreground-muted mt-6 pt-6 border-t border-border/50">
          Want to create an account with a password?{" "}
          <Link href="/signup" className="text-primary hover:underline font-semibold">
            Sign up
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}

// Wrap LoginContent in Suspense because useSearchParams() requires it in Next.js App Router
export default function LoginPage() {
  return (
    <Suspense>
      <LoginContent />
    </Suspense>
  );
}
