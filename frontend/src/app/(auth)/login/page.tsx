"use client";

import { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Mail, User, Lock, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useAuthStore } from "@/store/auth";
import { emailOtpApi } from "@/lib/api";

type LoginMode = "email-otp" | "password";

export default function LoginPage() {
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect");
  const { login, loginWithEmailOTP, isLoading, error, clearError } = useAuthStore();

  const getRedirectUrl = (role?: string) => {
    if (role === "admin") return "/admin";
    return redirectTo || "/";
  };

  const [loginMode, setLoginMode] = useState<LoginMode>("email-otp");

  // Password login state
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Email OTP state
  const [emailForOtp, setEmailForOtp] = useState("");
  const [emailOtpCode, setEmailOtpCode] = useState("");
  const [emailOtpSent, setEmailOtpSent] = useState(false);
  const [emailOtpLoading, setEmailOtpLoading] = useState(false);
  const [emailOtpError, setEmailOtpError] = useState("");
  const [emailResendCountdown, setEmailResendCountdown] = useState(0);

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

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (formErrors[name]) {
      setFormErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  const switchMode = (mode: LoginMode) => {
    clearError();
    setFormErrors({});
    setEmailOtpError("");
    setLoginMode(mode);
  };

  return (
    <Card className="border-border">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Welcome to ZONIQ</CardTitle>
        <CardDescription>Sign in or create your account instantly</CardDescription>
      </CardHeader>
      <CardContent>
        {/* Login mode tabs */}
        <div className="flex mb-6 border border-border rounded-lg overflow-hidden">
          <button
            type="button"
            onClick={() => switchMode("email-otp")}
            className={`flex-1 py-2.5 text-sm font-medium transition-colors ${
              loginMode === "email-otp"
                ? "bg-primary text-primary-foreground"
                : "bg-background text-foreground-muted hover:text-foreground"
            }`}
          >
            Email
          </button>
          <button
            type="button"
            onClick={() => switchMode("password")}
            className={`flex-1 py-2.5 text-sm font-medium transition-colors ${
              loginMode === "password"
                ? "bg-primary text-primary-foreground"
                : "bg-background text-foreground-muted hover:text-foreground"
            }`}
          >
            Password
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 text-error text-sm mb-4">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Email OTP Login Form (Default) */}
        {loginMode === "email-otp" && (
          <form onSubmit={handleEmailOTPSubmit} className="space-y-4">
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
                      className="whitespace-nowrap h-10"
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
                      className="whitespace-nowrap h-10 text-foreground-muted"
                    >
                      Change
                    </Button>
                  )}
                </div>
              </div>
            </div>

            {emailOtpSent && (
              <div className="space-y-3">
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
                  className="text-center tracking-widest text-lg"
                  autoFocus
                />

                {emailOtpError && (
                  <p className="text-xs text-error">{emailOtpError}</p>
                )}

                <div className="flex items-center justify-between">
                  <button
                    type="button"
                    onClick={handleResendEmailOTP}
                    disabled={emailOtpLoading || emailResendCountdown > 0}
                    className="text-sm text-primary hover:underline disabled:text-foreground-muted disabled:no-underline"
                  >
                    {emailResendCountdown > 0
                      ? `Resend code in ${emailResendCountdown}s`
                      : "Resend code"}
                  </button>
                </div>

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

            {!emailOtpSent && (
              <p className="text-xs text-foreground-muted text-center">
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

        <div className="text-center text-sm text-foreground-muted mt-4">
          Want to create an account with a password?{" "}
          <Link href="/signup" className="text-primary hover:underline font-medium">
            Sign up
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
