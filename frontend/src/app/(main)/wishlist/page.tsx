/*
 * Wishlist page: displays the user's saved/favorited events in a responsive grid.
 *
 * Key features:
 *   - Requires authentication; redirects to /login if not logged in.
 *   - Fetches the wishlist from the wishlist store on mount.
 *   - Each event card has a hover-reveal "Remove" button to remove it from the wishlist.
 *   - Shows an empty state with a CTA to browse events when the wishlist is empty.
 *   - Includes a "Tips" section at the bottom with helpful reminders for users.
 */

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Heart, Trash2, Calendar, MapPin, ArrowRight } from "lucide-react";
import { Button, Card, CardContent } from "@/components/ui";
import { EventCard, EventCardSkeleton } from "@/components/events/event-card";
import { useIsAuthenticated } from "@/store/auth";
import { useWishlistStore, useWishlistItems } from "@/store/wishlist";

// Empty state component shown when the wishlist has no items
function EmptyState() {
  return (
    <div className="text-center py-12">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-background-elevated mb-4">
        <Heart className="h-8 w-8 text-foreground-muted" />
      </div>
      <h3 className="text-lg font-semibold text-foreground mb-2">
        Your wishlist is empty
      </h3>
      <p className="text-foreground-muted mb-6 max-w-md mx-auto">
        Save events you&apos;re interested in by clicking the heart icon. They&apos;ll
        appear here so you can easily find them later.
      </p>
      <Button onClick={() => (window.location.href = "/events")}>
        Browse Events
      </Button>
    </div>
  );
}

export default function WishlistPage() {
  const router = useRouter();
  const isAuthenticated = useIsAuthenticated();
  // Wishlist items from the store (each item contains the associated event data)
  const items = useWishlistItems();
  const { fetchWishlist, removeFromWishlist, isLoading, error } = useWishlistStore();

  // Redirect unauthenticated users to login, otherwise fetch the wishlist
  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login?redirect=/wishlist");
      return;
    }
    fetchWishlist();
  }, [isAuthenticated, router, fetchWishlist]);

  // Remove an event from the wishlist by its event ID
  const handleRemove = async (eventId: number) => {
    await removeFromWishlist(eventId);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Header with wishlist count and "Browse More" button */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
              <Heart className="h-8 w-8 text-primary" />
              My Wishlist
            </h1>
            <p className="text-foreground-muted mt-1">
              {items.length} {items.length === 1 ? "event" : "events"} saved
            </p>
          </div>
          {items.length > 0 && (
            <Button
              variant="outline"
              onClick={() => router.push("/events")}
              rightIcon={<ArrowRight className="h-4 w-4" />}
            >
              Browse More
            </Button>
          )}
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 rounded-lg bg-error/10 text-error">
            {error}
          </div>
        )}

        {/* Loading State: skeleton cards while data is fetched */}
        {isLoading && (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <EventCardSkeleton />
            <EventCardSkeleton />
            <EventCardSkeleton />
          </div>
        )}

        {/* Wishlist Items grid with hover-reveal remove buttons */}
        {!isLoading && (
          <>
            {items.length === 0 ? (
              <EmptyState />
            ) : (
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {items.map((item) => (
                  <div key={item.id} className="relative group">
                    <EventCard event={item.event} />
                    {/* Remove Button Overlay: visible on hover */}
                    <button
                      onClick={() => handleRemove(item.eventId)}
                      className="absolute top-3 right-3 p-2 rounded-full bg-background-card/90 backdrop-blur-sm border border-border opacity-0 group-hover:opacity-100 transition-opacity hover:bg-error/20 hover:border-error hover:text-error"
                      title="Remove from wishlist"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Tips Section: helpful advice shown below wishlist items */}
        {!isLoading && items.length > 0 && (
          <div className="mt-12">
            <Card>
              <CardContent className="p-6">
                <h3 className="font-semibold text-foreground mb-4">
                  Tips for Your Wishlist
                </h3>
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Calendar className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-foreground">
                        Check Event Dates
                      </h4>
                      <p className="text-xs text-foreground-muted mt-1">
                        Make sure to book before tickets sell out
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <MapPin className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-foreground">
                        Venue Details
                      </h4>
                      <p className="text-xs text-foreground-muted mt-1">
                        Check venue location and accessibility
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Heart className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-foreground">
                        Share with Friends
                      </h4>
                      <p className="text-xs text-foreground-muted mt-1">
                        Plan together by sharing event links
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
