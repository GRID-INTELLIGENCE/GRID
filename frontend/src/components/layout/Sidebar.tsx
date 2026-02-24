import { cn } from "@/lib/utils";
import { appConfig, getRoute, iconRegistry } from "@/schema";
import { NavLink } from "react-router-dom";

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <span className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-widest text-[var(--muted-foreground)]">
      {children}
    </span>
  );
}

function NavSection({
  items,
  label,
}: {
  items: ReturnType<typeof getRoute>[];
  label?: string;
}) {
  return (
    <nav className="flex flex-col gap-0.5 px-2">
      {label && <SectionLabel>{label}</SectionLabel>}
      {items.map((item) => {
        const Icon = iconRegistry[item.icon];
        return (
          <NavLink
            key={item.id}
            to={item.path}
            className={({ isActive }) =>
              cn(
                "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all",
                "duration-150",
                isActive
                  ? "text-[var(--sidebar-active)] font-medium"
                  : "text-[var(--sidebar-foreground)] hover:text-[var(--foreground)] hover:translate-x-0.5"
              )
            }
          >
            {({ isActive }) => (
              <>
                {/* Active indicator bar */}
                {isActive && (
                  <span
                    className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-[var(--primary)]"
                    aria-hidden="true"
                  />
                )}
                <Icon className="h-4 w-4 shrink-0" />
                <span>{item.navLabel}</span>
              </>
            )}
          </NavLink>
        );
      })}
    </nav>
  );
}

export function Sidebar() {
  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-[var(--border)] bg-[var(--sidebar)]">
      <div className="flex-1 overflow-y-auto py-4">
        <NavSection
          label="Core"
          items={appConfig.navigation.primary.map(getRoute)}
        />
      </div>
      <div className="border-t border-[var(--border)] py-3">
        <NavSection
          label="Tools"
          items={appConfig.navigation.secondary.map(getRoute)}
        />
      </div>
    </aside>
  );
}
