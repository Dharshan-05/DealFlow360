"use client";

import React, { useEffect, useRef, useCallback } from "react";
import { X, AlertCircle, CheckCircle2, AlertTriangle, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type ModalVariant = "default" | "confirmation" | "destructive" | "info";

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children?: React.ReactNode;
  variant?: ModalVariant;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm?: () => void | Promise<void>;
  isLoading?: boolean;
  className?: string;
  size?: "sm" | "md" | "lg" | "xl";
}

const variantIcons = {
  default: null,
  confirmation: CheckCircle2,
  destructive: AlertCircle,
  info: Info,
};

const variantIconStyles = {
  default: "",
  confirmation: "bg-emerald-50 text-emerald-600 border-emerald-200",
  destructive: "bg-rose-50 text-rose-600 border-rose-200",
  info: "bg-blue-50 text-blue-600 border-blue-200",
};

export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  variant = "default",
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  onConfirm,
  isLoading = false,
  className,
  size = "md",
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen && !isLoading) {
        onClose();
      }

      // Basic focus trap within the dialog
      if (e.key === "Tab" && modalRef.current) {
        const focusables = modalRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusables.length === 0) return;

        const first = focusables[0];
        const last = focusables[focusables.length - 1];

        if (e.shiftKey && document.activeElement === first) {
          last.focus();
          e.preventDefault();
        } else if (!e.shiftKey && document.activeElement === last) {
          first.focus();
          e.preventDefault();
        }
      }
    },
    [isOpen, isLoading, onClose]
  );

  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement as HTMLElement;
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);

      // Focus the modal container
      setTimeout(() => {
        modalRef.current?.focus();
      }, 50);
    } else {
      document.body.style.overflow = "";
      previousActiveElement.current?.focus();
    }

    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  const Icon = variantIcons[variant];

  const sizeClasses = {
    sm: "max-w-md",
    md: "max-w-lg",
    lg: "max-w-2xl",
    xl: "max-w-4xl",
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      aria-describedby={description ? "modal-description" : undefined}
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity"
        onClick={() => {
          if (!isLoading) onClose();
        }}
        aria-hidden="true"
      />

      {/* Modal Card */}
      <div
        ref={modalRef}
        tabIndex={-1}
        className={cn(
          "relative z-50 w-full rounded-xl border border-border bg-card p-6 shadow-2xl transition-all duration-200 focus:outline-none",
          sizeClasses[size],
          className
        )}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 pb-4">
          <div className="flex items-start gap-3">
            {Icon && (
              <div
                className={cn(
                  "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border",
                  variantIconStyles[variant]
                )}
                aria-hidden="true"
              >
                <Icon className="h-5 w-5" />
              </div>
            )}
            <div>
              <h3 id="modal-title" className="text-lg font-bold text-foreground leading-snug">
                {title}
              </h3>
              {description && (
                <p id="modal-description" className="mt-1 text-xs text-muted leading-relaxed">
                  {description}
                </p>
              )}
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            aria-label="Close dialog"
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        {/* Content Body */}
        {children && <div className="py-2 text-sm text-foreground">{children}</div>}

        {/* Action Footer (if onConfirm provided) */}
        {onConfirm && (
          <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-border">
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
              disabled={isLoading}
              type="button"
            >
              {cancelLabel}
            </Button>
            <Button
              variant={variant === "destructive" ? "destructive" : "primary"}
              size="sm"
              onClick={onConfirm}
              isLoading={isLoading}
              type="button"
            >
              {confirmLabel}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
