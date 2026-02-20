/*
 * Checkout page: handles the full payment flow for cart items.
 *
 * Flow:
 *   1. Fetches the current cart and pre-fills contact info from the user profile.
 *   2. Loads the Razorpay checkout script (external payment gateway).
 *   3. On "Pay" click: creates a pending booking via the API, creates a Razorpay order,
 *      and opens the Razorpay checkout modal.
 *   4. On payment success: verifies the payment signature with the backend,
 *      clears the cart, and redirects to the order confirmation page.
 *   5. On payment dismissal: cancels the pending booking to release held seats.
 *
 * Requires authentication; redirects to /login if not authenticated.
 */

"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Script from "next/script";
import {
    ArrowLeft,
    Shield,
    Clock,
    CreditCard,
    Loader2,
    AlertCircle,
    CheckCircle2,
    Calendar,
    Ticket,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCartStore } from "@/store/cart";
import { useAuthStore, useIsAuthenticated } from "@/store/auth";
import { paymentsApi } from "@/lib/api";
import type { RazorpayOptions, RazorpayResponse } from "@/types";

// Extend the Window interface to include the Razorpay constructor loaded via external script
declare global {
    interface Window {
        Razorpay: new (options: RazorpayOptions) => {
            open: () => void;
            on: (event: string, handler: () => void) => void;
        };
    }
}

