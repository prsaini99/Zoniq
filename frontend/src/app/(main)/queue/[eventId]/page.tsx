"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import {
    Users,
    Clock,
    ArrowRight,
    AlertCircle,
    Loader2,
    LogOut,
    CheckCircle,
    Wifi,
    WifiOff,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useQueueStore, useQueuePosition, useQueueConnected } from "@/store/queue";
import { useIsAuthenticated } from "@/store/auth";
import { eventsApi, queueApi } from "@/lib/api";
import type { EventDetail, QueueStatusResponse } from "@/types";

export default function QueueWaitingRoom() {
    const router = useRouter();
    const params = useParams();
    const eventId = parseInt(params.eventId as string, 10);

    const isAuthenticated = useIsAuthenticated();
    const position = useQueuePosition();
    const isConnected = useQueueConnected();
    const { joinQueue, leaveQueue, isConnecting, error, reset } = useQueueStore();

    const [event, setEvent] = useState<EventDetail | null>(null);
    const [queueStatus, setQueueStatus] = useState<QueueStatusResponse | null>(null);
    const [isLoadingEvent, setIsLoadingEvent] = useState(true);
    const [isLeaving, setIsLeaving] = useState(false);
    const [expiryCountdown, setExpiryCountdown] = useState<string | null>(null);

    // Redirect if not authenticated
    useEffect(() => {
        if (!isAuthenticated) {
            router.push(`/login?redirect=/queue/${eventId}`);
        }
    }, [isAuthenticated, router]);

    // Load event details and queue status
    useEffect(() => {
        const loadData = async () => {
            if (!eventId) return;

            setIsLoadingEvent(true);
            try {
                const [eventData, statusData] = await Promise.all([
                    eventsApi.getByIdOrSlug(eventId),
                    queueApi.getStatus(eventId),
                ]);
                setEvent(eventData);
                setQueueStatus(statusData);
            } catch {
                // Handle error
            } finally {
                setIsLoadingEvent(false);
            }
        };

        loadData();
    }, [eventId]);

    // Join queue on mount
    useEffect(() => {
        if (!eventId || !isAuthenticated) return;

        // Check if already in queue
        const checkAndJoin = async () => {
            try {
                // Try to get existing position
                const existingPosition = await queueApi.getPosition(eventId);
                if (existingPosition) {
                    // Already in queue, just connect WebSocket
                    useQueueStore.setState({
                        position: existingPosition,
                        eventId
                    });
                    useQueueStore.getState().connect(eventId);
                    return;
                }
            } catch {
                // Not in queue, join it
            }

            try {
                await joinQueue(eventId);
            } catch {
                // Error handled by store
            }
        };

        checkAndJoin();

        return () => {
            // Don't disconnect on unmount, user might navigate away temporarily
        };
    }, [eventId, isAuthenticated, joinQueue]);

    // Handle expiry countdown when processing
    useEffect(() => {
        if (!position?.expiresAt || position.status !== "processing") {
            setExpiryCountdown(null);
            return;
        }

        const updateCountdown = () => {
            const now = new Date();
            const expires = new Date(position.expiresAt!);
            const diff = expires.getTime() - now.getTime();

            if (diff <= 0) {
                setExpiryCountdown("Expired");
                return;
            }

            const mins = Math.floor(diff / 60000);
            const secs = Math.floor((diff % 60000) / 1000);
            setExpiryCountdown(`${mins}:${secs.toString().padStart(2, "0")}`);
        };

        updateCountdown();
        const interval = setInterval(updateCountdown, 1000);
        return () => clearInterval(interval);
    }, [position?.expiresAt, position?.status]);

    const handleLeaveQueue = useCallback(async () => {
        // Show confirmation dialog
        const confirmed = window.confirm(
            "Are you sure you want to leave the queue? You will lose your position and will need to rejoin at the back of the queue."
        );

        if (!confirmed) return;

        setIsLeaving(true);
        try {
            await leaveQueue();
            reset();
            router.push(`/events/${event?.slug || eventId}`);
        } catch {
            // Error handled by store
        } finally {
            setIsLeaving(false);
        }
    }, [leaveQueue, reset, router, event?.slug, eventId]);

    const handleProceedToCheckout = useCallback(() => {
        // Pass query param to indicate user has queue access
        router.push(`/events/${event?.slug || eventId}?fromQueue=true`);
    }, [router, event?.slug, eventId]);

    // Loading state
    if (isLoadingEvent || isConnecting) {
        return (
            <div className="container mx-auto px-4 py-20">
                <div className="flex flex-col items-center justify-center">
                    <Loader2 className="h-12 w-12 animate-spin text-primary" />
                    <p className="mt-4 text-foreground-muted">
                        {isConnecting ? "Joining queue..." : "Loading..."}
                    </p>
                </div>
            </div>
        );
    }

    // Can proceed to checkout
    if (position?.canProceed) {
        return (
            <div className="container mx-auto px-4 py-20">
                <div className="mx-auto max-w-lg text-center">
                    <div className="mb-8 flex justify-center">
                        <div className="flex h-24 w-24 items-center justify-center rounded-full bg-green-500/10">
                            <CheckCircle className="h-12 w-12 text-green-500" />
                        </div>
                    </div>

                    <h1 className="mb-3 text-3xl font-bold text-foreground">
                        It&apos;s Your Turn!
                    </h1>
                    <p className="mb-8 text-foreground-muted">
                        You can now proceed to select your tickets for{" "}
                        <span className="font-medium text-foreground">{event?.title}</span>
                    </p>

                    {expiryCountdown && (
                        <div className="mb-8 flex items-center justify-center gap-2 text-amber-500">
                            <Clock className="h-5 w-5" />
                            <span className="font-medium">
                                Time remaining: {expiryCountdown}
                            </span>
                        </div>
                    )}

                    <button
                        onClick={handleProceedToCheckout}
                        className="inline-flex items-center gap-2 rounded-xl bg-primary px-8 py-4 text-lg font-semibold text-white shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all"
                    >
                        Select Tickets
                        <ArrowRight className="h-5 w-5" />
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-12">
            <div className="mx-auto max-w-2xl">
                {/* Event Info Header */}
                {event && (
                    <div className="mb-8 text-center">
                        <h1 className="text-2xl font-bold text-foreground">{event.title}</h1>
                        <p className="mt-1 text-foreground-muted">
                            {new Date(event.eventDate).toLocaleDateString("en-IN", {
                                weekday: "long",
                                day: "numeric",
                                month: "long",
                                year: "numeric",
                            })}
                        </p>
                    </div>
                )}

                {/* Connection Status */}
                <div className="mb-6 flex items-center justify-center gap-2">
                    {isConnected ? (
                        <>
                            <Wifi className="h-4 w-4 text-green-500" />
                            <span className="text-sm text-green-500">Connected</span>
                        </>
                    ) : (
                        <>
                            <WifiOff className="h-4 w-4 text-amber-500" />
                            <span className="text-sm text-amber-500">Reconnecting...</span>
                        </>
                    )}
                </div>

                {/* Error Message */}
                {error && (
                    <div className="mb-6 flex items-center gap-3 rounded-xl bg-red-500/10 p-4 text-red-500">
                        <AlertCircle className="h-5 w-5 flex-shrink-0" />
                        <p className="text-sm">{error}</p>
                    </div>
                )}

                {/* Queue Position Card */}
                <div className="rounded-3xl border border-border bg-background-soft p-8 text-center shadow-xl">
                    <div className="mb-6">
                        <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-2 text-primary">
                            <Users className="h-4 w-4" />
                            <span className="text-sm font-medium">Virtual Queue</span>
                        </div>
                    </div>

                    {/* Position Display */}
                    <div className="mb-8">
                        <p className="text-sm uppercase tracking-wider text-foreground-muted">
                            Your Position
                        </p>
                        <div className="my-4 flex items-baseline justify-center gap-1">
                            <span className="text-7xl font-bold text-primary">
                                {position?.position || "-"}
                            </span>
                        </div>
                        {position && position.totalAhead > 0 && (
                            <p className="text-foreground-muted">
                                {position.totalAhead} {position.totalAhead === 1 ? "person" : "people"} ahead of you
                            </p>
                        )}
                    </div>

                    {/* Wait Time Estimate */}
                    {position?.estimatedWaitMinutes !== null && position?.estimatedWaitMinutes !== undefined && (
                        <div className="mb-8 rounded-xl bg-background p-4">
                            <div className="flex items-center justify-center gap-2 text-foreground-muted">
                                <Clock className="h-5 w-5" />
                                <span>Estimated wait:</span>
                                <span className="font-semibold text-foreground">
                                    {position.estimatedWaitMinutes === 0
                                        ? "Less than a minute"
                                        : `~${position.estimatedWaitMinutes} minute${position.estimatedWaitMinutes !== 1 ? "s" : ""}`}
                                </span>
                            </div>
                        </div>
                    )}

                    {/* Queue Stats */}
                    {queueStatus && (
                        <div className="mb-8 grid grid-cols-2 gap-4">
                            <div className="rounded-xl bg-background p-4">
                                <p className="text-2xl font-bold text-foreground">
                                    {queueStatus.totalInQueue}
                                </p>
                                <p className="text-xs text-foreground-muted">In Queue</p>
                            </div>
                            <div className="rounded-xl bg-background p-4">
                                <p className="text-2xl font-bold text-foreground">
                                    {queueStatus.currentlyProcessing}
                                </p>
                                <p className="text-xs text-foreground-muted">Being Served</p>
                            </div>
                        </div>
                    )}

                    {/* Status Info */}
                    <div className="mb-8 rounded-xl border border-primary/20 bg-primary/5 p-4">
                        <p className="text-sm text-foreground">
                            {position?.status === "waiting" ? (
                                <>
                                    Please keep this page open. You&apos;ll be notified when it&apos;s your turn.
                                </>
                            ) : position?.status === "processing" ? (
                                <>
                                    It&apos;s almost your turn! Get ready to select your tickets.
                                </>
                            ) : (
                                <>
                                    You&apos;re in the queue. We&apos;ll let you know when it&apos;s your turn.
                                </>
                            )}
                        </p>
                    </div>

                    {/* Leave Queue Button */}
                    <button
                        onClick={handleLeaveQueue}
                        disabled={isLeaving}
                        className={cn(
                            "inline-flex items-center gap-2 rounded-xl border border-border px-6 py-3",
                            "text-foreground-muted hover:text-red-500 hover:border-red-500/50 hover:bg-red-500/5",
                            "transition-all disabled:opacity-50"
                        )}
                    >
                        {isLeaving ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <LogOut className="h-4 w-4" />
                        )}
                        Leave Queue
                    </button>
                </div>

                {/* Tips Section */}
                <div className="mt-8 rounded-2xl border border-border bg-background-soft p-6">
                    <h3 className="mb-4 font-semibold text-foreground">Tips while you wait</h3>
                    <ul className="space-y-2 text-sm text-foreground-muted">
                        <li className="flex items-start gap-2">
                            <span className="text-primary">1.</span>
                            Keep this browser tab open to maintain your position
                        </li>
                        <li className="flex items-start gap-2">
                            <span className="text-primary">2.</span>
                            Have your payment details ready for a faster checkout
                        </li>
                        <li className="flex items-start gap-2">
                            <span className="text-primary">3.</span>
                            Know which ticket category you want before your turn
                        </li>
                        <li className="flex items-start gap-2">
                            <span className="text-primary">4.</span>
                            Your session will expire if you don&apos;t complete checkout in time
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    );
}
