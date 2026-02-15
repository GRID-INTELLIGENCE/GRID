# Frontend Rules (React + TypeScript + Electron)

Applies to: `frontend/**`

## Standards
- React 19 with functional components and hooks only (no class components)
- TypeScript strict mode — no `any` types, explicit return types on exported functions
- TailwindCSS 4 for all styling (no inline styles, no CSS modules)
- Component variants: use `class-variance-authority` (CVA) + `clsx` + `tailwind-merge`
- Icons: `lucide-react` only
- Data fetching: `@tanstack/react-query`
- Routing: `react-router-dom` v7
- Validation: `zod` schemas

## Dev Commands
- Dev server: `npm run dev` (Vite + Electron concurrently)
- Lint: `npm run lint` (ESLint + TypeScript noEmit)
- Format: `npm run format` (Prettier)
- Test: `npm test` (Vitest)
- Storybook: `npm run storybook` (port 6006)

## Conventions
- File naming: PascalCase for components (`Button.tsx`), camelCase for utils (`useMetrics.ts`)
- Exports: named exports preferred over default exports
- No barrel files unless already established
