/*
 * utils.ts — Shared utility functions used across the Zoniq frontend.
 * Provides class name merging, date/time/price formatting, string
 * manipulation helpers, and a generic debounce function.
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// Merges class names using clsx (conditional classes) and tailwind-merge (deduplicates Tailwind classes)
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Formats a date string or Date object into a short, human-readable date (e.g., "Fri, 20 Feb 2026")
export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString("en-IN", {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

// Formats a date string or Date object into a 2-digit hour:minute time string (e.g., "07:30 PM")
export function formatTime(date: string | Date): string {
  return new Date(date).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Combines formatDate and formatTime into a single string (e.g., "Fri, 20 Feb 2026 at 07:30 PM")
export function formatDateTime(date: string | Date): string {
  return `${formatDate(date)} at ${formatTime(date)}`;
}

// Formats a numeric or string price into Indian Rupee currency format (e.g., "Rs.1,500")
export function formatPrice(price: number | string): string {
  const numPrice = typeof price === "string" ? parseFloat(price) : price;
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(numPrice);
}

// Converts a text string into a URL-friendly slug (lowercase, hyphens, no special chars)
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .replace(/[\s_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

// Truncates a string to the given length, appending "..." if it exceeds the limit
export function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.slice(0, length).trim() + "...";
}

// Extracts up to 2 uppercase initials from a name (e.g., "John Doe" -> "JD")
export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

// Creates a debounced version of a function that delays invocation by the given milliseconds.
// Resets the timer on each subsequent call so the function only fires after the caller stops calling.
export function debounce<T extends (...args: never[]) => void>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}
