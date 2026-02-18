"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { X, Minus, Plus, Ticket, Loader2 } from "lucide-react";
import { cn, formatPrice } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useCartStore } from "@/store/cart";
import { cartApi } from "@/lib/api";
import type { SeatCategory } from "@/types";

interface TicketSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  eventId: number;
  eventTitle: string;
  categories: SeatCategory[];
  maxTicketsPerBooking: number;
}

interface TicketQuantity {
  categoryId: number;
  quantity: number;
}

export function TicketSelectionModal({
  isOpen,
  onClose,
  eventId,
  eventTitle,
  categories,
  maxTicketsPerBooking,
}: TicketSelectionModalProps) {
  const router = useRouter();
  const { addItem, clearCartAsync } = useCartStore();
  const [quantities, setQuantities] = useState<TicketQuantity[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize quantities when modal opens
  useEffect(() => {
    if (isOpen) {
      setQuantities(
        categories
          .filter((c) => c.isActive && c.availableSeats > 0)
          .map((c) => ({ categoryId: c.id, quantity: 0 }))
      );
      setError(null);
    }
  }, [isOpen, categories]);

  const updateQuantity = (categoryId: number, delta: number) => {
    setQuantities((prev) =>
      prev.map((q) => {
        if (q.categoryId !== categoryId) return q;
        const category = categories.find((c) => c.id === categoryId);
        if (!category) return q;

        const newQty = Math.max(0, Math.min(q.quantity + delta, category.availableSeats, maxTicketsPerBooking));
        return { ...q, quantity: newQty };
      })
    );
  };

  const totalTickets = quantities.reduce((sum, q) => sum + q.quantity, 0);
  const totalAmount = quantities.reduce((sum, q) => {
    const category = categories.find((c) => c.id === q.categoryId);
    return sum + (category ? parseFloat(category.price) * q.quantity : 0);
  }, 0);

  const handleProceedToPayment = async () => {
    const selectedTickets = quantities.filter((q) => q.quantity > 0);
    if (selectedTickets.length === 0) {
      setError("Please select at least one ticket");
      return;
    }

    if (totalTickets > maxTicketsPerBooking) {
      setError(`Maximum ${maxTicketsPerBooking} tickets per booking`);
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      // Clear any existing cart first (on backend too)
      await clearCartAsync();

      // Add all selected tickets to cart
      for (const ticket of selectedTickets) {
        await addItem({
          eventId,
          seatCategoryId: ticket.categoryId,
          quantity: ticket.quantity,
        });
      }

      // Navigate to checkout
      router.push("/checkout");
    } catch (err: any) {
      setError(err.message || "Failed to add tickets. Please try again.");
      setIsProcessing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-md mx-4 bg-background-card rounded-2xl shadow-2xl border border-border overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div>
            <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
              <Ticket className="h-5 w-5 text-primary" />
              Select Tickets
            </h2>
            <p className="text-sm text-foreground-muted mt-1 truncate max-w-[280px]">
              {eventTitle}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-background-soft text-foreground-muted hover:text-foreground transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Ticket Categories */}
        <div className="p-6 space-y-4 max-h-[400px] overflow-y-auto">
          {categories
            .filter((c) => c.isActive)
            .map((category) => {
              const quantityObj = quantities.find((q) => q.categoryId === category.id);
              const quantity = quantityObj?.quantity || 0;
              const isSoldOut = category.availableSeats === 0;

              return (
                <div
                  key={category.id}
                  className={cn(
                    "p-4 rounded-xl border transition-all",
                    isSoldOut
                      ? "border-border opacity-50"
                      : quantity > 0
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-border-hover"
                  )}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <div
                          className="h-3 w-3 rounded-full ring-2 ring-offset-2 ring-offset-background-card"
                          style={{ backgroundColor: category.colorCode || "#3B82F6" }}
                        />
                        <span className="font-semibold text-foreground">
                          {category.name}
                        </span>
                      </div>
                      <div className="text-sm text-foreground-muted">
                        {formatPrice(category.price)}
                      </div>
                      <div className="text-xs text-foreground-subtle mt-1">
                        {isSoldOut
                          ? "Sold out"
                          : `${category.availableSeats} available`}
                      </div>
                    </div>

                    {/* Quantity Controls */}
                    {!isSoldOut && (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => updateQuantity(category.id, -1)}
                          disabled={quantity === 0}
                          className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-background hover:bg-background-soft disabled:opacity-50 transition-colors"
                        >
                          <Minus className="h-3 w-3" />
                        </button>
                        <span className="w-8 text-center font-semibold text-foreground">
                          {quantity}
                        </span>
                        <button
                          onClick={() => updateQuantity(category.id, 1)}
                          disabled={quantity >= Math.min(category.availableSeats, maxTicketsPerBooking - totalTickets + quantity)}
                          className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-background hover:bg-background-soft disabled:opacity-50 transition-colors"
                        >
                          <Plus className="h-3 w-3" />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-border bg-background-soft space-y-4">
          {error && (
            <div className="text-sm text-red-500 text-center">{error}</div>
          )}

          {/* Summary */}
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-foreground-muted">
                {totalTickets} {totalTickets === 1 ? "ticket" : "tickets"}
              </div>
              <div className="text-2xl font-bold text-foreground">
                {formatPrice(totalAmount)}
              </div>
            </div>
            <Button
              onClick={handleProceedToPayment}
              disabled={totalTickets === 0 || isProcessing}
              className="px-6"
              size="lg"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Processing...
                </>
              ) : (
                "Proceed to Payment"
              )}
            </Button>
          </div>

          <p className="text-xs text-foreground-subtle text-center">
            Max {maxTicketsPerBooking} tickets per booking
          </p>
        </div>
      </div>
    </div>
  );
}
