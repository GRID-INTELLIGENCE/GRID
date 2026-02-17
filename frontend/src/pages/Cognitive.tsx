import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useCockpitState,
  useNavigationPlan,
  useResonanceContext,
  useSkillsHealth,
} from "@/hooks";
import { cn } from "@/lib/utils";
import type { NavigationPlan } from "@/types/api";
import {
  Activity,
  Brain,
  Compass,
  GitFork,
  Loader2,
  Play,
  RefreshCw,
  Sparkles,
  Zap,
} from "lucide-react";
import { useState } from "react";

export function Cognitive() {
  const [navGoal, setNavGoal] = useState("");
  const [navResult, setNavResult] = useState<NavigationPlan | null>(null);

  const cockpit = useCockpitState();
  const resonance = useResonanceContext();
  const skills = useSkillsHealth();

  const navPlan = useNavigationPlan();

  const handleNavPlan = () => {
    if (!navGoal.trim() || navPlan.isPending) return;
    setNavResult(null);
    navPlan.mutate(
      { goal: navGoal.trim() },
      {
        onSuccess(res) {
          if (res.ok && res.data) setNavResult(res.data);
        },
      }
    );
  };

  const cockpitData = cockpit.data;
  const resonanceData = resonance.data;
  const skillsData = skills.data;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Cognitive Patterns
          </h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            Monitor event-driven cognitive processing, navigation, and resonance
            patterns
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            cockpit.refetch();
            resonance.refetch();
            skills.refetch();
          }}
        >
          <RefreshCw
            className={cn(
              "mr-1.5 h-3.5 w-3.5",
              cockpit.isFetching && "animate-spin"
            )}
          />
          Refresh
        </Button>
      </div>

      {/* Status cards row */}
      <div className="grid gap-3 sm:grid-cols-3">
        {/* Cockpit state */}
        <Card className="glass">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Brain className="h-4 w-4 text-[var(--primary)]" />
              Cockpit
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {cockpitData ? (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted-foreground)]">
                    Status
                  </span>
                  <Badge
                    variant={
                      cockpitData.status === "running" ? "success" : "warning"
                    }
                  >
                    {String(cockpitData.status ?? "unknown")}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted-foreground)]">
                    Mode
                  </span>
                  <span className="text-xs font-medium">
                    {String(cockpitData.mode ?? "—")}
                  </span>
                </div>
                {cockpitData.uptime !== undefined && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[var(--muted-foreground)]">
                      Uptime
                    </span>
                    <span className="text-xs font-mono">
                      {Math.floor(Number(cockpitData.uptime) / 60)}m
                    </span>
                  </div>
                )}
              </>
            ) : cockpit.isLoading ? (
              <Loader2 className="mx-auto h-5 w-5 animate-spin text-[var(--muted-foreground)]" />
            ) : (
              <p className="text-xs text-[var(--muted-foreground)]">
                Unable to reach cockpit
              </p>
            )}
          </CardContent>
        </Card>

        {/* Resonance */}
        <Card className="glass">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Activity className="h-4 w-4 text-[var(--primary)]" />
              Resonance
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {resonanceData ? (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted-foreground)]">
                    Active activities
                  </span>
                  <span className="text-xs font-mono">
                    {String(resonanceData.active_activities ?? 0)}
                  </span>
                </div>
                {resonanceData.context_state && (
                  <pre className="rounded bg-[var(--muted)] p-2 text-[10px] overflow-auto max-h-20">
                    {JSON.stringify(resonanceData.context_state, null, 2)}
                  </pre>
                )}
              </>
            ) : resonance.isLoading ? (
              <Loader2 className="mx-auto h-5 w-5 animate-spin text-[var(--muted-foreground)]" />
            ) : (
              <p className="text-xs text-[var(--muted-foreground)]">
                Resonance offline
              </p>
            )}
          </CardContent>
        </Card>

        {/* Skills */}
        <Card className="glass">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Sparkles className="h-4 w-4 text-[var(--primary)]" />
              Skills
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {skillsData ? (
              <pre className="rounded bg-[var(--muted)] p-2 text-[10px] overflow-auto max-h-24">
                {JSON.stringify(skillsData, null, 2)}
              </pre>
            ) : skills.isLoading ? (
              <Loader2 className="mx-auto h-5 w-5 animate-spin text-[var(--muted-foreground)]" />
            ) : (
              <p className="text-xs text-[var(--muted-foreground)]">
                Skills system offline
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Navigation planner */}
      <Card className="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Compass className="h-4 w-4 text-[var(--primary)]" />
            Navigation Planner
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-xs text-[var(--muted-foreground)]">
            Generate a navigation plan using the cognitive routing engine
          </p>
          <div className="flex gap-2">
            <input
              value={navGoal}
              onChange={(e) => setNavGoal(e.target.value)}
              placeholder="Describe your goal…"
              className="flex-1 rounded-md border border-[var(--input)] bg-transparent px-3 py-2 text-sm placeholder:text-[var(--muted-foreground)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
              onKeyDown={(e) => e.key === "Enter" && handleNavPlan()}
            />
            <Button
              onClick={handleNavPlan}
              disabled={navPlan.isPending || !navGoal.trim()}
            >
              {navPlan.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="mr-1.5 h-4 w-4" />
              )}
              Plan
            </Button>
          </div>
          {navResult && (
            <div className="space-y-2 rounded-md bg-[var(--muted)] p-3">
              {navResult.primary_path && (
                <div>
                  <div className="flex items-center gap-1.5 mb-1">
                    <Zap className="h-3 w-3 text-[var(--primary)]" />
                    <span className="text-xs font-medium">Primary Path</span>
                  </div>
                  <pre className="text-[10px] overflow-auto">
                    {JSON.stringify(navResult.primary_path, null, 2)}
                  </pre>
                </div>
              )}
              {navResult.alternatives && navResult.alternatives.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-1">
                    <GitFork className="h-3 w-3 text-[var(--muted-foreground)]" />
                    <span className="text-xs font-medium">
                      Alternatives ({navResult.alternatives.length})
                    </span>
                  </div>
                  <pre className="text-[10px] overflow-auto max-h-40">
                    {JSON.stringify(navResult.alternatives, null, 2)}
                  </pre>
                </div>
              )}
              {!navResult.primary_path && !navResult.alternatives && (
                <pre className="text-[10px] overflow-auto">
                  {JSON.stringify(navResult, null, 2)}
                </pre>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
