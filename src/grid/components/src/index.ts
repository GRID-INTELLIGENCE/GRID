// Main exports for GRID Component Library

// Components
import Button from "./components/Button";
import Card from "./components/Card";
import Input from "./components/Input";
import Table from "./components/Table";

export { Button, Card, Input, Table };

// Theme system
export { defaultTheme } from "./hooks/useTheme";

// Types
export type {
  BaseComponentProps,
  ComponentSize,
  ComponentStatus,
  ComponentVariant,
  DistributiveOmit,
  FormFieldProps,
  InteractiveProps,
  Theme,
} from "./types";

// Component-specific types
export type { ButtonProps } from "./components/Button";
export type {
  CardContentProps,
  CardFooterProps,
  CardHeaderProps,
  CardProps,
} from "./components/Card";
export type { InputProps } from "./components/Input";
export type {
  Column,
  FilterConfig,
  PaginationConfig,
  SortConfig,
  TableProps,
} from "./components/Table";

// Re-export React for convenience
export { default as React } from "react";

// Library version and metadata
export const GRID_COMPONENTS_VERSION = "1.0.0";
export const GRID_COMPONENTS_AUTHOR = "GRID Team";

// Utility functions
export const createTheme = (
  customTheme: Partial<import("./types").Theme>
): import("./types").Theme => {
  return { ...defaultTheme, ...customTheme };
};

// Default export for easy importing
const GRIDComponents = {
  Button,
  Input,
  Card,
  Table,
  defaultTheme,
  createTheme,
  version: GRID_COMPONENTS_VERSION,
};

export default GRIDComponents;
