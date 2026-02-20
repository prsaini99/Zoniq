/**
 * WishlistButton - A toggle button that allows users to add or remove events
 * from their wishlist.
 *
 * Two visual variants:
 * - "icon" (default): A small circular button with just a Heart icon.
 *   Used on event cards with hover-reveal behavior.
 * - "button": A wider rectangular button with an optional "Save"/"Saved" label.
 *   Used on event detail pages.
 *
 * Behavior:
 * - If the user is not authenticated, clicking redirects to /login with a
 *   redirect query param back to the event page.
 * - If authenticated, toggles the wishlist state via the Zustand wishlist store
 *   (addToWishlist / removeFromWishlist).
 * - Plays a brief scale animation on the Heart icon when toggled.
 * - The Heart icon is filled when the event is in the wishlist.
 *
 * Props:
 * - event: The Event object to wishlist.
 * - size: "sm" | "md" | "lg" for icon and padding sizing.
 * - variant: "icon" | "button" for the two display modes.
 * - showLabel: Whether to show the "Save"/"Saved" text (button variant only).
 */
"use client";

import { useState } from "react";
import { Heart } from "lucide-react";
import { cn } from "@/lib/utils";
import { useWishlistStore, useIsInWishlist } from "@/store/wishlist";
import { useIsAuthenticated } from "@/store/auth";
import type { Event } from "@/types";

interface WishlistButtonProps {
  event: Event;
  size?: "sm" | "md" | "lg";
  variant?: "icon" | "button";
  className?: string;
  showLabel?: boolean;
}

// Heart icon size classes by size prop
const sizes = {
  sm: "h-4 w-4",
  md: "h-5 w-5",
  lg: "h-6 w-6",
};

// Padding classes for the "icon" variant by size prop
const buttonSizes = {
  sm: "p-1.5",
  md: "p-2",
  lg: "p-2.5",
};

export function WishlistButton({
  event,
  size = "md",
  variant = "icon",
  className,
  showLabel = false,
}: WishlistButtonProps) {
  const isAuthenticated = useIsAuthenticated();
  // Check if this specific event is already in the user's wishlist
  const isInWishlist = useIsInWishlist(event.id);
  const { addToWishlist, removeFromWishlist } = useWishlistStore();
  // Controls the brief scale-up animation on the heart icon
  const [isAnimating, setIsAnimating] = useState(false);

  // Click handler: redirect unauthenticated users, otherwise toggle wishlist
  const handleClick = async (e: React.MouseEvent) => {
    // Prevent the click from bubbling up to parent Link components
    e.preventDefault();
    e.stopPropagation();

    if (!isAuthenticated) {
      // Redirect to login with a return URL to come back to this event
      window.location.href = `/login?redirect=/events/${event.slug}`;
      return;
    }

    // Trigger a brief animation on the heart icon
    setIsAnimating(true);
    setTimeout(() => setIsAnimating(false), 300);

    // Toggle wishlist state
    if (isInWishlist) {
      await removeFromWishlist(event.id);
    } else {
      await addToWishlist(event);
    }
  };

  // "button" variant: rectangular button with optional text label
  if (variant === "button") {
    return (
      <button
        onClick={handleClick}
        className={cn(
          "flex items-center gap-2 px-4 py-2 rounded-lg border transition-all",
          isInWishlist
            ? "bg-primary/10 border-primary text-primary"
            : "bg-transparent border-border text-foreground-muted hover:border-primary hover:text-primary",
          className
        )}
      >
        <Heart
          className={cn(
            sizes[size],
            isInWishlist && "fill-current",
            isAnimating && "scale-125"
          )}
          style={{ transition: "transform 0.15s ease" }}
        />
        {showLabel && (
          <span className="text-sm font-medium">
            {isInWishlist ? "Saved" : "Save"}
          </span>
        )}
      </button>
    );
  }

  // "icon" variant (default): small circular button with just the heart icon
  return (
    <button
      onClick={handleClick}
      className={cn(
        "rounded-full transition-all",
        buttonSizes[size],
        isInWishlist
          ? "bg-primary/20 text-primary"
          : "bg-background-card/80 backdrop-blur-sm text-foreground-muted hover:text-primary hover:bg-primary/10",
        className
      )}
      title={isInWishlist ? "Remove from wishlist" : "Add to wishlist"}
    >
      <Heart
        className={cn(
          sizes[size],
          isInWishlist && "fill-current",
          isAnimating && "scale-125"
        )}
        style={{ transition: "transform 0.15s ease" }}
      />
    </button>
  );
}
