# GRID Curated Examples

This directory contains curated examples extracted from GRID research and development work.

## Components

### React Components

Located in `../lib/extracted/components/react/hogwarts-theme/`

#### WizardButton

A themed button component with house colors and multiple variants.

- **Features**: Primary/secondary/outline variants, sizes, loading states, icons
- **Dependencies**: React, house theme context
- **Use case**: Themed UI buttons in GRID applications

#### HouseThemedCard

A card component with house-themed borders and backgrounds.

- **Features**: Interactive states, accessibility support, theme integration
- **Dependencies**: React, house theme context
- **Use case**: Content containers with consistent theming

#### SpellboundInput

An input component with house theming and validation states.

- **Features**: Labels, error states, helper text, icon support
- **Dependencies**: React, house theme context
- **Use case**: Form inputs with consistent styling

#### LoadingSpinner

An animated loading spinner component.

- **Features**: Smooth animations, theme integration
- **Dependencies**: React
- **Use case**: Loading states and async operations

#### ErrorBoundary

A React error boundary for graceful error handling.

- **Features**: Error catching, fallback UI, error reporting
- **Dependencies**: React
- **Use case**: Error handling in React applications

## Visualizations

### Chart Components

Located in `../lib/extracted/visualizations/charts/`

#### ConfidenceRadar

A radar chart for displaying confidence scores.

- **Features**: Multi-dimensional data visualization
- **Dependencies**: React, charting library

#### HousePointsChart

A chart for displaying house points over time.

- **Features**: Time-series visualization, house theming
- **Dependencies**: React, charting library

#### NavigationPathChart

A chart for visualizing navigation paths.

- **Features**: Path visualization, interactive elements
- **Dependencies**: React, charting library

### Interactive Visualizations

Located in `../lib/extracted/visualizations/visualizations/interactive/`

#### D3 Circle Visualization

Interactive circle-based data visualization using D3.js.

- **Features**: Interactive elements, data binding
- **Dependencies**: D3.js, HTML/CSS

#### Plotly Circle

Interactive circle visualization using Plotly.

- **Features**: Web-based interactivity, multiple data formats
- **Dependencies**: Plotly.js

#### Rowling Tribute

Interactive visualization honoring J.K. Rowling's work.

- **Features**: Thematic elements, interactive storytelling
- **Dependencies**: HTML/CSS/JavaScript

## Configuration Templates

Located in `../lib/extracted/config-templates/`

### Build Tools

- **Vite config**: Modern build tool configuration
- **Vitest config**: Testing framework configuration
- **Tailwind config**: CSS framework configuration
- **PostCSS config**: CSS processing configuration

## Usage Examples

### Using React Components

```typescript
import { WizardButton, HouseThemedCard, SpellboundInput } from '../lib/extracted/components/react/hogwarts-theme';

// In your component
<HouseThemedCard>
  <h3>Welcome to Hogwarts</h3>
  <SpellboundInput label="Student Name" />
  <WizardButton variant="primary">Enroll</WizardButton>
</HouseThemedCard>
```

### Using Visualizations

```typescript
import ConfidenceRadar from '../lib/extracted/visualizations/charts/ConfidenceRadar';

// In your dashboard
<ConfidenceRadar data={confidenceData} />
```

## Integration Guide

### 1. Copy Components

Copy the desired components from `../lib/extracted/` to your project.

### 2. Install Dependencies

```bash
npm install react typescript @types/react
# Plus any specific dependencies for visualizations
```

### 3. Set Up Theme Context

For themed components, you'll need to provide a theme context:

```typescript
const theme = {
  colors: {
    primary: "#3b82f6",
    secondary: "#64748b",
    // ... other colors
  },
  // ... other theme properties
};
```

### 4. Import and Use

```typescript
import { WizardButton } from "./path/to/extracted/components";
```

## Contributing

To add new curated examples:

1. Extract components using `tools/extract_components.py`
2. Add documentation to this README
3. Test the examples in a sample application
4. Update the usage examples

## Categories

- **UI Components**: Reusable interface elements
- **Visualizations**: Data visualization components
- **Utilities**: Helper functions and utilities
- **Configurations**: Build and development configurations
- **Educational**: Tutorial and example code
