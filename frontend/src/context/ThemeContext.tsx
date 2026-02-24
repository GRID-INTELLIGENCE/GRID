import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import type { ThemeName } from "@/tokens";

const STORAGE_KEY = "grid-theme";
const VALID_THEMES: ThemeName[] = ["dark", "light", "mycelium"];
const DEFAULT_THEME: ThemeName = "dark";

interface ThemeContextValue {
  theme: ThemeName;
  setTheme: (theme: ThemeName) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function getStoredTheme(): ThemeName {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && VALID_THEMES.includes(stored as ThemeName)) {
      return stored as ThemeName;
    }
  } catch {
    // localStorage unavailable
  }
  return DEFAULT_THEME;
}

function applyThemeClass(theme: ThemeName): void {
  const root = document.documentElement;
  for (const t of VALID_THEMES) {
    root.classList.remove(t);
  }
  root.classList.add(theme);
}

export function ThemeProvider({
  children,
}: {
  children: React.ReactNode;
}): React.JSX.Element {
  const [theme, setThemeState] = useState<ThemeName>(getStoredTheme);

  const setTheme = useCallback((next: ThemeName) => {
    setThemeState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // localStorage unavailable
    }
    applyThemeClass(next);
  }, []);

  useEffect(() => {
    applyThemeClass(theme);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return ctx;
}
