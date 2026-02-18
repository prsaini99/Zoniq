import { create } from "zustand";
import type { QueuePositionResponse, QueueStatus } from "@/types";
import { queueApi } from "@/lib/api";

interface QueueState {
  // Current queue position data
  position: QueuePositionResponse | null;
  eventId: number | null;

  // Connection state
  isConnecting: boolean;
  isConnected: boolean;
  error: string | null;

  // WebSocket instance
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
  position: null,
  eventId: null,
  isConnecting: false,
  isConnected: false,
  error: null,
  ws: null,

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

  connect: (eventId: number) => {
    const { ws: existingWs } = get();

    // Close existing connection if any
    if (existingWs) {
      existingWs.close();
    }

    set({ isConnecting: true, error: null });

    let wsUrl: string;
    try {
      wsUrl = queueApi.getWebSocketUrl(eventId);
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Failed to connect", isConnecting: false });
      return;
    }

    console.log("Connecting to WebSocket:", wsUrl);
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("WebSocket connected successfully");
      set({ isConnected: true, isConnecting: false, error: null });
    };

    ws.onclose = (event) => {
      console.log("WebSocket closed:", event.code, event.reason);
      set({ isConnected: false, ws: null });

      // Set error message for specific close codes
      if (event.code === 4001) {
        set({ error: "Authentication failed - please log in again" });
        return;
      }

      // Auto-reconnect if not intentional close
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

    ws.onerror = (event) => {
      console.error("WebSocket error:", event);
      set({ error: "WebSocket connection error - check browser console for details", isConnecting: false });
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        switch (message.type) {
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

          case "error":
            set({ error: message.data.message || "Queue error" });
            break;

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

  disconnect: () => {
    const { ws } = get();
    if (ws) {
      ws.close(1000, "User disconnected");
    }
    set({ ws: null, isConnected: false });
  },

  refreshPosition: () => {
    const { ws, isConnected } = get();
    if (ws && isConnected) {
      ws.send(JSON.stringify({ type: "refresh" }));
    }
  },

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

// Selector hooks
export const useQueuePosition = () => useQueueStore((state) => state.position);
export const useQueueConnected = () => useQueueStore((state) => state.isConnected);
export const useCanProceedToCheckout = () =>
  useQueueStore((state) => state.position?.canProceed ?? false);
