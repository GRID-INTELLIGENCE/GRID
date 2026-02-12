import React, { forwardRef } from "react";
import { useTheme } from "../hooks/useTheme";
import { BaseComponentProps, ComponentSize } from "../types";

export interface CardProps extends BaseComponentProps {
  children: React.ReactNode;
  variant?: "default" | "elevated" | "outlined" | "filled";
  size?: ComponentSize;
  interactive?: boolean;
  onClick?: () => void;
}

export interface CardHeaderProps extends BaseComponentProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export interface CardContentProps extends BaseComponentProps {
  children: React.ReactNode;
}

export interface CardFooterProps extends BaseComponentProps {
  children: React.ReactNode;
}

const sizeStyles: Record<ComponentSize, string> = {
  xs: "p-2",
  sm: "p-3",
  md: "p-4",
  lg: "p-6",
  xl: "p-8",
};

const CardRoot = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      variant = "default",
      size = "md",
      interactive = false,
      onClick,
      className = "",
      style,
      "data-testid": testId,
      ...props
    },
    ref
  ) => {
    const theme = useTheme();

    const getVariantClasses = () => {
      const baseClasses = `
      rounded-lg transition-all duration-200
      ${sizeStyles[size]}
      ${interactive ? "cursor-pointer" : ""}
    `;

      switch (variant) {
        case "elevated":
          return `
          ${baseClasses}
          bg-[${theme.colors.surface}]
          shadow-[${theme.shadows.lg}]
          border border-[${theme.colors.border}]
          hover:shadow-[${theme.shadows.xl}]
        `;
        case "outlined":
          return `
          ${baseClasses}
          bg-transparent
          border-2 border-[${theme.colors.border}]
          hover:border-[${theme.colors.primary}]
          hover:bg-[${theme.colors.primary}]/5
        `;
        case "filled":
          return `
          ${baseClasses}
          bg-[${theme.colors.surface}]
          border border-[${theme.colors.border}]
        `;
        case "default":
        default:
          return `
          ${baseClasses}
          bg-[${theme.colors.surface}]
          border border-[${theme.colors.border}]
          ${
            interactive
              ? "hover:shadow-[${theme.shadows.md}] hover:bg-[${theme.colors.surface}]/80"
              : ""
          }
        `;
      }
    };

    const variantClasses = getVariantClasses();

    const handleClick = () => {
      if (interactive && onClick) {
        onClick();
      }
    };

    const handleKeyDown = (event: React.KeyboardEvent) => {
      if (
        interactive &&
        onClick &&
        (event.key === "Enter" || event.key === " ")
      ) {
        event.preventDefault();
        onClick();
      }
    };

    return (
      <div
        ref={ref}
        className={`${variantClasses} ${className}`}
        style={style}
        data-testid={testId}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        role={interactive ? "button" : undefined}
        tabIndex={interactive ? 0 : undefined}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardRoot.displayName = "Card";

const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  (
    {
      title,
      subtitle,
      action,
      className = "",
      style,
      "data-testid": testId,
      ...props
    },
    ref
  ) => {
    const theme = useTheme();

    return (
      <div
        ref={ref}
        className={`flex items-center justify-between pb-3 mb-3 border-b border-[${theme.colors.border}] ${className}`}
        style={style}
        data-testid={testId}
        {...props}
      >
        <div className="flex-1 min-w-0">
          <h3
            className="text-lg font-semibold truncate"
            style={{ color: theme.colors.text }}
          >
            {title}
          </h3>
          {subtitle && (
            <p
              className="text-sm mt-1 truncate"
              style={{ color: theme.colors.textSecondary }}
            >
              {subtitle}
            </p>
          )}
        </div>
        {action && <div className="flex-shrink-0 ml-3">{action}</div>}
      </div>
    );
  }
);

CardHeader.displayName = "CardHeader";

const CardContent = forwardRef<HTMLDivElement, CardContentProps>(
  (
    { children, className = "", style, "data-testid": testId, ...props },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={`flex-1 ${className}`}
        style={style}
        data-testid={testId}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardContent.displayName = "CardContent";

const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  (
    { children, className = "", style, "data-testid": testId, ...props },
    ref
  ) => {
    const theme = useTheme();

    return (
      <div
        ref={ref}
        className={`pt-3 mt-3 border-t border-[${theme.colors.border}] ${className}`}
        style={style}
        data-testid={testId}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardFooter.displayName = "CardFooter";

// Main Card component with sub-components
export const Card = Object.assign(CardRoot, {
  Header: CardHeader,
  Content: CardContent,
  Footer: CardFooter,
});

export default Card;
