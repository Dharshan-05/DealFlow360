import React, { createContext, useContext, useId } from "react";
import { cn } from "@/lib/utils";

interface FormItemContextValue {
  id: string;
  errorId?: string;
  descriptionId?: string;
  isInvalid: boolean;
}

const FormItemContext = createContext<FormItemContextValue | null>(null);

export function useFormItem() {
  const context = useContext(FormItemContext);
  if (!context) {
    throw new Error("useFormItem should be used within <FormItem>");
  }
  return context;
}

export interface FormItemProps extends React.HTMLAttributes<HTMLDivElement> {
  error?: string;
  description?: string;
}

export function FormItem({
  className,
  error,
  description,
  children,
  ...props
}: FormItemProps) {
  const id = useId();
  const errorId = error ? `${id}-error` : undefined;
  const descriptionId = description ? `${id}-description` : undefined;

  return (
    <FormItemContext.Provider
      value={{ id, errorId, descriptionId, isInvalid: Boolean(error) }}
    >
      <div className={cn("space-y-1.5", className)} {...props}>
        {children}
        {description && (
          <p id={descriptionId} className="text-xs text-muted leading-normal">
            {description}
          </p>
        )}
        {error && (
          <p id={errorId} role="alert" className="text-xs font-medium text-rose-600 leading-normal">
            {error}
          </p>
        )}
      </div>
    </FormItemContext.Provider>
  );
}

export interface FormLabelProps
  extends React.LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean;
}

export function FormLabel({
  className,
  required,
  children,
  ...props
}: FormLabelProps) {
  const { id } = useFormItem();

  return (
    <label
      htmlFor={id}
      className={cn(
        "block text-xs font-semibold uppercase tracking-wider text-slate-700",
        className
      )}
      {...props}
    >
      {children}
      {required && <span className="ml-1 text-rose-500" aria-hidden="true">*</span>}
    </label>
  );
}

export function FormControl({
  children,
}: {
  children: React.ReactElement;
}) {
  const { id, errorId, descriptionId, isInvalid } = useFormItem();

  const describedBy = [errorId, descriptionId].filter(Boolean).join(" ") || undefined;

  return React.cloneElement(children, {
    id,
    "aria-invalid": isInvalid ? "true" : undefined,
    "aria-describedby": describedBy,
    error: isInvalid,
  });
}
