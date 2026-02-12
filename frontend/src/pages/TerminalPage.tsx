import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Terminal as TerminalIcon } from "lucide-react";

export function TerminalPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Terminal</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Interactive terminal for GRID CLI commands
        </p>
      </div>
      <Card className="glass min-h-[400px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <TerminalIcon className="h-4 w-4 text-[var(--primary)]" />
            GRID Shell
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg bg-[var(--background)] p-4 font-mono text-sm">
            <span className="text-[var(--primary)]">grid&gt;</span>{" "}
            <span className="text-[var(--muted-foreground)]">
              Type a command…
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
