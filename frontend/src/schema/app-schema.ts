export type IconKey =
  | "layout-dashboard"
  | "search"
  | "brain"
  | "shield"
  | "activity"
  | "database"
  | "terminal"
  | "settings"
  | "zap"
  | "message-square"
  | "sparkles"
  | "radar"
  | "cog";

export type RouteKey =
  | "dashboard"
  | "chat"
  | "rag"
  | "intelligence"
  | "cognitive"
  | "security"
  | "observability"
  | "knowledge"
  | "terminal"
  | "settings";

export type EndpointKey =
  | "health"
  | "healthLive"
  | "healthReady"
  | "ragQuery"
  | "ragQueryStream"
  | "intelligenceProcess"
  | "cockpitStatus"
  | "cockpitHealth"
  | "agenticCases"
  | "navigationPlan"
  | "safetyInfer"
  | "skillsHealth"
  | "securityStatus"
  | "ollamaModels"
  | "ollamaChat";

export type BadgeVariant =
  | "default"
  | "secondary"
  | "success"
  | "warning"
  | "destructive"
  | "outline";

export interface RouteConfig {
  id: RouteKey;
  path: string;
  title: string;
  description: string;
  navLabel: string;
  icon: IconKey;
}

export interface NavigationConfig {
  primary: RouteKey[];
  secondary: RouteKey[];
}

export interface DashboardStat {
  id: string;
  label: string;
  icon: IconKey;
  source: "static" | "health";
  value?: string;
  health?: {
    ok: string;
    fail: string;
    okVariant: BadgeVariant;
    failVariant: BadgeVariant;
  };
}

export interface DashboardQuickAction {
  id: string;
  title: string;
  description: string;
  icon: IconKey;
  routeId?: RouteKey;
}

export interface RagConfig {
  title: string;
  description: string;
  placeholder: string;
  submitLabel: string;
  endpointId: EndpointKey;
  streamEndpointId: EndpointKey;
}

export interface ChatConfig {
  title: string;
  description: string;
  placeholder: string;
  defaultModel: string;
  systemPrompt: string;
  preferredModels: string[];
}

export interface IntelligenceConfig {
  title: string;
  description: string;
  endpointId: EndpointKey;
  capabilities: {
    id: string;
    label: string;
    description: string;
    icon: IconKey;
  }[];
}

export interface SettingsItem {
  label: string;
  value?: string;
  valueFrom?: "api.baseUrl" | "api.ollamaUrl";
}

export interface SettingsSection {
  title: string;
  description?: string;
  items: SettingsItem[];
}

export interface AppConfig {
  metadata: {
    name: string;
    description: string;
    version: string;
  };
  api: {
    baseUrl: string;
    ollamaUrl: string;
    endpoints: Record<EndpointKey, string>;
  };
  routes: RouteConfig[];
  navigation: NavigationConfig;
  dashboard: {
    stats: DashboardStat[];
    quickActions: DashboardQuickAction[];
  };
  chat: ChatConfig;
  rag: RagConfig;
  intelligence: IntelligenceConfig;
  settings: {
    sections: SettingsSection[];
  };
}
