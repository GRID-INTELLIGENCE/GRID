import type { LucideIcon } from "lucide-react";
import {
  Activity,
  Brain,
  Cog,
  Compass,
  Database,
  LayoutDashboard,
  MessageSquare,
  Presentation,
  Radar,
  Search,
  Settings,
  Shield,
  Sparkles,
  Sprout,
  Terminal,
  Zap,
} from "lucide-react";
import { lazy, type ComponentType } from "react";
import type {
  AppConfig,
  EndpointKey,
  IconKey,
  RouteConfig,
  RouteKey,
  SettingsItem,
} from "./app-schema";
import rawConfig from "./app.config.json";

export const appConfig = rawConfig as AppConfig;

export const iconRegistry: Record<IconKey, LucideIcon> = {
  activity: Activity,
  brain: Brain,
  cog: Cog,
  compass: Compass,
  database: Database,
  "layout-dashboard": LayoutDashboard,
  "message-square": MessageSquare,
  radar: Radar,
  search: Search,
  settings: Settings,
  shield: Shield,
  sparkles: Sparkles,
  terminal: Terminal,
  zap: Zap,
  sprout: Sprout,
  presentation: Presentation,
};

/** Helper to lazy-load a named export from a page module */
function lazyRoute<T extends Record<string, ComponentType>>(
  loader: () => Promise<T>,
  exportName: keyof T
): React.LazyExoticComponent<ComponentType> {
  return lazy(() =>
    loader().then((mod) => ({ default: mod[exportName] as ComponentType }))
  );
}

export const routeComponents: Record<RouteKey, ComponentType> = {
  dashboard: lazyRoute(() => import("@/pages/Dashboard"), "Dashboard"),
  chat: lazyRoute(() => import("@/pages/ChatPage"), "ChatPage"),
  rag: lazyRoute(() => import("@/pages/RagQuery"), "RagQuery"),
  intelligence: lazyRoute(
    () => import("@/pages/IntelligencePage"),
    "IntelligencePage"
  ),
  cognitive: lazyRoute(() => import("@/pages/Cognitive"), "Cognitive"),
  security: lazyRoute(() => import("@/pages/Security"), "Security"),
  observability: lazyRoute(
    () => import("@/pages/Observability"),
    "Observability"
  ),
  knowledge: lazyRoute(() => import("@/pages/Knowledge"), "Knowledge"),
  terminal: lazyRoute(() => import("@/pages/TerminalPage"), "TerminalPage"),
  settings: lazyRoute(() => import("@/pages/SettingsPage"), "SettingsPage"),
  register: lazyRoute(() => import("@/pages/Register"), "Register"),
  login: lazyRoute(() => import("@/pages/Login"), "Login"),
  roundtable: lazyRoute(
    () => import("@/pages/RoundTablePage"),
    "RoundTablePage"
  ),
  mycelium: lazyRoute(() => import("@/pages/MyceliumPage"), "MyceliumPage"),
  "mycelium-demo": lazyRoute(
    () => import("@/pages/MyceliumDemo"),
    "MyceliumDemo"
  ),
};

const routesById = new Map<RouteKey, RouteConfig>(
  appConfig.routes.map((route) => [route.id, route])
);

export function getRoute(routeId: RouteKey): RouteConfig {
  const route = routesById.get(routeId);
  if (!route) {
    throw new Error(`Route not found: ${routeId}`);
  }
  return route;
}

export function getEndpoint(endpointId: EndpointKey): string {
  return appConfig.api.endpoints[endpointId];
}

export function resolveSettingValue(item: SettingsItem): string {
  if (item.value) return item.value;
  if (item.valueFrom === "api.baseUrl") return appConfig.api.baseUrl;
  if (item.valueFrom === "api.ollamaUrl") return appConfig.api.ollamaUrl;
  return "";
}
