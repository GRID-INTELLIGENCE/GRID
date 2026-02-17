# Hogwarts Visualizer

A React + TypeScript visualization application for the GRID Path Optimization Agent system. Features a Hogwarts house-themed UI that displays navigation plans and AI insights in an interactive, cinematic interface.

## Features

- 🏰 **House-Themed UI**: Switch between Gryffindor, Slytherin, Hufflepuff, and Ravenclaw themes
- 🧭 **Navigation Planning**: Generate intelligent navigation plans for your goals
- 📊 **Data Visualization**: Interactive charts using Recharts (Bar charts, Radar charts)
- 🎨 **Responsive Design**: Works on mobile, tablet, and desktop
- 🔄 **Mock/Real API**: Toggle between mock data (offline) and real backend API
- ⚡ **Fast Development**: Built with Vite for lightning-fast HMR

## Prerequisites

- **Node.js** 18+ and npm (or yarn/pnpm)
- **Backend API** running on `http://localhost:8080` (optional, can use mock data)

## Getting Started

### 1. Install Dependencies

```bash
cd hogwarts-visualizer
npm install
```

### 2. Configure Environment

Create a `.env` file in the project root (optional):

```env
VITE_API_BASE_URL=http://localhost:8080
```

If not configured, defaults to `http://localhost:8080/api/v1`.

### 3. Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`.

### 4. Build for Production

```bash
npm run build
```

Production files will be in the `dist/` directory.

## Project Structure

```
hogwarts-visualizer/
├── src/
│   ├── assets/              # Static assets (house logos, images)
│   ├── components/
│   │   ├── common/          # Reusable UI components
│   │   ├── charts/          # Chart components (Recharts)
│   │   └── layout/          # Layout components
│   ├── contexts/            # React Context providers
│   ├── services/
│   │   ├── api/             # API client and services
│   │   └── mock/            # Mock data for offline development
│   ├── styles/              # Global styles and Tailwind config
│   ├── types/               # TypeScript type definitions
│   └── views/               # Main view components
├── public/                  # Static public files
└── package.json
```

## Usage

### Generate Navigation Plan

1. Navigate to **Navigation Plans** from the sidebar
2. Enter your goal (e.g., "Optimize user onboarding flow")
3. Optionally toggle **Use mock data** for offline development
4. Click **Generate Navigation Plan**
5. View the plan with charts, confidence metrics, and alternative paths

### Switch Houses

1. Click the house selector in the header
2. Choose from: Gryffindor, Slytherin, Hufflepuff, or Ravenclaw
3. The entire UI theme will update to match the selected house colors

### View Settings

1. Navigate to **Settings** from the sidebar
2. Configure API URL, theme preferences, and house selection

## House Themes

### Gryffindor
- Primary: Red (#ae0001)
- Secondary: Gold (#d3a625)
- Traits: Bravery, courage, chivalry

### Slytherin
- Primary: Green (#2a623d)
- Secondary: Silver (#5d5d5d)
- Traits: Ambition, cunning, resourcefulness

### Hufflepuff
- Primary: Yellow (#ecb939)
- Secondary: Black (#000000)
- Traits: Loyalty, patience, hard work

### Ravenclaw
- Primary: Blue (#0e4a99)
- Secondary: Bronze (#946b2d)
- Traits: Intelligence, wisdom, creativity

## API Integration

The app integrates with the GRID FastAPI backend:

- **Endpoint**: `POST /api/v1/navigation/plan`
- **Request**: Navigation goal and optional context
- **Response**: Navigation plan with paths, steps, and confidence scores

See `src/services/api/navigation.ts` for API implementation details.

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run test` - Run tests (when implemented)
- `npm run lint` - Lint code (when configured)

### Mock Mode

Enable mock mode in the Navigation Plan view to develop offline without a backend. Mock data is provided in `src/services/mock/mockNavigation.ts`.

## Technologies Used

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TailwindCSS** - Utility-first CSS framework
- **Recharts** - Chart library
- **Axios** - HTTP client
- **React Router** - Client-side routing (if needed)

## Future Enhancements (Phase 4)

- User authentication with JWT tokens
- Real-time updates via WebSockets
- Save/load favorite navigation plans
- Export visualizations as images/PDFs
- Advanced filtering and search
- Real AI provider integration

## License

Part of the GRID project.

## Contributing

This is part of the GRID project. Follow the project's contribution guidelines.
