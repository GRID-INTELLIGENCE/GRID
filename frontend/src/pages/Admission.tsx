import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useAdmissionBannered,
  useAdmissionPolicy,
  useAdmissionStats,
} from "@/hooks";
import { cn } from "@/lib/utils";
import type { AdmissionEntityReport } from "@/types/api";
import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Scale,
  Shield,
  ShieldAlert,
  TrendingUp,
  Users,
} from "lucide-react";

function tierVariant(
  tier: string
): "default" | "warning" | "destructive" | "success" {
  switch (tier) {
    case "intentional_scheming":
      return "destructive";
    case "environment_pollution":
      return "warning";
    case "runtime_mistake":
      return "default";
    default:
      return "success";
  }
}

function EntityRow({ entity }: { entity: AdmissionEntityReport }) {
  return (
    <div className="flex items-center gap-3 rounded-md bg-[var(--muted)] p-3">
      <Ban className="h-4 w-4 shrink-0 text-[var(--destructive)]" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-mono font-medium">
          {entity.entity_id}
        </p>
        <p className="text-[11px] text-[var(--muted-foreground)]">
          {entity.banner_reason || "Threshold exceeded"}
        </p>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <Badge
          variant={tierVariant(entity.penalty_tier)}
          className="text-[10px]"
        >
          {entity.penalty_tier.replace(/_/g, " ")}
        </Badge>
        <span className="text-xs font-mono tabular-nums text-[var(--muted-foreground)]">
          {entity.total_penalty_points} pts
        </span>
        <span className="text-xs text-[var(--muted-foreground)]">
          {entity.violation_count} violations
        </span>
      </div>
    </div>
  );
}

