import React, { ReactNode, createContext, useContext } from "react";
import { Theme } from "../types";

// Default theme configuration
export const defaultTheme: Theme = {
  colors: {
    primary: "#3b82f6", // Blue-500
    secondary: "#64748b", // Slate-500
    accent: "#8b5cf6", // Violet-500
    background: "#0f172a", // Slate-900
    surface: "#1e293b", // Slate-800
    text: "#f1f5f9", // Slate-100
    textSecondary: "#94a3b8", // Slate-400
    border: "#334155", // Slate-700
    error: "#ef4444", // Red-500
    warning: "#f59e0b", // Amber-500
    success: "#10b981", // Emerald-500
    info: "#06b6d4", // Cyan-500
  },
  spacing: {
    xs: "0.25rem", // 4px
    sm: "0.5rem", // 8px
    md: "1rem", // 16px
    lg: "1.5rem", // 24px
    xl: "2rem", // 32px
    xxl: "3rem", // 48px
  },
  typography: {
    fontFamily:
      'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontSize: {
      xs: "0.75rem", // 12px
      sm: "0.875rem", // 14px
      md: "1rem", // 16px
      lg: "1.125rem", // 18px
      xl: "1.25rem", // 20px
      xxl: "1.5rem", // 24px
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.625,
    },
  },
  borderRadius: {
    none: "0",
    sm: "0.25rem", // 4px
    md: "0.375rem", // 6px
    lg: "0.5rem", // 8px
    xl: "0.75rem", // 12px
    full: "9999px",
  },
  shadows: {
    none: "none",
    sm: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
    md: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
    lg: "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
    xl: "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
  },
  transitions: {
    fast: "150ms ease-in-out",
    normal: "200ms ease-in-out",
    slow: "300ms ease-in-out",
  },
};

// Theme context
const ThemeContext = createContext<Theme>(defaultTheme);

// Theme provider component
export interface ThemeProviderProps {
  theme?: Partial<Theme>;
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  theme: customTheme,
  children,
}) => {
  // Deep merge custom theme with default theme
  const mergedTheme = React.useMemo(() => {
    if (!customTheme) return defaultTheme;

    const mergeObjects = (target: any, source: any): any => {
      const result = { ...target };
      Object.keys(source).forEach((key) => {
        if (
          typeof source[key] === "object" &&
          source[key] !== null &&
          !Array.isArray(source[key])
        ) {
          result[key] = mergeObjects(result[key] || {}, source[key]);
        } else {
          result[key] = source[key];
        }
      });
      return result;
    };

    return mergeObjects(defaultTheme, customTheme);
  }, [customTheme]);

  return (
    <ThemeContext.Provider value={mergedTheme}>
      {children}
    </ThemeContext.Provider>
  );
};

// Hook to use theme
export const useTheme = (): Theme => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
};

// Hook to get theme values as CSS custom properties
export const useThemeCSSVariables = (): Record<string, string> => {
  const theme = useTheme();

  return React.useMemo(() => {
    const variables: Record<string, string> = {};

    // Colors
    Object.entries(theme.colors).forEach(([key, value]) => {
      variables[`--color-${key}`] = value;
    });

    // Spacing
    Object.entries(theme.spacing).forEach(([key, value]) => {
      variables[`--spacing-${key}`] = value;
    });

    // Typography
    Object.entries(theme.typography.fontSize).forEach(([key, value]) => {
      variables[`--font-size-${key}`] = value;
    });

    Object.entries(theme.typography.fontWeight).forEach(([key, value]) => {
      variables[`--font-weight-${key}`] = value.toString();
    });

    Object.entries(theme.typography.lineHeight).forEach(([key, value]) => {
      variables[`--line-height-${key}`] = value.toString();
    });

    // Border radius
    Object.entries(theme.borderRadius).forEach(([key, value]) => {
      variables[`--border-radius-${key}`] = value;
    });

    // Shadows
    Object.entries(theme.shadows).forEach(([key, value]) => {
      variables[`--shadow-${key}`] = value;
    });

    // Transitions
    Object.entries(theme.transitions).forEach(([key, value]) => {
      variables[`--transition-${key}`] = value;
    });

    return variables;
  }, [theme]);
};
