/*
 * cart.ts — Zustand store for shopping cart state management.
 * Tracks the active cart, item count, loading state, and errors.
 * Provides actions to fetch, add/update/remove items, checkout, and clear the cart.
 * This is a client-only store (no persistence) since cart data lives on the server.
 */

"use client";

import { create } from "zustand";
import { cartApi } from "@/lib/api";
import type { Cart } from "@/types";

// Shape of the cart store: state fields and action methods
interface CartState {
    cart: Cart | null;
    cartCount: number;
    isLoading: boolean;
    error: string | null;

    // Actions
    fetchCurrentCart: () => Promise<void>;
    fetchCart: (eventId: number) => Promise<void>;
    fetchCartCount: () => Promise<void>;
    addItem: (data: { eventId: number; seatCategoryId: number; quantity?: number; seatIds?: number[] }) => Promise<void>;
    updateItem: (itemId: number, quantity: number) => Promise<void>;
    removeItem: (itemId: number) => Promise<void>;
    checkout: (data?: { contactEmail?: string; contactPhone?: string }) => Promise<number>;
    clearCart: () => void;
    clearCartAsync: () => Promise<void>;
    clearError: () => void;
}

export const useCartStore = create<CartState>((set, get) => ({
    // ---- Initial state ----
    cart: null,
    cartCount: 0,
    isLoading: false,
    error: null,

    // Fetches the user's current active cart from the server
    fetchCurrentCart: async () => {
        set({ isLoading: true, error: null });
        try {
            const cart = await cartApi.getCurrent();
            set({ cart, cartCount: cart?.itemCount || 0, isLoading: false });
        } catch (err: any) {
            set({ error: err.message || "Failed to load cart", isLoading: false });
        }
    },

    // Fetches or creates a cart scoped to a specific event
    fetchCart: async (eventId: number) => {
        set({ isLoading: true, error: null });
        try {
            const cart = await cartApi.getOrCreate(eventId);
            set({ cart, isLoading: false });
        } catch (err: any) {
            set({ error: err.message || "Failed to load cart", isLoading: false });
        }
    },

    // Fetches only the cart item count (lightweight call, used for navbar badge)
    fetchCartCount: async () => {
        try {
            const count = await cartApi.getCount();
            set({ cartCount: count });
        } catch {
            // Silently fail for count
        }
    },

    // Adds seats/tickets to the cart and updates local state with the returned cart
    addItem: async (data) => {
        set({ isLoading: true, error: null });
        try {
            const cart = await cartApi.addItem(data);
            set({ cart, cartCount: cart.itemCount, isLoading: false });
        } catch (err: any) {
            const message = err.message || "Failed to add item";
            set({ error: message, isLoading: false });
            throw err;
        }
    },

    // Updates the quantity of a cart item by its ID
    updateItem: async (itemId: number, quantity: number) => {
        set({ isLoading: true, error: null });
        try {
            const cart = await cartApi.updateItem(itemId, quantity);
            set({ cart, cartCount: cart.itemCount, isLoading: false });
        } catch (err: any) {
            set({ error: err.message || "Failed to update item", isLoading: false });
        }
    },

    // Removes a specific item from the cart by its ID
    removeItem: async (itemId: number) => {
        set({ isLoading: true, error: null });
        try {
            const cart = await cartApi.removeItem(itemId);
            set({ cart, cartCount: cart.itemCount, isLoading: false });
        } catch (err: any) {
            set({ error: err.message || "Failed to remove item", isLoading: false });
        }
    },

    // Converts the cart into a booking and returns the new booking ID
    checkout: async (data) => {
        set({ isLoading: true, error: null });
        try {
            const booking = await cartApi.checkout(data);
            set({ cart: null, cartCount: 0, isLoading: false });
            return booking.id;
        } catch (err: any) {
            const message = err.message || "Checkout failed";
            set({ error: message, isLoading: false });
            throw err;
        }
    },

    // Clears cart from local state only (no server call)
    clearCart: () => set({ cart: null, cartCount: 0 }),

    // Clears the cart on the server and resets local state; silently handles errors
    clearCartAsync: async () => {
        try {
            await cartApi.clear();
            set({ cart: null, cartCount: 0 });
        } catch {
            // Silently fail - local state is cleared anyway
            set({ cart: null, cartCount: 0 });
        }
    },

    // Resets the error field
    clearError: () => set({ error: null }),
}));
