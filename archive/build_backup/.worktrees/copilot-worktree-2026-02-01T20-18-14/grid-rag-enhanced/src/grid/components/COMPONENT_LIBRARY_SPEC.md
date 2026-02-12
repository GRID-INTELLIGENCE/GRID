# GRID Unified Component Library

## Overview

A comprehensive, themeable component library for GRID applications with:

- **TypeScript-first** design with full type safety
- **Theme-aware** components that adapt to different contexts
- **Accessibility-first** with ARIA support and keyboard navigation
- **Design system** with consistent spacing, colors, and typography
- **Performance optimized** with proper memoization and lazy loading

## Architecture

### Theme System

```typescript
interface Theme {
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    warning: string;
    success: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  typography: {
    fontFamily: string;
    fontSize: Record<"xs" | "sm" | "md" | "lg" | "xl", string>;
    fontWeight: Record<"normal" | "medium" | "semibold" | "bold", number>;
  };
  borderRadius: Record<"none" | "sm" | "md" | "lg" | "full", string>;
  shadows: Record<"none" | "sm" | "md" | "lg" | "xl", string>;
}
```

### Component Categories

#### Form Components

- **Button** - Primary actions, secondary actions, danger states
- **Input** - Text input, password, email, search
- **Textarea** - Multi-line text input
- **Select** - Dropdown selection
- **Checkbox** - Boolean selection
- **Radio** - Single selection from options
- **Switch** - Toggle between two states

#### Layout Components

- **Card** - Content containers with headers, body, footer
- **Modal** - Overlay dialogs
- **Drawer** - Slide-out panels
- **Tabs** - Tabbed content organization
- **Accordion** - Collapsible content sections

#### Data Display Components

- **Table** - Data grid with sorting, filtering, pagination
- **List** - Vertical list of items
- **Badge** - Status indicators and labels
- **Avatar** - User/profile images
- **Tooltip** - Contextual help
- **Popover** - Floating content containers

#### Feedback Components

- **Alert** - Status messages (success, error, warning, info)
- **Spinner** - Loading indicators
- **Progress** - Progress bars and indicators
- **Skeleton** - Loading placeholders
- **Toast** - Temporary notifications

#### Navigation Components

- **Breadcrumb** - Navigation path display
- **Pagination** - Page navigation
- **Menu** - Dropdown menus and context menus

## Component Specifications

### Button Component

```typescript
interface ButtonProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "size"> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  fullWidth?: boolean;
}

const Button: React.FC<ButtonProps> = ({ variant = "primary", size = "md", loading = false, disabled = false, children, ...props }) => {
  /* implementation */
};
```

**Variants:**

- `primary` - Main call-to-action, highest emphasis
- `secondary` - Alternative actions, medium emphasis
- `outline` - Subtle actions, low emphasis
- `ghost` - Minimal styling, often for toolbars
- `danger` - Destructive actions

**Sizes:**

- `xs` (24px height) - Compact buttons
- `sm` (32px height) - Small buttons
- `md` (40px height) - Default size
- `lg` (48px height) - Large buttons
- `xl` (56px height) - Extra large buttons

### Input Component

```typescript
interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "size"> {
  label?: string;
  helperText?: string;
  error?: string;
  success?: string;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "filled" | "outlined";
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
  fullWidth?: boolean;
}

const Input: React.FC<InputProps> = ({ label, helperText, error, success, size = "md", variant = "outlined", ...props }) => {
  /* implementation */
};
```

### Card Component

```typescript
interface CardProps {
  children: React.ReactNode;
  variant?: "default" | "elevated" | "outlined" | "filled";
  size?: "sm" | "md" | "lg";
  interactive?: boolean;
  onClick?: () => void;
  className?: string;
}

interface CardHeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}

interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

const Card: React.FC<CardProps> & {
  Header: React.FC<CardHeaderProps>;
  Content: React.FC<CardContentProps>;
  Footer: React.FC<CardFooterProps>;
} = ({ children, ...props }) => {
  /* implementation */
};
```

### Table Component

```typescript
interface Column<T = any> {
  key: keyof T | string;
  title: string;
  width?: string | number;
  sortable?: boolean;
  filterable?: boolean;
  render?: (value: any, record: T, index: number) => React.ReactNode;
}

interface TableProps<T = any> {
  data: T[];
  columns: Column<T>[];
  loading?: boolean;
  pagination?: {
    current: number;
    total: number;
    pageSize: number;
    onChange: (page: number, pageSize: number) => void;
  };
  onSort?: (key: string, order: "asc" | "desc") => void;
  onFilter?: (filters: Record<string, any>) => void;
  rowKey?: keyof T | ((record: T) => string);
  size?: "sm" | "md" | "lg";
}

const Table: React.FC<TableProps> = ({ data, columns, loading = false, ...props }) => {
  /* implementation */
};
```

## Implementation Guidelines

### Styling Approach

- **Tailwind CSS** for utility classes
- **CSS custom properties** for theme variables
- **Inline styles** only for dynamic theme values
- **Consistent spacing** using theme spacing scale
- **Responsive design** with mobile-first approach

### Accessibility

- **ARIA attributes** for screen readers
- **Keyboard navigation** support
- **Focus management** with visible focus indicators
- **Color contrast** meeting WCAG AA standards
- **Semantic HTML** structure

### Performance

- **React.memo** for expensive components
- **useMemo/useCallback** for computed values
- **Lazy loading** for heavy components
- **Bundle splitting** for large component libraries

### Testing

- **Unit tests** for component logic
- **Integration tests** for user interactions
- **Visual regression tests** for UI consistency
- **Accessibility tests** with axe-core

## Migration Guide

### From Existing Components

#### WizardButton → Button

```typescript
// Before
<WizardButton variant="primary" size="md">Click me</WizardButton>

// After
<Button variant="primary" size="md">Click me</Button>
```

#### HouseThemedCard → Card

```typescript
// Before
<HouseThemedCard onClick={handleClick}>
  <h3>Card Title</h3>
  <p>Card content</p>
</HouseThemedCard>

// After
<Card variant="elevated" interactive onClick={handleClick}>
  <Card.Header title="Card Title" />
  <Card.Content>
    <p>Card content</p>
  </Card.Content>
</Card>
```

#### SpellboundInput → Input

```typescript
// Before
<SpellboundInput label="Name" error={errors.name} />

// After
<Input label="Name" error={errors.name} />
```

## Development Setup

### Storybook

```bash
npm install -D @storybook/react @storybook/addon-essentials
npx storybook init
```

### Testing

```bash
npm install -D @testing-library/react @testing-library/jest-dom
```

### Build

```bash
npm run build
npm run storybook
```
