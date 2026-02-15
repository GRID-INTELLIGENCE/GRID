import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useChaosResilience,
  useHealth,
  useMetrics,
  useReadiness,
  useVersion,
} from "@/hooks";
import { cn } from "@/lib/utils";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Cpu,
  Gauge,
  Heart,
  Loader2,
  RefreshCw,
  Server,
  XCircle,
  Zap,
} from "lucide-react";

export function Observability() {
  const health = useHealth();
  const metrics = useMetrics();
  const readiness = useReadiness();
  const version = useVersion();
  const chaos = useChaosResilience();

  const healthData = health.data;
  const metricsData = metrics.data;
  const readinessData = readiness.data;
  const versionData = version.data;
  const chaosData = chaos.data;
  const isLoading = health.isLoading || metrics.isLoading;

  const formatUptime = (seconds?: number) => {
    if (!seconds) return "—";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Observability</h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            System health, metrics, resilience scoring, and real-time monitoring
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            health.refetch();
            metrics.refetch();
            readiness.refetch();
            chaos.refetch();
          }}
        >
          <RefreshCw
            className={cn("mr-1.5 h-3.5 w-3.5", isLoading && "animate-spin")}
          />
          Refresh
        </Button>
      </div>

      {/* Key metrics row */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="glass">
          <CardContent className="flex items-center gap-3 p-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-[var(--primary)]/10">
              <Heart className="h-5 w-5 text-[var(--primary)]" />
            </div>
            <div>
              <p className="text-xs text-[var(--muted-foreground)]">Status</p>
              <Badge
                variant={
                  healthData?.status === "healthy"
                    ? "success"
                    : health.data === null && !health.isLoading
                      ? "destructive"
                      : "warning"
                }
              >
                {healthData?.status ??
                  (health.data === null && !health.isLoading
                    ? "Offline"
                    : "Loading…")}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="glass">
          <CardContent className="flex items-center gap-3 p-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-[var(--primary)]/10">
              <Clock className="h-5 w-5 text-[var(--primary)]" />
            </div>
            <div>
              <p className="text-xs text-[var(--muted-foreground)]">Uptime</p>
              <p className="text-sm font-bold">
                {formatUptime(metricsData?.uptime)}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="glass">
          <CardContent className="flex items-center gap-3 p-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-[var(--primary)]/10">
              <Zap className="h-5 w-5 text-[var(--primary)]" />
            </div>
            <div>
              <p className="text-xs text-[var(--muted-foreground)]">
                Operations
              </p>
              <p className="text-sm font-bold">
                {metricsData?.operations ?? "—"}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="glass">
          <CardContent className="flex items-center gap-3 p-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-[var(--primary)]/10">
              <Gauge className="h-5 w-5 text-[var(--primary)]" />
            </div>
            <div>
              <p className="text-xs text-[var(--muted-foreground)]">
                Resilience
              </p>
              {chaosData?.resilience_score !== undefined ? (
                <Badge
                  variant={
                    Number(chaosData.resilience_score) >= 80
                      ? "success"
                      : Number(chaosData.resilience_score) >= 50
                        ? "warning"
                        : "destructive"
                  }
                >
                  {chaosData.resilience_score}%
                </Badge>
              ) : (
                <p className="text-sm font-bold">{"—"}</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {/* Readiness checks */}
        <Card className="glass">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Activity className="h-4 w-4 text-[var(--primary)]" />
              Readiness Probes
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1.5">
            {readinessData?.checks ? (
              Object.entries(readinessData.checks).map(([name, ok]) => (
                <div key={name} className="flex items-center gap-2 text-xs">
                  {ok ? (
                    <CheckCircle2 className="h-3.5 w-3.5 text-[var(--success)]" />
                  ) : (
                    <XCircle className="h-3.5 w-3.5 text-[var(--destructive)]" />
                  )}
                  <span className="capitalize">{name.replace(/_/g, " ")}</span>
                </div>
              ))
            ) : readiness.isLoading ? (
              <Loader2 className="mx-auto h-5 w-5 animate-spin text-[var(--muted-foreground)]" />
            ) : (
              <p className="text-xs text-[var(--muted-foreground)]">
                Readiness checks unavailable
              </p>
            )}
          </CardContent>
        </Card>

        {/* Version info */}
        <Card className="glass">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Server className="h-4 w-4 text-[var(--primary)]" />
              System Info
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1.5">
            {versionData ? (
              <>
                {versionData.name && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[var(--muted-foreground)]">App</span>
                    <span className="font-medium">{versionData.name}</span>
                  </div>
                )}
                {versionData.version && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[var(--muted-foreground)]">
                      Version
                    </span>
                    <Badge variant="outline">{versionData.version}</Badge>
                  </div>
                )}
                {versionData.environment && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[var(--muted-foreground)]">
                      Environment
                    </span>
                    <span className="font-medium">
                      {versionData.environment}
                    </span>
                  </div>
                )}
                {versionData.python_version && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[var(--muted-foreground)]">
                      Python
                    </span>
                    <span className="font-mono text-[10px]">
                      {versionData.python_version}
                    </span>
                  </div>
                )}
              </>
            ) : version.isLoading ? (
              <Loader2 className="mx-auto h-5 w-5 animate-spin text-[var(--muted-foreground)]" />
            ) : (
              <p className="text-xs text-[var(--muted-foreground)]">
                Version info unavailable
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Components list */}
      {healthData?.components && Array.isArray(healthData.components) && (
        <Card className="glass">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Cpu className="h-4 w-4 text-[var(--primary)]" />
              Components ({healthData.components.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 sm:grid-cols-2">
              {healthData.components.map((comp, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 rounded-md bg-[var(--muted)] p-2.5"
                >
                  {comp.status === "healthy" || comp.status === "ok" ? (
                    <CheckCircle2 className="h-3.5 w-3.5 text-[var(--success)] shrink-0" />
                  ) : (
                    <AlertTriangle className="h-3.5 w-3.5 text-[var(--warning)] shrink-0" />
                  )}
                  <span className="text-xs font-medium flex-1">
                    {comp.name}
                  </span>
                  <Badge variant="outline" className="text-[10px]">
                    {comp.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Alerts */}
      {healthData?.alerts &&
        Array.isArray(healthData.alerts) &&
        healthData.alerts.length > 0 && (
          <Card className="border-[var(--warning)]/30">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <AlertTriangle className="h-4 w-4 text-[var(--warning)]" />
                Active Alerts ({healthData.alerts.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {healthData.alerts.map((alert, i) => (
                <div key={i} className="flex items-start gap-2 text-xs">
                  <Badge
                    variant={
                      alert.level === "critical"
                        ? "destructive"
                        : alert.level === "warning"
                          ? "warning"
                          : "secondary"
                    }
                    className="shrink-0"
                  >
                    {alert.level}
                  </Badge>
                  <span className="text-[var(--muted-foreground)]">
                    {alert.message}
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

      {/* Chaos resilience recommendations */}
      {chaosData?.recommendations && chaosData.recommendations.length > 0 && (
        <Card className="glass">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">
              Resilience Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1">
              {chaosData.recommendations.map((rec, i) => (
                <li
                  key={i}
                  className="text-xs text-[var(--muted-foreground)] flex items-start gap-2"
                >
                  <span className="text-[var(--primary)] mt-0.5">{"•"}</span>
                  {rec}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
