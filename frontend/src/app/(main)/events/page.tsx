"use client";

import { Suspense, useEffect, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Search, Filter, X, Calendar, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { PageSpinner } from "@/components/ui/spinner";
import { EventCard, EventCardSkeleton } from "@/components/events/event-card";
import { eventsApi } from "@/lib/api";
import type { Event, EventCategory } from "@/types";
import { CATEGORY_LABELS } from "@/types";
import { debounce } from "@/lib/utils";

const categories: { value: EventCategory; label: string }[] = [
  { value: "concert", label: "Concerts" },
  { value: "sports", label: "Sports" },
  { value: "theater", label: "Theater" },
  { value: "comedy", label: "Comedy" },
  { value: "conference", label: "Conferences" },
  { value: "workshop", label: "Workshops" },
  { value: "festival", label: "Festivals" },
  { value: "exhibition", label: "Exhibitions" },
  { value: "other", label: "Other" },
];

function EventsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [events, setEvents] = useState<Event[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [searchQuery, setSearchQuery] = useState(
    searchParams.get("search") || ""
  );
  const [selectedCategory, setSelectedCategory] = useState<string | null>(
    searchParams.get("category")
  );
  const [selectedCity, setSelectedCity] = useState(
    searchParams.get("city") || ""
  );
  const [showFilters, setShowFilters] = useState(false);

  const pageSize = 12;
  const hasMore = events.length < total;

  const fetchEvents = useCallback(
    async (pageNum: number, append = false) => {
      if (append) {
        setIsLoadingMore(true);
      } else {
        setIsLoading(true);
      }

      try {
        const response = await eventsApi.list({
          page: pageNum,
          pageSize,
          category: selectedCategory || undefined,
          city: selectedCity || undefined,
          search: searchQuery || undefined,
        });

        if (append) {
          setEvents((prev) => [...prev, ...response.events]);
        } else {
          setEvents(response.events);
        }
        setTotal(response.total);
        setPage(pageNum);
      } catch (error) {
        console.error("Failed to fetch events:", error);
      } finally {
        setIsLoading(false);
        setIsLoadingMore(false);
      }
    },
    [selectedCategory, selectedCity, searchQuery]
  );

  useEffect(() => {
    fetchEvents(1);
  }, [fetchEvents]);

  // Update URL params when filters change
  useEffect(() => {
    const params = new URLSearchParams();
    if (searchQuery) params.set("search", searchQuery);
    if (selectedCategory) params.set("category", selectedCategory);
    if (selectedCity) params.set("city", selectedCity);

    const newUrl = params.toString()
      ? `/events?${params.toString()}`
      : "/events";
    router.replace(newUrl, { scroll: false });
  }, [searchQuery, selectedCategory, selectedCity, router]);

  const handleSearch = debounce((value: string) => {
    setSearchQuery(value);
  }, 300);

  const handleCityChange = debounce((value: string) => {
    setSelectedCity(value);
  }, 300);

  const handleCategorySelect = (category: string | null) => {
    setSelectedCategory(category);
  };

  const handleLoadMore = () => {
    if (!isLoadingMore && hasMore) {
      fetchEvents(page + 1, true);
    }
  };

  const clearFilters = () => {
    setSearchQuery("");
    setSelectedCategory(null);
    setSelectedCity("");
  };

  const hasActiveFilters = searchQuery || selectedCategory || selectedCity;

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-2">
          Discover Events
        </h1>
        <p className="text-foreground-muted">
          Find and book tickets for amazing events near you
        </p>
      </div>

      {/* Search & Filters */}
      <div className="mb-8 space-y-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <Input
              placeholder="Search events..."
              defaultValue={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              leftIcon={<Search className="h-4 w-4" />}
            />
          </div>
          <Button
            variant="secondary"
            onClick={() => setShowFilters(!showFilters)}
            leftIcon={<Filter className="h-4 w-4" />}
          >
            Filters
            {hasActiveFilters && (
              <span className="ml-1 h-2 w-2 rounded-full bg-primary" />
            )}
          </Button>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="p-4 rounded-lg border border-border bg-background-card space-y-4 animate-fade-in">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-foreground">Filters</h3>
              {hasActiveFilters && (
                <button
                  onClick={clearFilters}
                  className="text-sm text-primary hover:underline"
                >
                  Clear all
                </button>
              )}
            </div>

            {/* City Filter */}
            <div>
              <label className="block text-sm text-foreground-muted mb-2">
                City
              </label>
              <Input
                placeholder="Filter by city..."
                defaultValue={selectedCity}
                onChange={(e) => handleCityChange(e.target.value)}
                leftIcon={<MapPin className="h-4 w-4" />}
              />
            </div>

            {/* Categories */}
            <div>
              <label className="block text-sm text-foreground-muted mb-2">
                Categories
              </label>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handleCategorySelect(null)}
                  className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
                    !selectedCategory
                      ? "bg-primary text-white"
                      : "bg-background-elevated text-foreground-muted hover:text-foreground"
                  }`}
                >
                  All
                </button>
                {categories.map((category) => (
                  <button
                    key={category.value}
                    onClick={() => handleCategorySelect(category.value)}
                    className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
                      selectedCategory === category.value
                        ? "bg-primary text-white"
                        : "bg-background-elevated text-foreground-muted hover:text-foreground"
                    }`}
                  >
                    {category.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Active Filters */}
        {hasActiveFilters && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm text-foreground-muted">
              Active filters:
            </span>
            {searchQuery && (
              <Badge variant="secondary" className="gap-1">
                Search: {searchQuery}
                <button
                  onClick={() => setSearchQuery("")}
                  className="hover:text-foreground"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            )}
            {selectedCategory && (
              <Badge variant="secondary" className="gap-1">
                {CATEGORY_LABELS[selectedCategory as EventCategory]}
                <button
                  onClick={() => setSelectedCategory(null)}
                  className="hover:text-foreground"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            )}
            {selectedCity && (
              <Badge variant="secondary" className="gap-1">
                City: {selectedCity}
                <button
                  onClick={() => setSelectedCity("")}
                  className="hover:text-foreground"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            )}
          </div>
        )}
      </div>

      {/* Results */}
      <div className="mb-4 text-sm text-foreground-muted">
        {!isLoading && (
          <span>
            Showing {events.length} of {total} events
          </span>
        )}
      </div>

      {/* Events Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, i) => (
            <EventCardSkeleton key={i} />
          ))}
        </div>
      ) : events.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {events.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>

          {/* Load More */}
          {hasMore && (
            <div className="flex justify-center mt-8">
              <Button
                variant="outline"
                onClick={handleLoadMore}
                isLoading={isLoadingMore}
              >
                Load More Events
              </Button>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-16">
          <Calendar className="h-16 w-16 text-foreground-muted mx-auto mb-4" />
          <h3 className="text-xl font-medium text-foreground mb-2">
            No events found
          </h3>
          <p className="text-foreground-muted mb-6">
            {hasActiveFilters
              ? "Try adjusting your filters to find more events"
              : "Check back later for new events"}
          </p>
          {hasActiveFilters && (
            <Button variant="outline" onClick={clearFilters}>
              Clear Filters
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

export default function EventsPage() {
  return (
    <Suspense fallback={<PageSpinner />}>
      <EventsContent />
    </Suspense>
  );
}
