import { Moon, Sun, Sprout } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";
import type { ThemeName } from "@/tokens";

const themes: { value: ThemeName; label: string; icon: React.ReactNode }[] = [
  { value: "dark", label: "Dark", icon: <Moon className="h-4 w-4" /> },
  { value: "light", label: "Light", icon: <Sun className="h-4 w-4" /> },
  {
    value: "mycelium",
    label: "Mycelium",
    icon: <Sprout className="h-4 w-4" />,
  },
];

export function ThemeSwitcher(): React.JSX.Element {
  const { theme, setTheme } = useTheme();

  return (
    <div
      className="inline-flex items-center gap-1 rounded-lg border border-[var(--border)] bg-[var(--secondary)] p-1"
      role="radiogroup"
      aria-label="Theme"
    >
      {themes.map(({ value, label, icon }) => {
        const active = theme === value;
        return (
          <button
            key={value}
            type="button"
            role="radio"
            aria-checked={active}
            aria-label={label}
            onClick={() => setTheme(value)}
            className={`
              inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium
              transition-all duration-150
              ${
                active
                  ? "bg-[var(--primary)] text-[var(--primary-foreground)] shadow-sm"
                  : "text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--muted)]"
              }
            `}
          >
            {icon}
            <span>{label}</span>
          </button>
        );
      })}
    </div>
  );
}
