import { cn } from "@/lib/utils";
import { appConfig, getRoute, iconRegistry } from "@/schema";
import { NavLink } from "react-router-dom";

function NavSection({ items }: { items: ReturnType<typeof getRoute>[] }) {
  return (
    <nav className="flex flex-col gap-1 px-2">
      {items.map((item) => {
        const Icon = iconRegistry[item.icon];
        return (
          <NavLink
            key={item.id}
            to={item.path}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-[var(--accent)] text-[var(--sidebar-active)] font-medium"
                  : "text-[var(--sidebar-foreground)] hover:bg-[var(--accent)] hover:text-[var(--foreground)]"
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            <span>{item.navLabel}</span>
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
        <NavSection items={appConfig.navigation.primary.map(getRoute)} />
      </div>
      <div className="border-t border-[var(--border)] py-3">
        <NavSection items={appConfig.navigation.secondary.map(getRoute)} />
      </div>
    </aside>
  );
}
