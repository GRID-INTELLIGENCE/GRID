import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ThemeSwitcher } from "@/components/ui/ThemeSwitcher";
import { UsageInsights } from "@/components/ui/UsageInsights";
import { useAnalyticsContext } from "@/context/AnalyticsContext";
import { appConfig, resolveSettingValue } from "@/schema";
import { BarChart3, Palette, Settings as SettingsIcon } from "lucide-react";

export function SettingsPage() {
  const { enabled, setEnabled } = useAnalyticsContext();

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Configure GRID frontend and backend connection
        </p>
      </div>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Palette className="h-4 w-4 text-[var(--primary)]" />
            Appearance
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-xs font-medium text-[var(--muted-foreground)]">
              Theme
            </label>
            <div className="mt-2">
              <ThemeSwitcher />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Usage Data */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <BarChart3 className="h-4 w-4 text-[var(--primary)]" />
            Usage Data
          </CardTitle>
          <p className="text-xs text-[var(--muted-foreground)]">
            All analytics are stored locally in your browser. Nothing is sent
            externally.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <label
              htmlFor="analytics-toggle"
              className="text-sm text-[var(--foreground)]"
            >
              Enable usage tracking
            </label>
            <button
              id="analytics-toggle"
              type="button"
              role="switch"
              aria-checked={enabled}
              onClick={() => setEnabled(!enabled)}
              className={`
                relative inline-flex h-6 w-11 items-center rounded-full transition-colors cursor-pointer
                focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]
                ${enabled ? "bg-[var(--primary)]" : "bg-[var(--muted)]"}
              `}
            >
              <span
                className={`
                  inline-block h-4 w-4 rounded-full bg-white transition-transform
                  ${enabled ? "translate-x-6" : "translate-x-1"}
                `}
              />
            </button>
          </div>
          {enabled && <UsageInsights />}
        </CardContent>
      </Card>

      {/* Existing config sections */}
      {appConfig.settings.sections.map((section) => (
        <Card key={section.title}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <SettingsIcon className="h-4 w-4 text-[var(--primary)]" />
              {section.title}
            </CardTitle>
            {section.description && (
              <p className="text-xs text-[var(--muted-foreground)]">
                {section.description}
              </p>
            )}
          </CardHeader>
          <CardContent className="space-y-4">
            {section.items.map((item) => (
              <div key={item.label}>
                <label className="text-xs font-medium text-[var(--muted-foreground)]">
                  {item.label}
                </label>
                <p className="text-sm mt-1">{resolveSettingValue(item)}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
