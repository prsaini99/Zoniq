"use client";

import Link from "next/link";
import Image from "next/image";
import { Calendar, MapPin, Clock, Users } from "lucide-react";
import { cn, formatDate, formatTime } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { WishlistButton } from "@/components/wishlist/WishlistButton";
import type { Event } from "@/types";
import { CATEGORY_LABELS } from "@/types";

interface EventCardProps {
  event: Event;
  className?: string;
  showWishlist?: boolean;
}

export function EventCard({ event, className, showWishlist = true }: EventCardProps) {
  const isSoldOut = event.availableSeats === 0;
  const isBookingOpen = event.isBookingOpen;

  return (
    <Link href={`/events/${event.slug}`}>
      <Card
        hover
        className={cn(
          "overflow-hidden group",
          className
        )}
      >
        {/* Image */}
        <div className="relative aspect-[16/9] overflow-hidden bg-background-elevated">
          {event.bannerImageUrl ? (
            <Image
              src={event.bannerImageUrl}
              alt={event.title}
              fill
              className="object-cover transition-transform duration-300 group-hover:scale-105"
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-4xl font-bold text-foreground-subtle">
                {event.title[0]}
              </div>
            </div>
          )}

          {/* Category Badge */}
          <div className="absolute top-3 left-3">
            <Badge variant="default">
              {CATEGORY_LABELS[event.category] || event.category}
            </Badge>
          </div>

          {/* Status Badge or Wishlist Button */}
          <div className="absolute top-3 right-3 flex items-center gap-2">
            {isSoldOut ? (
              <Badge variant="error">Sold Out</Badge>
            ) : !isBookingOpen ? (
              <Badge variant="warning">Coming Soon</Badge>
            ) : null}
            {showWishlist && (
              <WishlistButton
                event={event}
                size="sm"
                className="opacity-0 group-hover:opacity-100 transition-opacity"
              />
            )}
          </div>
        </div>

        {/* Content */}
        <div className="p-4 space-y-3">
          {/* Title */}
          <h3 className="font-semibold text-lg text-foreground line-clamp-2 group-hover:text-primary transition-colors">
            {event.title}
          </h3>

          {/* Description */}
          {event.shortDescription && (
            <p className="text-sm text-foreground-muted line-clamp-2">
              {event.shortDescription}
            </p>
          )}

          {/* Details */}
          <div className="space-y-2 text-sm text-foreground-muted">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-primary" />
              <span>{formatDate(event.eventDate)}</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-primary" />
              <span>{formatTime(event.eventDate)}</span>
            </div>
            {event.venue && (
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-primary" />
                <span className="truncate">
                  {event.venue.name}, {event.venue.city}
                </span>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between pt-3 border-t border-border">
            <div className="flex items-center gap-1 text-sm text-foreground-muted">
              <Users className="h-4 w-4" />
              <span>
                {event.availableSeats} / {event.totalSeats} seats
              </span>
            </div>

            {isBookingOpen && !isSoldOut && (
              <span className="text-sm font-medium text-primary">
                Book Now →
              </span>
            )}
          </div>
        </div>
      </Card>
    </Link>
  );
}

// Skeleton for loading state
export function EventCardSkeleton() {
  return (
    <Card className="overflow-hidden">
      <div className="aspect-[16/9] bg-background-elevated animate-pulse" />
      <div className="p-4 space-y-3">
        <div className="h-6 bg-background-elevated rounded animate-pulse" />
        <div className="h-4 bg-background-elevated rounded animate-pulse w-3/4" />
        <div className="space-y-2">
          <div className="h-4 bg-background-elevated rounded animate-pulse w-1/2" />
          <div className="h-4 bg-background-elevated rounded animate-pulse w-2/3" />
        </div>
        <div className="pt-3 border-t border-border">
          <div className="h-4 bg-background-elevated rounded animate-pulse w-1/3" />
        </div>
      </div>
    </Card>
  );
}
