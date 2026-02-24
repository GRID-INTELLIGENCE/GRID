import { Cognitive } from "@/pages/Cognitive";
import { Login } from "@/pages/Login";
import { Register } from "@/pages/Register";
import { Dashboard } from "@/pages/Dashboard";
import { Knowledge } from "@/pages/Knowledge";
import { Observability } from "@/pages/Observability";
import { RagQuery } from "@/pages/RagQuery";
import { Security } from "@/pages/Security";
import { SettingsPage } from "@/pages/SettingsPage";
import { RoundTablePage } from "@/pages/RoundTablePage";
import { TerminalPage } from "@/pages/TerminalPage";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  Brain,
  Cog,
  Compass,
  Database,
  LayoutDashboard,
  MessageSquare,
  Radar,
  Search,
  Settings,
  Shield,
  Sparkles,
  Terminal,
  Zap,
} from "lucide-react";
import type { ComponentType } from "react";
import { ChatPage } from "../pages/ChatPage";
import { IntelligencePage } from "../pages/IntelligencePage";
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
};

export const routeComponents: Record<RouteKey, ComponentType> = {
  dashboard: Dashboard,
  chat: ChatPage,
  rag: RagQuery,
  intelligence: IntelligencePage,
  cognitive: Cognitive,
  security: Security,
  observability: Observability,
  knowledge: Knowledge,
  terminal: TerminalPage,
  settings: SettingsPage,
  register: Register,
  login: Login,
  roundtable: RoundTablePage,
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
