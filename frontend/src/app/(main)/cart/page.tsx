/*
 * Cart page: displays the user's current ticket cart for a single event.
 *
 * Key features:
 *   - Requires authentication; redirects unauthenticated users to /login.
 *   - Fetches the current cart from the API on mount via the cart store.
 *   - Shows a countdown timer for cart expiry (seats are held temporarily).
 *   - Allows adjusting ticket quantity (increment/decrement) and removing items.
 *   - Displays an order summary sidebar with subtotal, total, and checkout link.
 *   - Shows appropriate empty state when the cart has no items.
 */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
    ShoppingCart,
    Trash2,
    Minus,
    Plus,
    Clock,
    ArrowRight,
    ShoppingBag,
    AlertCircle,
    X,
    Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCartStore } from "@/store/cart";
import { useIsAuthenticated } from "@/store/auth";
import type { Cart } from "@/types";

export default function CartPage() {
    const router = useRouter();
    const isAuthenticated = useIsAuthenticated();
    const { cart, isLoading, error, updateItem, removeItem, clearError, fetchCurrentCart } = useCartStore();
    // Tracks the remaining time before the cart expires (formatted as mm:ss)
    const [timeLeft, setTimeLeft] = useState("");

    // Redirect unauthenticated users to login, otherwise fetch the cart
    useEffect(() => {
        if (!isAuthenticated) {
            router.push("/login?redirect=/cart");
            return;
        }
        // Fetch the current cart on mount
        fetchCurrentCart();
    }, [isAuthenticated, router, fetchCurrentCart]);

    // Timer for cart expiry: updates every second with remaining time
    useEffect(() => {
        if (!cart?.expiresAt) return;

        const updateTimer = () => {
            const now = new Date();
            const expires = new Date(cart.expiresAt);
            const diff = expires.getTime() - now.getTime();

            if (diff <= 0) {
                setTimeLeft("Expired");
                return;
            }

            const mins = Math.floor(diff / 60000);
            const secs = Math.floor((diff % 60000) / 1000);
            setTimeLeft(`${mins}:${secs.toString().padStart(2, "0")}`);
        };

        updateTimer();
        const interval = setInterval(updateTimer, 1000);
        return () => clearInterval(interval);
    }, [cart?.expiresAt]);

    // Show loading spinner while fetching cart
    if (isLoading) {
        return (
            <div className="container mx-auto px-4 py-20">
                <div className="flex flex-col items-center justify-center text-center">
                    <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
                    <p className="text-foreground-muted">Loading your cart...</p>
                </div>
            </div>
        );
    }

    // Empty cart state: prompt the user to browse events
    if (!cart || cart.items.length === 0) {
        return (
            <div className="container mx-auto px-4 py-20">
                <div className="flex flex-col items-center justify-center text-center">
                    <div className="mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-background-soft">
                        <ShoppingBag className="h-12 w-12 text-foreground-muted" />
                    </div>
                    <h1 className="mb-3 text-2xl font-bold text-foreground">Your cart is empty</h1>
                    <p className="mb-8 max-w-md text-foreground-muted">
                        Looks like you haven&apos;t added any tickets yet. Browse our events to find something you&apos;ll love!
                    </p>
                    <Link
                        href="/events"
                        className="inline-flex items-center gap-2 rounded-xl bg-primary px-8 py-3 text-white font-medium hover:bg-primary/90 transition-colors"
                    >
                        Browse Events
                        <ArrowRight className="h-4 w-4" />
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Header with event title and expiry countdown */}
            <div className="mb-8 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-foreground">Your Cart</h1>
                    {cart.eventTitle && (
                        <p className="mt-1 text-foreground-muted">
                            Tickets for <span className="font-medium text-foreground">{cart.eventTitle}</span>
                        </p>
                    )}
                </div>
                {/* Cart expiry timer badge */}
                {timeLeft && timeLeft !== "Expired" && (
                    <div className="flex items-center gap-2 rounded-lg bg-amber-500/10 px-4 py-2 text-amber-500">
                        <Clock className="h-4 w-4" />
                        <span className="text-sm font-medium">Expires in {timeLeft}</span>
                    </div>
                )}
            </div>

            {/* Dismissible error banner */}
            {error && (
                <div className="mb-6 flex items-center gap-3 rounded-xl bg-red-500/10 p-4 text-red-500">
                    <AlertCircle className="h-5 w-5 flex-shrink-0" />
                    <p className="text-sm">{error}</p>
                    <button onClick={clearError} className="ml-auto">
                        <X className="h-4 w-4" />
                    </button>
                </div>
            )}

            <div className="grid gap-8 lg:grid-cols-3">
                {/* Cart Items list (left column) */}
                <div className="lg:col-span-2 space-y-4">
                    {cart.items.map((item) => (
                        <div
                            key={item.id}
                            className="group rounded-2xl border border-border bg-background-soft p-6 transition-all hover:border-primary/20"
                        >
                            <div className="flex items-start justify-between gap-4">
                                <div className="flex-1">
                                    {/* Category color dot and name */}
                                    <div className="flex items-center gap-3 mb-3">
                                        <div
                                            className="h-4 w-4 rounded-full ring-2 ring-offset-2 ring-offset-background-soft"
                                            style={{ backgroundColor: item.categoryColor || "#3B82F6" }}
                                        />
                                        <h3 className="text-lg font-semibold text-foreground">
                                            {item.categoryName || "Ticket"}
                                        </h3>
                                    </div>

                                    {/* Per-ticket price and assigned seat count */}
                                    <div className="flex items-center gap-4 text-sm text-foreground-muted">
                                        <span>₹{parseFloat(item.unitPrice).toLocaleString()} per ticket</span>
                                        {item.seatIds && item.seatIds.length > 0 && (
                                            <span className="rounded-md bg-primary/10 px-2 py-0.5 text-primary text-xs font-medium">
                                                {item.seatIds.length} assigned seat(s)
                                            </span>
                                        )}
                                    </div>
                                </div>

                                {/* Remove item button */}
                                <button
                                    onClick={() => removeItem(item.id)}
                                    disabled={isLoading}
                                    className="p-2 rounded-lg text-foreground-muted hover:text-red-500 hover:bg-red-500/10 transition-colors"
                                    title="Remove"
                                >
                                    <Trash2 className="h-4 w-4" />
                                </button>
                            </div>

                            <div className="mt-4 flex items-center justify-between">
                                {/* Quantity Controls: +/- buttons for non-assigned-seat items */}
                                {!item.seatIds ? (
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => {
                                                if (item.quantity > 1) updateItem(item.id, item.quantity - 1);
                                            }}
                                            disabled={isLoading || item.quantity <= 1}
                                            className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-background hover:bg-background-soft disabled:opacity-50 transition-colors"
                                        >
                                            <Minus className="h-3 w-3" />
                                        </button>
                                        <span className="w-10 text-center font-semibold text-foreground">{item.quantity}</span>
                                        <button
                                            onClick={() => updateItem(item.id, item.quantity + 1)}
                                            disabled={isLoading || item.quantity >= 10}
                                            className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-background hover:bg-background-soft disabled:opacity-50 transition-colors"
                                        >
                                            <Plus className="h-3 w-3" />
                                        </button>
                                    </div>
                                ) : (
                                    <span className="text-sm text-foreground-muted">
                                        Qty: {item.quantity}
                                    </span>
                                )}

                                {/* Line item subtotal */}
                                <span className="text-lg font-bold text-foreground">
                                    ₹{parseFloat(item.subtotal).toLocaleString()}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Order Summary sidebar (right column, sticky) */}
                <div className="lg:col-span-1">
                    <div className="sticky top-24 rounded-2xl border border-border bg-background-soft p-6">
                        <h2 className="text-lg font-bold text-foreground mb-6">Order Summary</h2>

                        {/* Price Breakdown */}
                        <div className="space-y-3 border-t border-border pt-4">
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

                        {/* Checkout Button */}
                        <Link
                            href="/checkout"
                            className={cn(
                                "mt-6 flex w-full items-center justify-center gap-2 rounded-xl px-6 py-3.5 text-sm font-semibold transition-all",
                                "bg-primary text-white hover:bg-primary/90 shadow-lg shadow-primary/20"
                            )}
                        >
                            Proceed to Checkout
                            <ArrowRight className="h-4 w-4" />
                        </Link>

                        {/* Continue Shopping link */}
                        <Link
                            href="/events"
                            className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl border border-border px-6 py-3 text-sm font-medium text-foreground-muted hover:text-foreground hover:bg-background transition-colors"
                        >
                            Continue Shopping
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
