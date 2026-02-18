"use client";

import { useState } from "react";
import Link from "next/link";
import { Mail, User, Lock, Phone, AlertCircle, Check, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useAuthStore } from "@/store/auth";
import { emailOtpApi } from "@/lib/api";

const passwordRequirements = [
  { regex: /.{8,}/, label: "At least 8 characters" },
  { regex: /[A-Z]/, label: "One uppercase letter" },
  { regex: /[a-z]/, label: "One lowercase letter" },
  { regex: /[0-9]/, label: "One number" },
  { regex: /[!@#$%^&*]/, label: "One special character (!@#$%^&*)" },
];

export default function SignupPage() {
  const { register, isLoading, error, clearError } = useAuthStore();

  const [formData, setFormData] = useState({
    username: "",
    email: "",
    phone: "",
    password: "",
    confirmPassword: "",
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [showPasswordHints, setShowPasswordHints] = useState(false);

  // Email OTP state
  const [emailOtpSent, setEmailOtpSent] = useState(false);
  const [emailOtpCode, setEmailOtpCode] = useState("");
  const [emailVerified, setEmailVerified] = useState(false);
  const [otpLoading, setOtpLoading] = useState(false);
  const [otpError, setOtpError] = useState("");
  const [resendCountdown, setResendCountdown] = useState(0);

  const startResendCountdown = () => {
    setResendCountdown(30);
    const interval = setInterval(() => {
      setResendCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const handleSendOTP = async () => {
    if (!formData.email.trim()) {
      setFormErrors((prev) => ({ ...prev, email: "Email is required" }));
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      setFormErrors((prev) => ({ ...prev, email: "Enter a valid email address" }));
      return;
    }

    setOtpLoading(true);
    setOtpError("");
    try {
      await emailOtpApi.sendOTP(formData.email);
      setEmailOtpSent(true);
      startResendCountdown();
    } catch (err: unknown) {
      setOtpError(err instanceof Error ? err.message : "Failed to send verification code");
    } finally {
      setOtpLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setOtpLoading(true);
    setOtpError("");
    try {
      await emailOtpApi.sendOTP(formData.email);
      startResendCountdown();
    } catch (err: unknown) {
      setOtpError(err instanceof Error ? err.message : "Failed to resend verification code");
    } finally {
      setOtpLoading(false);
    }
  };

  const validateForm = () => {
    const errors: Record<string, string> = {};

    if (!formData.username.trim()) {
      errors.username = "Username is required";
    } else if (formData.username.length < 3) {
      errors.username = "Username must be at least 3 characters";
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      errors.username = "Username can only contain letters, numbers, and underscores";
    }

    if (!formData.email.trim()) {
      errors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = "Invalid email address";
    }

    if (!emailOtpCode.trim() || emailOtpCode.length < 4) {
      errors.otp = "Please enter the verification code sent to your email";
    }

    if (!formData.password) {
      errors.password = "Password is required";
    } else {
      const failedRequirements = passwordRequirements.filter(
        (req) => !req.regex.test(formData.password)
      );
      if (failedRequirements.length > 0) {
        errors.password = "Password does not meet requirements";
      }
    }

    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = "Passwords do not match";
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!validateForm()) return;

    try {
      await register(
        formData.username,
        formData.email,
        formData.password,
        emailOtpCode,
        formData.phone.trim() || undefined
      );
      const user = useAuthStore.getState().user;
      window.location.href = user?.role === "admin" ? "/admin" : "/";
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
    // Reset OTP state if email changes
    if (name === "email" && emailOtpSent) {
      setEmailOtpSent(false);
      setEmailOtpCode("");
      setEmailVerified(false);
    }
  };

  const getPasswordStrength = () => {
    const passed = passwordRequirements.filter((req) =>
      req.regex.test(formData.password)
    ).length;
    if (passed === 0) return { label: "", color: "" };
    if (passed <= 2) return { label: "Weak", color: "bg-red-500" };
    if (passed <= 4) return { label: "Medium", color: "bg-yellow-500" };
    return { label: "Strong", color: "bg-green-500" };
  };

  const passwordStrength = getPasswordStrength();

  return (
    <Card className="border-border/50 shadow-card-hover">
      <CardHeader className="text-center pb-2">
        <CardTitle className="text-2xl tracking-tight">Create an account</CardTitle>
        <CardDescription>Join ZONIQ to book tickets for amazing events</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="flex items-center gap-2.5 p-3.5 rounded-xl bg-error/5 border border-error/10 text-error text-sm">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <Input
            label="Username"
            name="username"
            placeholder="Choose a username"
            value={formData.username}
            onChange={handleChange}
            error={formErrors.username}
            leftIcon={<User className="h-4 w-4" />}
            autoComplete="username"
          />

          {/* Email with OTP Verification */}
          <div className="space-y-2">
            <div className="flex gap-2">
              <div className="flex-1">
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
                  disabled={emailOtpSent}
                />
              </div>
              <div className="flex items-end pb-1">
                {!emailOtpSent ? (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleSendOTP}
                    disabled={otpLoading || !formData.email.trim()}
                    className="whitespace-nowrap h-10"
                  >
                    {otpLoading ? (
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
                      setEmailVerified(false);
                      setOtpError("");
                    }}
                    className="whitespace-nowrap h-10 text-foreground-muted"
                  >
                    Change
                  </Button>
                )}
              </div>
            </div>

            {emailOtpSent && (
              <div className="space-y-2">
                <Input
                  label="Verification Code"
                  name="otp"
                  placeholder="Enter 6-digit code"
                  value={emailOtpCode}
                  onChange={(e) => {
                    setEmailOtpCode(e.target.value);
                    setOtpError("");
                    if (formErrors.otp) {
                      setFormErrors((prev) => ({ ...prev, otp: "" }));
                    }
                  }}
                  error={formErrors.otp}
                  maxLength={6}
                  className="text-center tracking-widest text-lg"
                  autoFocus
                />

                {otpError && (
                  <p className="text-xs text-error">{otpError}</p>
                )}

                <div className="flex items-center justify-between">
                  <button
                    type="button"
                    onClick={handleResendOTP}
                    disabled={otpLoading || resendCountdown > 0}
                    className="text-sm text-primary hover:underline disabled:text-foreground-muted disabled:no-underline"
                  >
                    {resendCountdown > 0
                      ? `Resend code in ${resendCountdown}s`
                      : "Resend code"}
                  </button>
                </div>
              </div>
            )}
          </div>

          <Input
            label="Phone (optional)"
            name="phone"
            type="tel"
            placeholder="10-digit mobile number"
            value={formData.phone}
            onChange={handleChange}
            error={formErrors.phone}
            leftIcon={<Phone className="h-4 w-4" />}
            autoComplete="tel"
          />

          <div className="space-y-2">
            <Input
              label="Password"
              name="password"
              type="password"
              placeholder="Create a password"
              value={formData.password}
              onChange={handleChange}
              onFocus={() => setShowPasswordHints(true)}
              error={formErrors.password}
              leftIcon={<Lock className="h-4 w-4" />}
              autoComplete="new-password"
            />

            {/* Password Strength Indicator */}
            {formData.password && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1 bg-background-elevated rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${passwordStrength.color}`}
                      style={{
                        width: `${(passwordRequirements.filter((req) =>
                          req.regex.test(formData.password)
                        ).length /
                            passwordRequirements.length) *
                          100
                          }%`,
                      }}
                    />
                  </div>
                  {passwordStrength.label && (
                    <span className="text-xs text-foreground-muted">
                      {passwordStrength.label}
                    </span>
                  )}
                </div>

                {showPasswordHints && (
                  <ul className="space-y-1 text-xs">
                    {passwordRequirements.map((req, index) => {
                      const passed = req.regex.test(formData.password);
                      return (
                        <li
                          key={index}
                          className={`flex items-center gap-2 ${passed
                              ? "text-success"
                              : "text-foreground-muted"
                            }`}
                        >
                          <Check
                            className={`h-3 w-3 ${passed ? "opacity-100" : "opacity-30"}`}
                          />
                          {req.label}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            )}
          </div>

          <Input
            label="Confirm Password"
            name="confirmPassword"
            type="password"
            placeholder="Confirm your password"
            value={formData.confirmPassword}
            onChange={handleChange}
            error={formErrors.confirmPassword}
            leftIcon={<Lock className="h-4 w-4" />}
            autoComplete="new-password"
          />

          <div className="text-xs text-foreground-muted">
            By creating an account, you agree to our{" "}
            <Link href="/terms" className="text-primary hover:underline">
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link href="/privacy" className="text-primary hover:underline">
              Privacy Policy
            </Link>
            .
          </div>

          <Button
            type="submit"
            className="w-full"
            size="lg"
            isLoading={isLoading}
            disabled={!emailOtpSent || !emailOtpCode.trim()}
          >
            Create Account
          </Button>

          <div className="text-center text-sm text-foreground-muted pt-2 border-t border-border/50">
            Already have an account?{" "}
            <Link href="/login" className="text-primary hover:underline font-semibold">
              Sign in
            </Link>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
