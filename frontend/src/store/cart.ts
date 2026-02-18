"use client";

import { create } from "zustand";
import { cartApi } from "@/lib/api";
import type { Cart } from "@/types";

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
    cart: null,
    cartCount: 0,
    isLoading: false,
    error: null,

    fetchCurrentCart: async () => {
        set({ isLoading: true, error: null });
        try {
            const cart = await cartApi.getCurrent();
            set({ cart, cartCount: cart?.itemCount || 0, isLoading: false });
        } catch (err: any) {
            set({ error: err.message || "Failed to load cart", isLoading: false });
        }
    },

    fetchCart: async (eventId: number) => {
        set({ isLoading: true, error: null });
        try {
            const cart = await cartApi.getOrCreate(eventId);
            set({ cart, isLoading: false });
        } catch (err: any) {
            set({ error: err.message || "Failed to load cart", isLoading: false });
        }
    },

    fetchCartCount: async () => {
        try {
            const count = await cartApi.getCount();
            set({ cartCount: count });
        } catch {
            // Silently fail for count
        }
    },

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

    updateItem: async (itemId: number, quantity: number) => {
        set({ isLoading: true, error: null });
        try {
            const cart = await cartApi.updateItem(itemId, quantity);
            set({ cart, cartCount: cart.itemCount, isLoading: false });
        } catch (err: any) {
            set({ error: err.message || "Failed to update item", isLoading: false });
        }
    },

    removeItem: async (itemId: number) => {
        set({ isLoading: true, error: null });
        try {
            const cart = await cartApi.removeItem(itemId);
            set({ cart, cartCount: cart.itemCount, isLoading: false });
        } catch (err: any) {
            set({ error: err.message || "Failed to remove item", isLoading: false });
        }
    },

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

    clearCart: () => set({ cart: null, cartCount: 0 }),
    clearCartAsync: async () => {
        try {
            await cartApi.clear();
            set({ cart: null, cartCount: 0 });
        } catch {
            // Silently fail - local state is cleared anyway
            set({ cart: null, cartCount: 0 });
        }
    },
    clearError: () => set({ error: null }),
}));
