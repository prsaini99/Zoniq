/*
 * wishlist.ts — Zustand store for wishlist state management.
 * Persists wishlist items and event IDs to localStorage via zustand/persist.
 * Uses optimistic updates for add/remove: the UI updates immediately and
 * reverts on API failure. Maintains a Set of event IDs for O(1) lookups.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { WishlistItem, Event } from "@/types";
import { wishlistApi } from "@/lib/api";

// Shape of the wishlist store: state fields and action methods
interface WishlistState {
  items: WishlistItem[];
  eventIds: Set<number>; // Set for fast O(1) membership checks
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchWishlist: () => Promise<void>;
  addToWishlist: (event: Event) => Promise<void>;
  removeFromWishlist: (eventId: number) => Promise<void>;
  isInWishlist: (eventId: number) => boolean;
  clearWishlist: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useWishlistStore = create<WishlistState>()(
  persist(
    (set, get) => ({
      // ---- Initial state ----
      items: [],
      eventIds: new Set<number>(),
      isLoading: false,
      error: null,

      // Sets the loading flag
      setLoading: (isLoading) => set({ isLoading }),

      // Sets or clears the error message
      setError: (error) => set({ error }),

      // Fetches the full wishlist from the server and rebuilds the eventIds Set
      fetchWishlist: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await wishlistApi.list();
          const eventIds = new Set(response.items.map((item) => item.eventId));
          set({ items: response.items, eventIds, isLoading: false });
        } catch (error) {
          const message =
            error instanceof Error ? error.message : "Failed to fetch wishlist";
          set({ error: message, isLoading: false });
        }
      },

      // Adds an event to the wishlist with optimistic update (reverts on failure)
      addToWishlist: async (event: Event) => {
        const { eventIds, items } = get();
        if (eventIds.has(event.id)) return; // Already in wishlist, skip

        // Optimistic update: add the event ID immediately for instant UI feedback
        const newEventIds = new Set(eventIds);
        newEventIds.add(event.id);
        set({ eventIds: newEventIds });

        try {
          const newItem = await wishlistApi.add(event.id);
          set({ items: [...items, newItem] });
        } catch (error) {
          // Revert on error: remove the optimistically added event ID
          const revertedIds = new Set(eventIds);
          revertedIds.delete(event.id);
          set({ eventIds: revertedIds });
          const message =
            error instanceof Error ? error.message : "Failed to add to wishlist";
          set({ error: message });
        }
      },

      // Removes an event from the wishlist with optimistic update (reverts on failure)
      removeFromWishlist: async (eventId: number) => {
        const { eventIds, items } = get();
        if (!eventIds.has(eventId)) return; // Not in wishlist, skip

        // Optimistic update: remove immediately for instant UI feedback
        const newEventIds = new Set(eventIds);
        newEventIds.delete(eventId);
        const newItems = items.filter((item) => item.eventId !== eventId);
        set({ eventIds: newEventIds, items: newItems });

        try {
          await wishlistApi.remove(eventId);
        } catch (error) {
          // Revert on error: restore the original items and event IDs
          set({ eventIds, items });
          const message =
            error instanceof Error ? error.message : "Failed to remove from wishlist";
          set({ error: message });
        }
      },

      // Checks if a given event is currently in the wishlist
      isInWishlist: (eventId: number) => {
        return get().eventIds.has(eventId);
      },

      // Clears the wishlist from local state
      clearWishlist: () => {
        set({ items: [], eventIds: new Set() });
      },
    }),
    {
      name: "zoniq-wishlist", // localStorage key for persisted wishlist state
      // Persist items and eventIds (converted to array since Sets are not JSON-serializable)
      partialize: (state) => ({
        items: state.items,
        eventIds: Array.from(state.eventIds),
      }),
      // Custom merge to convert the persisted eventIds array back into a Set on rehydration
      merge: (persisted, current) => {
        const persistedState = persisted as { items?: WishlistItem[]; eventIds?: number[] };
        return {
          ...current,
          items: persistedState?.items || [],
          eventIds: new Set(persistedState?.eventIds || []),
        };
      },
    }
  )
);

// ---- Convenience selector hooks ----

// Returns the array of wishlist items
export const useWishlistItems = () => useWishlistStore((state) => state.items);

// Returns the total number of items in the wishlist
export const useWishlistCount = () => useWishlistStore((state) => state.items.length);

// Returns whether a specific event is in the wishlist (reactive to changes)
export const useIsInWishlist = (eventId: number) =>
  useWishlistStore((state) => state.eventIds.has(eventId));
