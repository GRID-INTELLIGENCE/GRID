import React, { forwardRef } from "react";
import { useTheme } from "../hooks/useTheme";
import {
  BaseComponentProps,
  ComponentSize,
  ComponentVariant,
  InteractiveProps,
} from "../types";

export interface ButtonProps extends BaseComponentProps, InteractiveProps {
  children: React.ReactNode;
  variant?: ComponentVariant;
  size?: ComponentSize;
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  fullWidth?: boolean;
  type?: "button" | "submit" | "reset";
}

const sizeStyles: Record<ComponentSize, string> = {
  xs: "px-2.5 py-1.5 text-xs",
  sm: "px-3 py-2 text-sm",
  md: "px-4 py-2 text-base",
  lg: "px-4 py-2 text-lg",
  xl: "px-6 py-3 text-xl",
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

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = "primary",
      size = "md",
      loading = false,
      disabled = false,
      icon,
      iconPosition = "left",
      fullWidth = false,
      type = "button",
      className = "",
      style,
      "data-testid": testId,
      onClick,
      onMouseEnter,
      onMouseLeave,
      onFocus,
      onBlur,
      ...props
    },
    ref
  ) => {
    const theme = useTheme();

    const isDisabled = disabled || loading;

    const baseClasses = `
    inline-flex items-center justify-center
    font-medium rounded-md
    transition-all duration-200
    focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed
    ${fullWidth ? "w-full" : ""}
    ${sizeStyles[size]}
    ${heightStyles[size]}
    ${className}
  `;

    const getVariantClasses = () => {
      switch (variant) {
        case "primary":
          return `
          bg-[${theme.colors.primary}]
          hover:bg-[${theme.colors.primary}]/90
          text-white
          focus:ring-[${theme.colors.primary}]
          border border-transparent
        `;
        case "secondary":
          return `
          bg-[${theme.colors.secondary}]
          hover:bg-[${theme.colors.secondary}]/90
          text-white
          focus:ring-[${theme.colors.secondary}]
          border border-transparent
        `;
        case "outline":
          return `
          border-2 border-[${theme.colors.border}]
          bg-transparent
          hover:bg-[${theme.colors.primary}]/10
          text-[${theme.colors.text}]
          focus:ring-[${theme.colors.primary}]
        `;
        case "ghost":
          return `
          bg-transparent
          hover:bg-[${theme.colors.surface}]
          text-[${theme.colors.text}]
          focus:ring-[${theme.colors.primary}]
          border border-transparent
        `;
        case "danger":
          return `
          bg-[${theme.colors.error}]
          hover:bg-[${theme.colors.error}]/90
          text-white
          focus:ring-[${theme.colors.error}]
          border border-transparent
        `;
        case "success":
          return `
          bg-[${theme.colors.success}]
          hover:bg-[${theme.colors.success}]/90
          text-white
          focus:ring-[${theme.colors.success}]
          border border-transparent
        `;
        case "warning":
          return `
          bg-[${theme.colors.warning}]
          hover:bg-[${theme.colors.warning}]/90
          text-black
          focus:ring-[${theme.colors.warning}]
          border border-transparent
        `;
        default:
          return "";
      }
    };

    const variantClasses = getVariantClasses();

    const getFocusRingColor = () => {
      switch (variant) {
        case "primary":
          return theme.colors.primary;
        case "secondary":
          return theme.colors.secondary;
        case "danger":
          return theme.colors.error;
        case "success":
          return theme.colors.success;
        case "warning":
          return theme.colors.warning;
        default:
          return theme.colors.primary;
      }
    };

    const focusRingColor = getFocusRingColor();

    const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
      if (isDisabled) return;
      onClick?.(event);
    };

    const renderIcon = () => {
      if (!icon) return null;

      return (
        <span
          className={`
          ${iconSizeStyles[size]}
          ${iconPosition === "left" ? "mr-2" : "ml-2"}
          ${loading ? "animate-spin" : ""}
        `}
          style={{ color: "currentColor" }}
        >
          {icon}
        </span>
      );
    };

    const renderContent = () => {
      if (loading) {
        return (
          <>
            <svg
              className={`animate-spin ${iconSizeStyles[size]} mr-2`}
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Loading...
          </>
        );
      }

      return (
        <>
          {iconPosition === "left" && renderIcon()}
          {children}
          {iconPosition === "right" && renderIcon()}
        </>
      );
    };

    return (
      <button
        ref={ref}
        type={type}
        disabled={isDisabled}
        className={`${baseClasses} ${variantClasses}`}
        style={
          {
            // Dynamic theme colors that can't be done with Tailwind
            "--focus-ring-color": focusRingColor,
            ...style,
          } as React.CSSProperties
        }
        data-testid={testId}
        onClick={handleClick}
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
        onFocus={onFocus}
        onBlur={onBlur}
        {...props}
      >
        {renderContent()}
      </button>
    );
  }
);

Button.displayName = "Button";

export default Button;
