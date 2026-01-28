import React from "react";
import { LucideIcon, AlertCircle } from "lucide-react";

interface FormFieldProps {
  label: string;
  error?: string;
  icon?: LucideIcon;
  children: React.ReactNode;
}

/**
 * Reusable form field component with consistent styling.
 *
 * Provides:
 * - Label with uppercase styling
 * - Optional icon
 * - Error message display
 * - Proper spacing and layout
 *
 * Usage:
 * <FormField label="Email" error={errors.email?.message} icon={Mail}>
 *   <input {...register("email")} />
 * </FormField>
 */
export function FormField({
  label,
  error,
  icon: Icon,
  children,
}: FormFieldProps) {
  return (
    <div className="space-y-2">
      <label className="text-xs font-bold text-zinc-500 uppercase tracking-widest pl-1">
        {label}
      </label>
      <div className="relative group">
        {Icon && (
          <Icon className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 group-focus-within:text-[#ff4655] transition-colors" />
        )}
        {children}
      </div>
      {error && (
        <p className="text-red-500 text-xs pl-1 font-medium flex items-center gap-1">
          <AlertCircle className="w-3 h-3" />
          {error}
        </p>
      )}
    </div>
  );
}
