import React, { forwardRef } from "react";
import { useTheme } from "../hooks/useTheme";
import { BaseComponentProps, ComponentSize, FormFieldProps } from "../types";

export interface InputProps
  extends BaseComponentProps,
    FormFieldProps,
    Omit<
      React.InputHTMLAttributes<HTMLInputElement>,
      keyof BaseComponentProps
    > {
  size?: ComponentSize;
  variant?: "default" | "filled" | "outlined";
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
  fullWidth?: boolean;
}

const sizeStyles: Record<ComponentSize, string> = {
  xs: "px-2 py-1 text-xs",
  sm: "px-3 py-1.5 text-sm",
  md: "px-3 py-2 text-base",
  lg: "px-4 py-2 text-base",
  xl: "px-4 py-3 text-lg",
};

const heightStyles: Record<ComponentSize, string> = {
  xs: "h-6",
  sm: "h-8",
  md: "h-10",
  lg: "h-12",
  xl: "h-14",
};

const iconSizeStyles: Record<ComponentSize, string> = {
  xs: "w-3 h-3",
  sm: "w-4 h-4",
  md: "w-5 h-5",
  lg: "w-6 h-6",
  xl: "w-7 h-7",
};

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      helperText,
      error,
      success,
      required = false,
      size = "md",
      variant = "outlined",
      startIcon,
      endIcon,
      fullWidth = false,
      disabled = false,
      id: providedId,
      className = "",
      style,
      "data-testid": testId,
      ...props
    },
    ref
  ) => {
    const theme = useTheme();

    // Generate unique ID if not provided
    const inputId = providedId || React.useId();
    const helperId = `${inputId}-helper`;
    const errorId = `${inputId}-error`;
    const successId = `${inputId}-success`;

    const hasError = !!error;
    const hasSuccess = !!success && !hasError;
    const hasHelper = !!helperText;

    const containerClasses = `
    ${fullWidth ? "w-full" : ""}
  `;

    const getVariantClasses = () => {
      const baseClasses = `
      w-full
      bg-transparent
      text-[${theme.colors.text}]
      placeholder:text-[${theme.colors.textSecondary}]
      focus:outline-none focus:ring-2 focus:ring-offset-2
      transition-all duration-200
      disabled:opacity-50 disabled:cursor-not-allowed
      ${sizeStyles[size]}
      ${heightStyles[size]}
    `;

      switch (variant) {
        case "filled":
          return `
          ${baseClasses}
          bg-[${theme.colors.surface}]
          border-b-2
          ${
            hasError
              ? `border-[${theme.colors.error}] focus:border-[${theme.colors.error}] focus:ring-[${theme.colors.error}]`
              : hasSuccess
              ? `border-[${theme.colors.success}] focus:border-[${theme.colors.success}] focus:ring-[${theme.colors.success}]`
              : `border-[${theme.colors.border}] focus:border-[${theme.colors.primary}] focus:ring-[${theme.colors.primary}]`
          }
          rounded-t-md
        `;
        case "outlined":
        default:
          return `
          ${baseClasses}
          border-2 rounded-md
          ${
            hasError
              ? `border-[${theme.colors.error}] focus:border-[${theme.colors.error}] focus:ring-[${theme.colors.error}]`
              : hasSuccess
              ? `border-[${theme.colors.success}] focus:border-[${theme.colors.success}] focus:ring-[${theme.colors.success}]`
              : `border-[${theme.colors.border}] focus:border-[${theme.colors.primary}] focus:ring-[${theme.colors.primary}]`
          }
        `;
      }
    };

    const variantClasses = getVariantClasses();

    const getFocusRingColor = () => {
      if (hasError) return theme.colors.error;
      if (hasSuccess) return theme.colors.success;
      return theme.colors.primary;
    };

    const focusRingColor = getFocusRingColor();

    const renderLabel = () => {
      if (!label) return null;

      return (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium mb-1.5"
          style={{ color: theme.colors.text }}
        >
          {label}
          {required && (
            <span
              className="ml-1"
              style={{ color: theme.colors.error }}
              aria-label="required"
            >
              *
            </span>
          )}
        </label>
      );
    };

    const renderHelperText = () => {
      if (!hasHelper) return null;

      return (
        <p
          id={helperId}
          className="mt-1 text-sm"
          style={{ color: theme.colors.textSecondary }}
        >
          {helperText}
        </p>
      );
    };

    const renderError = () => {
      if (!hasError) return null;

      return (
        <p
          id={errorId}
          className="mt-1 text-sm"
          style={{ color: theme.colors.error }}
          role="alert"
          aria-live="polite"
        >
          {error}
        </p>
      );
    };

    const renderSuccess = () => {
      if (!hasSuccess) return null;

      return (
        <p
          id={successId}
          className="mt-1 text-sm"
          style={{ color: theme.colors.success }}
          role="status"
          aria-live="polite"
        >
          {success}
        </p>
      );
    };

    const renderIcon = (icon: React.ReactNode, position: "start" | "end") => {
      if (!icon) return null;

      const isStart = position === "start";

      return (
        <div
          className={`
          absolute inset-y-0 flex items-center pointer-events-none
          ${isStart ? "left-0 pl-3" : "right-0 pr-3"}
        `}
        >
          <span
            className={iconSizeStyles[size]}
            style={{ color: theme.colors.textSecondary }}
          >
            {icon}
          </span>
        </div>
      );
    };

    const inputPaddingLeft = startIcon ? "pl-10" : "";
    const inputPaddingRight = endIcon ? "pr-10" : "";

    return (
      <div className={containerClasses}>
        {renderLabel()}

        <div className="relative">
          {renderIcon(startIcon, "start")}

          <input
            ref={ref}
            id={inputId}
            disabled={disabled}
            className={`
            ${variantClasses}
            ${inputPaddingLeft}
            ${inputPaddingRight}
            ${className}
          `}
            style={
              {
                "--focus-ring-color": focusRingColor,
                ...style,
              } as React.CSSProperties
            }
            data-testid={testId}
            aria-describedby={
              [
                hasHelper ? helperId : "",
                hasError ? errorId : "",
                hasSuccess ? successId : "",
              ]
                .filter(Boolean)
                .join(" ") || undefined
            }
            aria-invalid={hasError}
            aria-required={required}
            {...props}
          />

          {renderIcon(endIcon, "end")}
        </div>

        {renderError()}
        {renderSuccess()}
        {renderHelperText()}
      </div>
    );
  }
);

Input.displayName = "Input";

export default Input;
