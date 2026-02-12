import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { appConfig, resolveSettingValue } from "@/schema";
import { Settings as SettingsIcon } from "lucide-react";

export function SettingsPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Configure GRID frontend and backend connection
        </p>
      </div>
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
