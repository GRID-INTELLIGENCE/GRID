import { Suspense } from "react";
import { Outlet } from "react-router-dom";
import { OfflineBanner } from "../ui/OfflineBanner";
import { Sidebar } from "./Sidebar";
import { TitleBar } from "./TitleBar";

function PageSkeleton() {
  return (
    <div
      className="flex flex-col gap-4 p-6 animate-fade-in"
      aria-busy="true"
      aria-label="Loading page"
    >
      <div className="h-8 w-48 rounded-lg bg-[var(--muted)] animate-shimmer bg-[length:200%_100%] bg-gradient-to-r from-[var(--muted)] via-[var(--border)] to-[var(--muted)]" />
      <div
        className="h-4 w-80 rounded bg-[var(--muted)] animate-shimmer bg-[length:200%_100%] bg-gradient-to-r from-[var(--muted)] via-[var(--border)] to-[var(--muted)]"
        style={{ animationDelay: "100ms" }}
      />
      <div className="mt-4 grid grid-cols-3 gap-4">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="h-32 rounded-xl bg-[var(--muted)] animate-shimmer bg-[length:200%_100%] bg-gradient-to-r from-[var(--muted)] via-[var(--border)] to-[var(--muted)]"
            style={{ animationDelay: `${150 + i * 75}ms` }}
          />
        ))}
      </div>
    </div>
  );
}

export function AppShell() {
  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <TitleBar />
      <OfflineBanner />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-6">
          <Suspense fallback={<PageSkeleton />}>
            <Outlet />
          </Suspense>
        </main>
      </div>
    </div>
  );
}
