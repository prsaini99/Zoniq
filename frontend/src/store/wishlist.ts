import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { WishlistItem, Event } from "@/types";
import { wishlistApi } from "@/lib/api";

interface WishlistState {
  items: WishlistItem[];
  eventIds: Set<number>;
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
      items: [],
      eventIds: new Set<number>(),
      isLoading: false,
      error: null,

      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),

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

      addToWishlist: async (event: Event) => {
        const { eventIds, items } = get();
        if (eventIds.has(event.id)) return;

        // Optimistic update
        const newEventIds = new Set(eventIds);
        newEventIds.add(event.id);
        set({ eventIds: newEventIds });

        try {
          const newItem = await wishlistApi.add(event.id);
          set({ items: [...items, newItem] });
        } catch (error) {
          // Revert on error
          const revertedIds = new Set(eventIds);
          revertedIds.delete(event.id);
          set({ eventIds: revertedIds });
          const message =
            error instanceof Error ? error.message : "Failed to add to wishlist";
          set({ error: message });
        }
      },

      removeFromWishlist: async (eventId: number) => {
        const { eventIds, items } = get();
        if (!eventIds.has(eventId)) return;

        // Optimistic update
        const newEventIds = new Set(eventIds);
        newEventIds.delete(eventId);
        const newItems = items.filter((item) => item.eventId !== eventId);
        set({ eventIds: newEventIds, items: newItems });

        try {
          await wishlistApi.remove(eventId);
        } catch (error) {
          // Revert on error
          set({ eventIds, items });
          const message =
            error instanceof Error ? error.message : "Failed to remove from wishlist";
          set({ error: message });
        }
      },

      isInWishlist: (eventId: number) => {
        return get().eventIds.has(eventId);
      },

      clearWishlist: () => {
        set({ items: [], eventIds: new Set() });
      },
    }),
    {
      name: "zoniq-wishlist",
      partialize: (state) => ({
        items: state.items,
        eventIds: Array.from(state.eventIds),
      }),
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

// Selector hooks
export const useWishlistItems = () => useWishlistStore((state) => state.items);
export const useWishlistCount = () => useWishlistStore((state) => state.items.length);
export const useIsInWishlist = (eventId: number) =>
  useWishlistStore((state) => state.eventIds.has(eventId));
