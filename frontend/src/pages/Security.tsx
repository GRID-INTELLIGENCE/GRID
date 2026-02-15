import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useCorruptionStats,
  useDrtOverview,
  useSecurityHealth,
  useSecurityStatus,
} from "@/hooks";
import { cn } from "@/lib/utils";
import {
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Lock,
  RefreshCw,
  Shield,
  ShieldAlert,
  ShieldCheck,
  XCircle,
} from "lucide-react";

export function Security() {
  const secStatus = useSecurityStatus();
  const secHealth = useSecurityHealth();
  const corruption = useCorruptionStats();
  const drt = useDrtOverview();

  const statusData = secStatus.data;
  const healthData = secHealth.data;
  const corruptionData = corruption.data;
  const drtData = drt.data;

  const isLoading = secStatus.isLoading || secHealth.isLoading;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Security</h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            Security posture, compliance checks, corruption monitoring, and DRT
            analysis
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            secStatus.refetch();
            secHealth.refetch();
            corruption.refetch();
            drt.refetch();
          }}
        >
          <RefreshCw
            className={cn("mr-1.5 h-3.5 w-3.5", isLoading && "animate-spin")}
          />
          Refresh
        </Button>
      </div>

      {/* Top-level status card */}
      {statusData && (
        <Card className="border-[var(--primary)]/20">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Shield className="h-4 w-4 text-[var(--primary)]" />
              Security Posture
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {Object.entries(statusData).map(([key, val]) => (
                <div
                  key={key}
                  className="flex items-center justify-between rounded-md bg-[var(--muted)] p-3"
                >
                  <span className="text-xs text-[var(--muted-foreground)] capitalize">
                    {key.replace(/_/g, " ")}
                  </span>
                  <Badge
                    variant={
                      val === true || val === "enabled" || val === "strict"
                        ? "success"
                        : val === false || val === "disabled" || val === "none"
                          ? "destructive"
                          : "secondary"
                    }
                  >
                    {String(val)}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Security health compliance */}
      {healthData && (
        <Card className="glass">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <ShieldCheck className="h-4 w-4 text-[var(--primary)]" />
              Compliance Checks
              {healthData.compliance_score !== undefined && (
                <Badge
                  variant={
                    Number(healthData.compliance_score) >= 80
                      ? "success"
                      : Number(healthData.compliance_score) >= 50
                        ? "warning"
                        : "destructive"
                  }
                  className="ml-auto"
                >
                  {healthData.compliance_score}%
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {healthData.checks && Array.isArray(healthData.checks) ? (
              <div className="space-y-1.5">
                {healthData.checks.map((check, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 rounded p-2 text-xs hover:bg-[var(--muted)]"
                  >
                    {check.status === "pass" || check.status === "ok" ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-[var(--success)] shrink-0" />
                    ) : check.status === "warn" ? (
                      <AlertTriangle className="h-3.5 w-3.5 text-[var(--warning)] shrink-0" />
                    ) : (
                      <XCircle className="h-3.5 w-3.5 text-[var(--destructive)] shrink-0" />
                    )}
                    <span className="font-medium flex-1">{check.name}</span>
                    {check.details && (
                      <span className="text-[var(--muted-foreground)] text-[10px]">
                        {check.details}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <pre className="rounded bg-[var(--muted)] p-2 text-[10px] overflow-auto max-h-32">
                {JSON.stringify(healthData, null, 2)}
              </pre>
            )}
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {/* Corruption monitoring */}
        <Card className="glass">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <ShieldAlert className="h-4 w-4 text-[var(--warning)]" />
              Corruption Monitor
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {corruptionData ? (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted-foreground)]">
                    Monitored endpoints
                  </span>
                  <span className="text-xs font-mono">
                    {String(corruptionData.monitored_endpoints ?? 0)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted-foreground)]">
                    Total penalties
                  </span>
                  <Badge
                    variant={
                      Number(corruptionData.total_penalties) > 0
                        ? "warning"
                        : "success"
                    }
                  >
                    {String(corruptionData.total_penalties ?? 0)}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted-foreground)]">
                    System status
                  </span>
                  <Badge variant="outline">
                    {String(corruptionData.system_status ?? "unknown")}
                  </Badge>
                </div>
              </>
            ) : corruption.isLoading ? (
              <Loader2 className="mx-auto h-5 w-5 animate-spin text-[var(--muted-foreground)]" />
            ) : (
              <p className="text-xs text-[var(--muted-foreground)]">
                Corruption monitor offline
              </p>
            )}
          </CardContent>
        </Card>

        {/* DRT analysis */}
        <Card className="glass">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Lock className="h-4 w-4 text-[var(--primary)]" />
              DRT Analysis
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {drtData ? (
              <pre className="rounded bg-[var(--muted)] p-2 text-[10px] overflow-auto max-h-32">
                {JSON.stringify(drtData, null, 2)}
              </pre>
            ) : drt.isLoading ? (
              <Loader2 className="mx-auto h-5 w-5 animate-spin text-[var(--muted-foreground)]" />
            ) : (
              <p className="text-xs text-[var(--muted-foreground)]">
                DRT system offline
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Fallback when all offline */}
      {!statusData && !healthData && !isLoading && (
        <Card className="border-[var(--warning)]/30">
          <CardContent className="flex items-center gap-3 p-4">
            <AlertTriangle className="h-5 w-5 text-[var(--warning)] shrink-0" />
            <p className="text-sm text-[var(--muted-foreground)]">
              Unable to reach GRID backend security endpoints. Start the API
              server to view security status.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
