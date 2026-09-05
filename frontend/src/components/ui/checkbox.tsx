import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";

export interface CheckboxProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
  description?: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, label, description, id, disabled, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

    return (
      <div className="flex items-start gap-2.5">
        <input
          type="checkbox"
          id={inputId}
          ref={ref}
          disabled={disabled}
          className={cn(
            "h-4 w-4 rounded border-border text-primary focus:ring-2 focus:ring-primary focus:ring-offset-1 mt-0.5",
            "disabled:cursor-not-allowed disabled:opacity-60",
            className
          )}
          {...props}
        />
        {(label || description) && (
          <div className="flex flex-col">
            {label && (
              <label
                htmlFor={inputId}
                className={cn(
                  "text-sm font-medium text-foreground leading-tight cursor-pointer",
                  disabled && "cursor-not-allowed opacity-60"
                )}
              >
                {label}
              </label>
            )}
            {description && (
              <p className="text-xs text-muted leading-normal mt-0.5">{description}</p>
            )}
          </div>
        )}
      </div>
    );
  }
);

Checkbox.displayName = "Checkbox";
