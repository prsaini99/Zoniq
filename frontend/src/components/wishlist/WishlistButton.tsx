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

const sizes = {
  sm: "h-4 w-4",
  md: "h-5 w-5",
  lg: "h-6 w-6",
};

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
  const isInWishlist = useIsInWishlist(event.id);
  const { addToWishlist, removeFromWishlist } = useWishlistStore();
  const [isAnimating, setIsAnimating] = useState(false);

  const handleClick = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!isAuthenticated) {
      // Redirect to login
      window.location.href = `/login?redirect=/events/${event.slug}`;
      return;
    }

    setIsAnimating(true);
    setTimeout(() => setIsAnimating(false), 300);

    if (isInWishlist) {
      await removeFromWishlist(event.id);
    } else {
      await addToWishlist(event);
    }
  };

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