export function Admission() {
  const stats = useAdmissionStats({ refetchInterval: 10_000 });
  const policy = useAdmissionPolicy();
  const bannered = useAdmissionBannered();

  const statsData = stats.data;
  const policyData = policy.data;
  const banneredData = bannered.data;

  const isLoading = stats.isLoading || policy.isLoading;

  const admitRate =
    statsData && statsData.total_admitted + statsData.total_rejected > 0
      ? (
          (statsData.total_admitted /
            (statsData.total_admitted + statsData.total_rejected)) *
          100
        ).toFixed(1)
      : "—";

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Admission Gate</h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            Ethical participation enforcement — policy, penalties, gate
            statistics
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            stats.refetch();
            policy.refetch();
            bannered.refetch();
          }}
        >
          <RefreshCw
            className={cn("mr-1.5 h-3.5 w-3.5", isLoading && "animate-spin")}
          />
          Refresh
        </Button>
      </div>

      {/* Stats row */}
      {statsData && (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <CheckCircle2 className="h-5 w-5 text-[var(--success)]" />
              <div>
                <p className="text-[10px] uppercase tracking-wide text-[var(--muted-foreground)]">
                  Admitted
                </p>
                <p className="text-lg font-semibold tabular-nums">
                  {statsData.total_admitted.toLocaleString()}
                </p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <ShieldAlert className="h-5 w-5 text-[var(--destructive)]" />
              <div>
                <p className="text-[10px] uppercase tracking-wide text-[var(--muted-foreground)]">
                  Rejected
                </p>
                <p className="text-lg font-semibold tabular-nums">
                  {statsData.total_rejected.toLocaleString()}
                </p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <TrendingUp className="h-5 w-5 text-[var(--primary)]" />
              <div>
                <p className="text-[10px] uppercase tracking-wide text-[var(--muted-foreground)]">
                  Admit Rate
                </p>
                <p className="text-lg font-semibold tabular-nums">
                  {admitRate}%
                </p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <Users className="h-5 w-5 text-[var(--primary)]" />
              <div>
                <p className="text-[10px] uppercase tracking-wide text-[var(--muted-foreground)]">
                  Tracked
                </p>
                <p className="text-lg font-semibold tabular-nums">
                  {statsData.tracked_entities}
                </p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <Ban className="h-5 w-5 text-[var(--warning)]" />
              <div>
                <p className="text-[10px] uppercase tracking-wide text-[var(--muted-foreground)]">
                  Bannered
                </p>
                <p className="text-lg font-semibold tabular-nums">
                  {statsData.bannered_entities}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Rejection breakdown */}
      {statsData && Object.keys(statsData.rejection_reasons).length > 0 && (
        <Card className="glass">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <ShieldAlert className="h-4 w-4 text-[var(--warning)]" />
              Rejection Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {Object.entries(statsData.rejection_reasons).map(
                ([reason, count]) => (
                  <div
                    key={reason}
                    className="flex items-center justify-between rounded-md bg-[var(--muted)] p-2.5"
                  >
                    <span className="text-xs text-[var(--muted-foreground)]">
                      {reason.replace(/_/g, " ")}
                    </span>
                    <Badge
                      variant="secondary"
                      className="font-mono text-[10px]"
                    >
                      {count}
                    </Badge>
                  </div>
                )
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Policy billboard */}
        {policyData && (
          <Card className="border-[var(--primary)]/20">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Scale className="h-4 w-4 text-[var(--primary)]" />
                Policy Billboard
                <Badge variant="outline" className="ml-auto text-[10px]">
                  v{policyData.billboard_version}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {/* Principles */}
              <div>
                <p className="mb-1.5 text-[10px] uppercase tracking-wide text-[var(--muted-foreground)]">
                  Principles
                </p>
                <div className="space-y-1">
                  {Object.entries(policyData.principles).map(([name, val]) => (
                    <div key={name} className="flex items-center gap-2 text-xs">
                      {val ? (
                        <CheckCircle2 className="h-3 w-3 text-[var(--success)]" />
                      ) : (
                        <AlertTriangle className="h-3 w-3 text-[var(--warning)]" />
                      )}
                      <span>{name.replace(/_/g, " ")}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Penalty tiers */}
              <div>
                <p className="mb-1.5 text-[10px] uppercase tracking-wide text-[var(--muted-foreground)]">
                  Penalty Tiers
                </p>
                <div className="space-y-1">
                  {Object.entries(policyData.penalty_tiers).map(
                    ([tier, desc]) => (
                      <div
                        key={tier}
                        className="flex items-start gap-2 rounded bg-[var(--muted)] p-2 text-xs"
                      >
                        <Badge
                          variant={tierVariant(tier)}
                          className="shrink-0 text-[10px]"
                        >
                          {tier.replace(/_/g, " ")}
                        </Badge>
                        <span className="text-[var(--muted-foreground)]">
                          {desc}
                        </span>
                      </div>
                    )
                  )}
                </div>
              </div>

              {/* Caution */}
              <div className="rounded border border-[var(--warning)]/30 bg-[var(--warning)]/5 p-2">
                <p className="text-[11px] text-[var(--warning)]">
                  {policyData.caution}
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Bannered entities */}
        <Card className="glass">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Shield className="h-4 w-4 text-[var(--destructive)]" />
              Bannered Entities
              {banneredData && (
                <Badge
                  variant={banneredData.count > 0 ? "destructive" : "success"}
                  className="ml-auto"
                >
                  {banneredData.count}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {banneredData && banneredData.entities.length > 0 ? (
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {banneredData.entities.map((entity) => (
                  <EntityRow key={entity.entity_id} entity={entity} />
                ))}
              </div>
            ) : bannered.isLoading ? (
              <Loader2 className="mx-auto h-5 w-5 animate-spin text-[var(--muted-foreground)]" />
            ) : (
              <div className="flex flex-col items-center gap-2 py-6 text-[var(--muted-foreground)]">
                <CheckCircle2 className="h-8 w-8 text-[var(--success)]" />
                <p className="text-xs">No entities currently bannered</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Offline fallback */}
      {!statsData && !policyData && !isLoading && (
        <Card className="border-[var(--warning)]/30">
          <CardContent className="flex items-center gap-3 p-4">
            <AlertTriangle className="h-5 w-5 text-[var(--warning)] shrink-0" />
            <p className="text-sm text-[var(--muted-foreground)]">
              Admission gate is not active. Start the Mothership API with
              admission gate enabled to view enforcement data.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
