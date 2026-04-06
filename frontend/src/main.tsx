import { QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { AnalyticsProvider } from "./context/AnalyticsContext";
import { ThemeProvider } from "./context/ThemeContext";
import "./index.css";
import { installBrowserShim } from "./lib/browser-shim";
import {
  createPersistedQueryClient,
  initializeStatePersistence,
} from "./lib/state-persistence";

// Install browser-mode shim FIRST (no-op in Electron)
installBrowserShim();

// Initialize state persistence on app startup
initializeStatePersistence();

// Create persisted QueryClient for state restoration
const queryClient = createPersistedQueryClient();

const rootEl = document.getElementById("root");
if (!rootEl) throw new Error("Missing #root element");
ReactDOM.createRoot(rootEl).render(
  <React.StrictMode>
    <ThemeProvider>
      <AnalyticsProvider>
        <QueryClientProvider client={queryClient}>
          <App />
        </QueryClientProvider>
      </AnalyticsProvider>
    </ThemeProvider>
  </React.StrictMode>
);
