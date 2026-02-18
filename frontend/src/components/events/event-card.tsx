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
              className="object-cover transition-transform duration-500 ease-out group-hover:scale-105"
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-background-elevated to-background-card">
              <div className="text-5xl font-bold text-foreground-subtle/30">
                {event.title[0]}
              </div>
            </div>
          )}

          {/* Gradient overlay at bottom of image */}
          <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-background-card to-transparent" />

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
                className="opacity-0 group-hover:opacity-100 transition-all duration-300"
              />
            )}
          </div>
        </div>

        {/* Content */}
        <div className="p-5 space-y-3">
          {/* Title */}
          <h3 className="font-semibold text-lg text-foreground line-clamp-2 group-hover:text-primary transition-colors duration-300 tracking-tight">
            {event.title}
          </h3>

          {/* Description */}
          {event.shortDescription && (
            <p className="text-sm text-foreground-muted line-clamp-2 leading-relaxed">
              {event.shortDescription}
            </p>
          )}

          {/* Details */}
          <div className="space-y-2 text-sm text-foreground-muted">
            <div className="flex items-center gap-2.5">
              <Calendar className="h-3.5 w-3.5 text-primary/60" />
              <span>{formatDate(event.eventDate)}</span>
            </div>
            <div className="flex items-center gap-2.5">
              <Clock className="h-3.5 w-3.5 text-primary/60" />
              <span>{formatTime(event.eventDate)}</span>
            </div>
            {event.venue && (
              <div className="flex items-center gap-2.5">
                <MapPin className="h-3.5 w-3.5 text-primary/60" />
                <span className="truncate">
                  {event.venue.name}, {event.venue.city}
                </span>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between pt-3 border-t border-border/50">
            <div className="flex items-center gap-1.5 text-xs text-foreground-subtle">
              <Users className="h-3.5 w-3.5" />
              <span>
                {event.availableSeats} / {event.totalSeats} seats
              </span>
            </div>

            {isBookingOpen && !isSoldOut && (
              <span className="text-xs font-semibold text-primary group-hover:translate-x-0.5 transition-transform duration-300 inline-flex items-center gap-1">
                Book Now
                <span className="text-primary/60">&rarr;</span>
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
      <div className="p-5 space-y-3">
        <div className="h-6 bg-background-elevated rounded-lg animate-pulse" />
        <div className="h-4 bg-background-elevated rounded-lg animate-pulse w-3/4" />
        <div className="space-y-2">
          <div className="h-4 bg-background-elevated rounded-lg animate-pulse w-1/2" />
          <div className="h-4 bg-background-elevated rounded-lg animate-pulse w-2/3" />
        </div>
        <div className="pt-3 border-t border-border/50">
          <div className="h-4 bg-background-elevated rounded-lg animate-pulse w-1/3" />
        </div>
      </div>
    </Card>
  );
}