export default function CheckoutPage() {
    const router = useRouter();
    const isAuthenticated = useIsAuthenticated();
    const { user } = useAuthStore();
    const { cart, isLoading, error, checkout, clearError, clearCart, fetchCurrentCart } = useCartStore();

    // Contact info fields (pre-filled from user profile)
    const [contactEmail, setContactEmail] = useState("");
    const [contactPhone, setContactPhone] = useState("");
    // Terms acceptance checkbox
    const [acceptTerms, setAcceptTerms] = useState(false);
    // Payment processing state
    const [isProcessing, setIsProcessing] = useState(false);
    const [paymentError, setPaymentError] = useState("");
    // Tracks whether the Razorpay external script has finished loading
    const [razorpayLoaded, setRazorpayLoaded] = useState(false);

    // On mount: redirect if not authenticated, fetch cart, and pre-fill contact info
    useEffect(() => {
        if (!isAuthenticated) {
            router.push("/login?redirect=/checkout");
            return;
        }
        // Fetch the cart on mount
        fetchCurrentCart();
        if (user) {
            setContactEmail(user.email || "");
            setContactPhone(user.phone || "");
        }
    }, [isAuthenticated, user, router, fetchCurrentCart]);

    // Check if Razorpay is already loaded (from cache or previous page)
    useEffect(() => {
        if (typeof window !== "undefined" && window.Razorpay) {
            setRazorpayLoaded(true);
        }
    }, []);

    // Callback after Razorpay payment succeeds: verify signature with backend
    const handlePaymentSuccess = useCallback(async (
        response: RazorpayResponse,
        bookingId: number
    ) => {
        try {
            // Verify payment with backend
            const result = await paymentsApi.verifyPayment({
                razorpayOrderId: response.razorpay_order_id,
                razorpayPaymentId: response.razorpay_payment_id,
                razorpaySignature: response.razorpay_signature,
            });

            if (result.success) {
                // Clear cart and redirect to confirmation
                clearCart();
                router.push(`/order-confirmation/${result.bookingId}`);
            } else {
                setPaymentError("Payment verification failed. Please contact support.");
                setIsProcessing(false);
            }
        } catch (err: any) {
            console.error("Payment verification error:", err);
            setPaymentError(err.response?.data?.detail || "Payment verification failed");
            setIsProcessing(false);
        }
    }, [clearCart, router]);

    // Open the Razorpay checkout modal with the order details
    const openRazorpayCheckout = useCallback((
        orderData: {
            orderId: string;
            amount: number;
            currency: string;
            keyId: string;
            bookingId: number;
            bookingNumber: string;
            userName: string | null;
            userEmail: string;
            userPhone: string | null;
        }
    ) => {
        if (!window.Razorpay) {
            setPaymentError("Payment gateway not loaded. Please refresh the page.");
            setIsProcessing(false);
            return;
        }

        const options: RazorpayOptions = {
            key: orderData.keyId,
            amount: orderData.amount,
            currency: orderData.currency,
            name: "ZONIQ",
            description: `Booking #${orderData.bookingNumber}`,
            order_id: orderData.orderId,
            prefill: {
                name: orderData.userName || undefined,
                email: orderData.userEmail,
                contact: orderData.userPhone || undefined,
            },
            theme: {
                color: "#6366F1", // Primary color
            },
            handler: (response) => {
                handlePaymentSuccess(response, orderData.bookingId);
            },
            modal: {
                ondismiss: async () => {
                    // Cancel the pending booking and release seats
                    try {
                        await paymentsApi.cancelPendingBooking(orderData.bookingId);
                        // Refresh the cart to get updated seat availability
                        await fetchCurrentCart();
                    } catch (err) {
                        console.error("Failed to cancel booking:", err);
                    }
                    setPaymentError("Payment was cancelled. Seats have been released.");
                    setIsProcessing(false);
                },
            },
        };

        const razorpay = new window.Razorpay(options);
        razorpay.open();
    }, [handlePaymentSuccess, fetchCurrentCart]);

    // Main checkout handler: create booking -> create Razorpay order -> open payment modal
    const handleCheckout = async () => {
        if (!acceptTerms) return;
        if (!razorpayLoaded) {
            setPaymentError("Payment gateway is loading. Please wait...");
            return;
        }

        setIsProcessing(true);
        setPaymentError("");
        clearError();

        try {
            // Step 1: Create booking (pending status)
            const bookingId = await checkout({
                contactEmail: contactEmail || undefined,
                contactPhone: contactPhone || undefined,
            });

            // Step 2: Create Razorpay order
            const orderData = await paymentsApi.createOrder(bookingId);

            // Step 3: Open Razorpay checkout
            openRazorpayCheckout(orderData);
        } catch (err: any) {
            console.error("Checkout error:", err);
            setPaymentError(err.response?.data?.detail || err.message || "Checkout failed");
            setIsProcessing(false);
        }
    };

    // Show loading state while cart data is being fetched
    if (isLoading) {
        return (
            <div className="container mx-auto px-4 py-20">
                <div className="flex flex-col items-center justify-center text-center">
                    <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
                    <p className="text-foreground-muted">Loading checkout...</p>
                </div>
            </div>
        );
    }

    // Empty cart state: redirect user to browse events
    if (!cart || cart.items.length === 0) {
        return (
            <div className="container mx-auto px-4 py-20">
                <div className="flex flex-col items-center justify-center text-center">
                    <h1 className="mb-3 text-2xl font-bold text-foreground">No items to checkout</h1>
                    <p className="mb-8 text-foreground-muted">Select tickets from an event to proceed.</p>
                    <Link
                        href="/events"
                        className="inline-flex items-center gap-2 rounded-xl bg-primary px-8 py-3 text-white font-medium hover:bg-primary/90 transition-colors"
                    >
                        Browse Events
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <>
            {/* Load Razorpay Script asynchronously after page is interactive */}
            <Script
                src="https://checkout.razorpay.com/v1/checkout.js"
                strategy="afterInteractive"
                onLoad={() => setRazorpayLoaded(true)}
                onReady={() => setRazorpayLoaded(true)}
                onError={() => setPaymentError("Failed to load payment gateway")}
            />

            <div className="container mx-auto px-4 py-8">
                {/* Header with back navigation */}
                <div className="mb-8">
                    <Link
                        href="/events"
                        className="mb-4 inline-flex items-center gap-2 text-sm text-foreground-muted hover:text-foreground transition-colors"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Back to Events
                    </Link>
                    <h1 className="text-3xl font-bold text-foreground">Checkout</h1>
                    <p className="mt-1 text-foreground-muted">Review your order and complete your purchase</p>
                </div>

                {/* Error banner for cart or payment errors */}
                {(error || paymentError) && (
                    <div className="mb-6 flex items-center gap-3 rounded-xl bg-red-500/10 p-4 text-red-500">
                        <AlertCircle className="h-5 w-5 flex-shrink-0" />
                        <p className="text-sm">{paymentError || error}</p>
                    </div>
                )}

                <div className="grid gap-8 lg:grid-cols-3">
                    {/* Left: Order Details & Contact */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Event Info Card: thumbnail, title, and date/time */}
                        <div className="rounded-2xl border border-border bg-background-soft p-6">
                            <h2 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
                                <Calendar className="h-5 w-5 text-primary" />
                                Event Details
                            </h2>
                            <div className="flex gap-4">
                                {cart.eventImage && (
                                    <img
                                        src={cart.eventImage}
                                        alt={cart.eventTitle || "Event"}
                                        className="h-20 w-32 rounded-xl object-cover"
                                    />
                                )}
                                <div>
                                    <h3 className="font-semibold text-foreground text-lg">{cart.eventTitle}</h3>
                                    {cart.eventDate && (
                                        <p className="mt-1 text-sm text-foreground-muted">
                                            {new Date(cart.eventDate).toLocaleDateString("en-IN", {
                                                weekday: "long",
                                                year: "numeric",
                                                month: "long",
                                                day: "numeric",
                                                hour: "2-digit",
                                                minute: "2-digit",
                                            })}
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Ticket Summary: lists each ticket line item with category, quantity, and subtotal */}
                        <div className="rounded-2xl border border-border bg-background-soft p-6">
                            <h2 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
                                <Ticket className="h-5 w-5 text-primary" />
                                Tickets ({cart.itemCount})
                            </h2>
                            <div className="space-y-3">
                                {cart.items.map((item) => (
                                    <div key={item.id} className="flex items-center justify-between rounded-xl bg-background p-4">
                                        <div className="flex items-center gap-3">
                                            <div
                                                className="h-3 w-3 rounded-full"
                                                style={{ backgroundColor: item.categoryColor || "#3B82F6" }}
                                            />
                                            <div>
                                                <span className="font-medium text-foreground">{item.categoryName}</span>
                                                <span className="ml-2 text-sm text-foreground-muted">x {item.quantity}</span>
                                            </div>
                                        </div>
                                        <span className="font-semibold text-foreground">₹{parseFloat(item.subtotal).toLocaleString()}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Contact Information: email (for e-ticket delivery) and optional phone */}
                        <div className="rounded-2xl border border-border bg-background-soft p-6">
                            <h2 className="text-lg font-bold text-foreground mb-4">Contact Information</h2>
                            <p className="text-sm text-foreground-muted mb-4">
                                We&apos;ll send your e-tickets to this email
                            </p>
                            <div className="grid gap-4 sm:grid-cols-2">
                                <div>
                                    <label className="mb-1.5 block text-sm font-medium text-foreground">Email</label>
                                    <input
                                        type="email"
                                        value={contactEmail}
                                        onChange={(e) => setContactEmail(e.target.value)}
                                        className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-foreground placeholder:text-foreground-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                                        placeholder="your@email.com"
                                    />
                                </div>
                                <div>
                                    <label className="mb-1.5 block text-sm font-medium text-foreground">Phone (optional)</label>
                                    <input
                                        type="tel"
                                        value={contactPhone}
                                        onChange={(e) => setContactPhone(e.target.value)}
                                        className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-foreground placeholder:text-foreground-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                                        placeholder="+91 XXXXX XXXXX"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Right: Payment Summary sidebar (sticky) */}
                    <div className="lg:col-span-1">
                        <div className="sticky top-24 rounded-2xl border border-border bg-background-soft p-6">
                            <h2 className="text-lg font-bold text-foreground mb-6">Payment Summary</h2>

                            {/* Price breakdown: subtotal and total */}
                            <div className="space-y-3">
                                <div className="flex justify-between text-sm">
                                    <span className="text-foreground-muted">Subtotal ({cart.itemCount} tickets)</span>
                                    <span className="text-foreground">₹{parseFloat(cart.subtotal).toLocaleString()}</span>
                                </div>
                                <div className="flex justify-between border-t border-border pt-3">
                                    <span className="text-lg font-bold text-foreground">Total</span>
                                    <span className="text-lg font-bold text-primary">
                                        ₹{parseFloat(cart.total).toLocaleString()}
                                    </span>
                                </div>
                            </div>

                            {/* Terms & Conditions checkbox */}
                            <label className="mt-6 flex items-start gap-3 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={acceptTerms}
                                    onChange={(e) => setAcceptTerms(e.target.checked)}
                                    className="mt-1 h-4 w-4 rounded border-border accent-primary"
                                />
                                <span className="text-xs text-foreground-muted leading-relaxed">
                                    I agree to the{" "}
                                    <Link href="/terms" className="text-primary hover:underline">Terms & Conditions</Link>
                                    {" "}and{" "}
                                    <Link href="/refund-policy" className="text-primary hover:underline">Cancellation Policy</Link>
                                </span>
                            </label>

                            {/* Pay Button: disabled until terms accepted and Razorpay is loaded */}
                            <button
                                onClick={handleCheckout}
                                disabled={!acceptTerms || isProcessing || !razorpayLoaded}
                                className={cn(
                                    "mt-6 flex w-full items-center justify-center gap-2 rounded-xl px-6 py-4 text-sm font-semibold transition-all",
                                    acceptTerms && !isProcessing && razorpayLoaded
                                        ? "bg-primary text-white hover:bg-primary/90 shadow-lg shadow-primary/20"
                                        : "bg-foreground-muted/20 text-foreground-muted cursor-not-allowed"
                                )}
                            >
                                {isProcessing ? (
                                    <>
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                        Processing...
                                    </>
                                ) : !razorpayLoaded ? (
                                    <>
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                        Loading Payment...
                                    </>
                                ) : (
                                    <>
                                        <CreditCard className="h-4 w-4" />
                                        Pay ₹{parseFloat(cart.total).toLocaleString()}
                                    </>
                                )}
                            </button>

                            {/* Trust Badges: reassure users about payment security */}
                            <div className="mt-6 space-y-3">
                                <div className="flex items-center gap-2 text-xs text-foreground-muted">
                                    <Shield className="h-4 w-4 text-green-500" />
                                    <span>Secure payment via Razorpay</span>
                                </div>
                                <div className="flex items-center gap-2 text-xs text-foreground-muted">
                                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                                    <span>Instant e-ticket delivery</span>
                                </div>
                                <div className="flex items-center gap-2 text-xs text-foreground-muted">
                                    <Clock className="h-4 w-4 text-green-500" />
                                    <span>Free cancellation up to 24 hours before</span>
                                </div>
                            </div>

                            {/* Accepted Payment Methods */}
                            <div className="mt-6 pt-4 border-t border-border">
                                <p className="text-xs text-foreground-muted mb-3">Accepted payment methods</p>
                                <div className="flex flex-wrap gap-2">
                                    <span className="px-2 py-1 bg-background rounded text-xs text-foreground-muted">UPI</span>
                                    <span className="px-2 py-1 bg-background rounded text-xs text-foreground-muted">Cards</span>
                                    <span className="px-2 py-1 bg-background rounded text-xs text-foreground-muted">Net Banking</span>
                                    <span className="px-2 py-1 bg-background rounded text-xs text-foreground-muted">Wallets</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}
