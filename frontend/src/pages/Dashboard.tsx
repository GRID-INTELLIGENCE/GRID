import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useHealth } from "@/hooks";
import { appConfig, getRoute, iconRegistry } from "@/schema";
import type { BadgeVariant } from "@/schema/app-schema";

function StatCard({
  icon: Icon,
  label,
  value,
  variant = "default",
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  variant?: BadgeVariant;
}) {
  return (
    <Card className="group hover:glow-primary transition-shadow">
      <CardContent className="flex items-center gap-4 p-5">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--accent)]">
          <Icon className="h-5 w-5 text-[var(--primary)]" />
        </div>
        <div className="min-w-0">
          <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wide">
            {label}
          </p>
          <p className="text-lg font-semibold truncate">{value}</p>
        </div>
        {variant !== "default" && (
          <Badge variant={variant} className="ml-auto">
            {variant === "success" ? "Active" : "Degraded"}
          </Badge>
        )}
      </CardContent>
    </Card>
  );
}

export function Dashboard() {
  const health = useHealth({ refetchInterval: 10_000 });

  const isOnline = health.isOnline;

  const dashboardRoute = getRoute("dashboard");

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {dashboardRoute.title}
          </h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            {dashboardRoute.description}
          </p>
        </div>
        <Badge variant={isOnline ? "success" : "warning"}>
          {isOnline ? "System Online" : "Connecting…"}
        </Badge>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {appConfig.dashboard.stats.map((stat) => {
          const Icon = iconRegistry[stat.icon];
          const value =
            stat.source === "health"
              ? isOnline
                ? (stat.health?.ok ?? "Operational")
                : (stat.health?.fail ?? "Offline")
              : (stat.value ?? "—");
          const variant =
            stat.source === "health"
              ? isOnline
                ? (stat.health?.okVariant ?? "success")
                : (stat.health?.failVariant ?? "warning")
              : "default";
          return (
            <StatCard
              key={stat.id}
              icon={Icon}
              label={stat.label}
              value={value}
              variant={variant}
            />
          );
        })}
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {appConfig.dashboard.quickActions.map((action) => {
          const Icon = iconRegistry[action.icon];
          return (
            <Card key={action.id} className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Icon className="h-4 w-4 text-[var(--primary)]" />
                  {action.title}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-[var(--muted-foreground)]">
                  {action.description}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
