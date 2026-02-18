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
    <div className="container mx-auto px-4 py-10">
      {/* Header */}
      <div className="mb-10">
        <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-3 tracking-tight">
          Discover Events
        </h1>
        <p className="text-foreground-muted text-lg">
          Find and book tickets for amazing events near you
        </p>
      </div>

      {/* Search & Filters */}
      <div className="mb-8 space-y-4">
        <div className="flex flex-col sm:flex-row gap-3">
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
              <span className="ml-1.5 h-1.5 w-1.5 rounded-full bg-primary" />
            )}
          </Button>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="p-5 rounded-xl border border-border bg-background-card space-y-5 animate-scale-in">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-foreground text-sm">Filters</h3>
              {hasActiveFilters && (
                <button
                  onClick={clearFilters}
                  className="text-xs font-medium text-primary hover:underline"
                >
                  Clear all
                </button>
              )}
            </div>

            {/* City Filter */}
            <div>
              <label className="block text-xs font-medium text-foreground-subtle mb-2 uppercase tracking-wider">
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
              <label className="block text-xs font-medium text-foreground-subtle mb-3 uppercase tracking-wider">
                Categories
              </label>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handleCategorySelect(null)}
                  className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all duration-200 ${
                    !selectedCategory
                      ? "bg-primary text-white shadow-glow-sm"
                      : "bg-background-elevated text-foreground-muted hover:text-foreground border border-border"
                  }`}
                >
                  All
                </button>
                {categories.map((category) => (
                  <button
                    key={category.value}
                    onClick={() => handleCategorySelect(category.value)}
                    className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all duration-200 ${
                      selectedCategory === category.value
                        ? "bg-primary text-white shadow-glow-sm"
                        : "bg-background-elevated text-foreground-muted hover:text-foreground border border-border"
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
            <span className="text-xs text-foreground-subtle font-medium uppercase tracking-wider">
              Active:
            </span>
            {searchQuery && (
              <Badge variant="secondary" className="gap-1.5">
                Search: {searchQuery}
                <button
                  onClick={() => setSearchQuery("")}
                  className="hover:text-foreground transition-colors"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            )}
            {selectedCategory && (
              <Badge variant="secondary" className="gap-1.5">
                {CATEGORY_LABELS[selectedCategory as EventCategory]}
                <button
                  onClick={() => setSelectedCategory(null)}
                  className="hover:text-foreground transition-colors"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            )}
            {selectedCity && (
              <Badge variant="secondary" className="gap-1.5">
                City: {selectedCity}
                <button
                  onClick={() => setSelectedCity("")}
                  className="hover:text-foreground transition-colors"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            )}
          </div>
        )}
      </div>

      {/* Results count */}
      <div className="mb-6 text-xs text-foreground-subtle font-medium uppercase tracking-wider">
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
            <div className="flex justify-center mt-12">
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
        <div className="text-center py-20">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-foreground/5 mb-6">
            <Calendar className="h-7 w-7 text-foreground-subtle" />
          </div>
          <h3 className="text-xl font-semibold text-foreground mb-2">
            No events found
          </h3>
          <p className="text-foreground-muted mb-8 max-w-sm mx-auto">
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
