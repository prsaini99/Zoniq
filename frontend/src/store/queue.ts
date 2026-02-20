/*
 * queue.ts — Zustand store for virtual waiting queue state management.
 * Manages queue position, WebSocket connectivity for real-time updates,
 * and queue join/leave operations. Used when events have high demand and
 * require a waiting room before users can proceed to booking.
 */

import { create } from "zustand";
import type { QueuePositionResponse, QueueStatus } from "@/types";
import { queueApi } from "@/lib/api";

// Shape of the queue store: state fields and action methods
interface QueueState {
  // Current queue position data (null when not in a queue)
  position: QueuePositionResponse | null;
  // The event ID the user is queued for
  eventId: number | null;

  // WebSocket connection state
  isConnecting: boolean;
  isConnected: boolean;
  error: string | null;

  // WebSocket instance for real-time position updates
  ws: WebSocket | null;

  // Actions
  joinQueue: (eventId: number) => Promise<void>;
  leaveQueue: () => Promise<void>;
  connect: (eventId: number) => void;
  disconnect: () => void;
  refreshPosition: () => void;
  reset: () => void;
}

export const useQueueStore = create<QueueState>()((set, get) => ({
  // ---- Initial state ----
  position: null,
  eventId: null,
  isConnecting: false,
  isConnected: false,
  error: null,
  ws: null,

  // Joins the queue for an event via REST API, then opens a WebSocket for real-time updates
  joinQueue: async (eventId: number) => {
    set({ error: null, isConnecting: true });
    try {
      const result = await queueApi.join(eventId);
      set({
        eventId,
        position: {
          queueEntryId: result.queueEntryId,
          eventId: result.eventId,
          position: result.position,
          status: result.status,
          estimatedWaitMinutes: result.estimatedWaitMinutes,
          totalAhead: result.totalAhead,
          expiresAt: null,
          canProceed: false,
        },
        isConnecting: false,
      });
      // Connect to WebSocket for real-time updates
      get().connect(eventId);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Failed to join queue";
      set({ error: message, isConnecting: false });
      throw error;
    }
  },

  // Leaves the queue for the current event, disconnects the WebSocket, and clears state
  leaveQueue: async () => {
    const { eventId } = get();
    if (!eventId) return;

    try {
      await queueApi.leave(eventId);
      get().disconnect();
      set({ position: null, eventId: null, error: null });
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Failed to leave queue";
      set({ error: message });
      throw error;
    }
  },

  // Opens a WebSocket connection for real-time queue position and status updates
  connect: (eventId: number) => {
    const { ws: existingWs } = get();

    // Close existing connection if any
    if (existingWs) {
      existingWs.close();
    }

    set({ isConnecting: true, error: null });

    // Build the authenticated WebSocket URL
    let wsUrl: string;
    try {
      wsUrl = queueApi.getWebSocketUrl(eventId);
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Failed to connect", isConnecting: false });
      return;
    }

    console.log("Connecting to WebSocket:", wsUrl);
    const ws = new WebSocket(wsUrl);

    // Mark connection as established
    ws.onopen = () => {
      console.log("WebSocket connected successfully");
      set({ isConnected: true, isConnecting: false, error: null });
    };

    // Handle connection close: set error for auth failures, auto-reconnect for unexpected closes
    ws.onclose = (event) => {
      console.log("WebSocket closed:", event.code, event.reason);
      set({ isConnected: false, ws: null });

      // Set error message for specific close codes
      if (event.code === 4001) {
        set({ error: "Authentication failed - please log in again" });
        return;
      }

      // Auto-reconnect after 3 seconds if the close was not intentional (code 1000)
      if (event.code !== 1000) {
        setTimeout(() => {
          const { eventId: currentEventId } = get();
          if (currentEventId) {
            console.log("Attempting to reconnect WebSocket...");
            get().connect(currentEventId);
          }
        }, 3000);
      }
    };

    // Log WebSocket errors
    ws.onerror = (event) => {
      console.error("WebSocket error:", event);
      set({ error: "WebSocket connection error - check browser console for details", isConnecting: false });
    };

    // Handle incoming WebSocket messages (position updates, status changes, errors, heartbeats)
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        switch (message.type) {
          // Server pushes updated queue position data
          case "position_update":
            set({
              position: {
                queueEntryId: get().position?.queueEntryId || "",
                eventId: get().eventId || 0,
                position: message.data.position,
                status: message.data.status as QueueStatus,
                estimatedWaitMinutes: message.data.estimatedWaitMinutes,
                totalAhead: message.data.totalAhead,
                expiresAt: message.data.expiresAt,
                canProceed: message.data.canProceed,
              },
            });
            break;

          // Server signals a queue status change (e.g., user can now proceed to checkout)
          case "status_change":
            // Update status and handle redirects
            if (message.data.newStatus === "processing") {
              set((state) => ({
                position: state.position
                  ? {
                      ...state.position,
                      status: message.data.newStatus as QueueStatus,
                      canProceed: true,
                    }
                  : null,
              }));
            }
            break;

          // Server reports an error
          case "error":
            set({ error: message.data.message || "Queue error" });
            break;

          // Heartbeat to keep the connection alive; no action needed
          case "heartbeat":
            // Connection alive, no action needed
            break;
        }
      } catch {
        // Ignore parse errors
      }
    };

    set({ ws, eventId });
  },

  // Gracefully closes the WebSocket connection with a normal close code (1000)
  disconnect: () => {
    const { ws } = get();
    if (ws) {
      ws.close(1000, "User disconnected");
    }
    set({ ws: null, isConnected: false });
  },

  // Sends a refresh request over the WebSocket to request updated position data
  refreshPosition: () => {
    const { ws, isConnected } = get();
    if (ws && isConnected) {
      ws.send(JSON.stringify({ type: "refresh" }));
    }
  },

  // Fully resets the queue store: disconnects WebSocket and clears all state
  reset: () => {
    get().disconnect();
    set({
      position: null,
      eventId: null,
      isConnecting: false,
      isConnected: false,
      error: null,
      ws: null,
    });
  },
}));

// ---- Convenience selector hooks ----

// Returns the current queue position data (or null)
export const useQueuePosition = () => useQueueStore((state) => state.position);

// Returns whether the WebSocket is currently connected
export const useQueueConnected = () => useQueueStore((state) => state.isConnected);

// Returns whether the user can proceed from the queue to checkout
export const useCanProceedToCheckout = () =>
  useQueueStore((state) => state.position?.canProceed ?? false);
