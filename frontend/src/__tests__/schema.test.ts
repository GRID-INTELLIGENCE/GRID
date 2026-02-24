import {
  appConfig,
  getEndpoint,
  getRoute,
  iconRegistry,
  resolveSettingValue,
  routeComponents,
} from "@/schema";
import type { EndpointKey, IconKey, RouteKey } from "@/schema/app-schema";
import { describe, expect, it } from "vitest";

describe("appConfig", () => {
  it("has valid metadata", () => {
    expect(appConfig.metadata.name).toBe("GRID");
    expect(appConfig.metadata.version).toMatch(/^\d+\.\d+\.\d+$/);
  });

  it("has api base urls", () => {
    expect(appConfig.api.baseUrl).toMatch(/^https?:\/\//);
    expect(appConfig.api.ollamaUrl).toMatch(/^https?:\/\//);
  });

  it("has at least 10 endpoints", () => {
    const endpointKeys = Object.keys(appConfig.api.endpoints);
    expect(endpointKeys.length).toBeGreaterThanOrEqual(10);
  });

  it("all endpoints are string paths", () => {
    for (const [_key, path] of Object.entries(appConfig.api.endpoints)) {
      expect(typeof path).toBe("string");
      expect(path).toMatch(/^\//);
    }
  });

  it("has at least 8 routes", () => {
    expect(appConfig.routes.length).toBeGreaterThanOrEqual(8);
  });

  it("all routes have required fields", () => {
    const navRouteIds = new Set([
      ...appConfig.navigation.primary,
      ...appConfig.navigation.secondary,
    ]);
    for (const route of appConfig.routes) {
      expect(route.id).toBeTruthy();
      expect(route.path).toMatch(/^\//);
      expect(route.title).toBeTruthy();
      // navLabel and icon are only required for navigable routes
      if (navRouteIds.has(route.id)) {
        expect(route.navLabel).toBeTruthy();
        expect(route.icon).toBeTruthy();
      }
    }
  });

  it("navigation references valid routes", () => {
    const routeIds = new Set(appConfig.routes.map((r) => r.id));
    for (const id of appConfig.navigation.primary) {
      expect(routeIds.has(id)).toBe(true);
    }
    for (const id of appConfig.navigation.secondary) {
      expect(routeIds.has(id)).toBe(true);
    }
  });

  it("dashboard stats reference valid icons", () => {
    const validIcons = new Set(Object.keys(iconRegistry));
    for (const stat of appConfig.dashboard.stats) {
      expect(validIcons.has(stat.icon)).toBe(true);
    }
  });

  it("dashboard quick actions reference valid routes", () => {
    const routeIds = new Set(appConfig.routes.map((r) => r.id));
    for (const action of appConfig.dashboard.quickActions) {
      if (action.routeId) {
        expect(routeIds.has(action.routeId)).toBe(true);
      }
    }
  });

  it("chat config has required fields", () => {
    expect(appConfig.chat.title).toBeTruthy();
    expect(appConfig.chat.defaultModel).toBeTruthy();
    expect(appConfig.chat.systemPrompt).toBeTruthy();
    expect(appConfig.chat.preferredModels.length).toBeGreaterThan(0);
  });

  it("rag config has both endpoint ids", () => {
    expect(appConfig.rag.endpointId).toBeTruthy();
    expect(appConfig.rag.streamEndpointId).toBeTruthy();
    expect(appConfig.api.endpoints[appConfig.rag.endpointId]).toBeTruthy();
    expect(
      appConfig.api.endpoints[appConfig.rag.streamEndpointId]
    ).toBeTruthy();
  });

  it("intelligence config has capabilities", () => {
    expect(appConfig.intelligence.capabilities.length).toBeGreaterThan(0);
    for (const cap of appConfig.intelligence.capabilities) {
      expect(cap.id).toBeTruthy();
      expect(cap.label).toBeTruthy();
      expect(cap.icon).toBeTruthy();
    }
  });
});

describe("iconRegistry", () => {
  it("has entries for all IconKey values", () => {
    const expectedKeys: IconKey[] = [
      "layout-dashboard",
      "search",
      "brain",
      "shield",
      "activity",
      "database",
      "terminal",
      "settings",
      "zap",
      "message-square",
      "sparkles",
      "radar",
      "cog",
      "compass",
    ];
    for (const key of expectedKeys) {
      expect(iconRegistry[key]).toBeDefined();
      // Lucide icons can be ForwardRef objects or functions depending on build
      expect(["function", "object"].includes(typeof iconRegistry[key])).toBe(
        true
      );
    }
  });
});

describe("routeComponents", () => {
  it("has a component for every route in config", () => {
    for (const route of appConfig.routes) {
      expect(routeComponents[route.id]).toBeDefined();
      expect(typeof routeComponents[route.id]).toBe("function");
    }
  });

  it("maps all RouteKey values", () => {
    const expectedKeys: RouteKey[] = [
      "dashboard",
      "chat",
      "rag",
      "intelligence",
      "cognitive",
      "security",
      "observability",
      "knowledge",
      "terminal",
      "settings",
    ];
    for (const key of expectedKeys) {
      expect(routeComponents[key]).toBeDefined();
    }
  });
});

describe("getRoute", () => {
  it("returns route config for valid id", () => {
    const route = getRoute("dashboard");
    expect(route.id).toBe("dashboard");
    expect(route.path).toBe("/");
    expect(route.title).toBeTruthy();
  });

  it("returns chat route", () => {
    const route = getRoute("chat");
    expect(route.id).toBe("chat");
    expect(route.path).toBe("/chat");
  });

  it("throws for invalid route", () => {
    expect(() => getRoute("nonexistent" as RouteKey)).toThrow(
      "Route not found"
    );
  });
});

describe("getEndpoint", () => {
  it("returns health endpoint path", () => {
    expect(getEndpoint("health")).toBe("/health");
  });

  it("returns ragQueryStream endpoint path", () => {
    expect(getEndpoint("ragQueryStream")).toBe("/rag/query/stream");
  });

  it("returns intelligenceProcess endpoint path", () => {
    expect(getEndpoint("intelligenceProcess")).toBe(
      "/api/v1/intelligence/process"
    );
  });

  it("returns all required endpoints", () => {
    const keys: EndpointKey[] = [
      "health",
      "healthLive",
      "healthReady",
      "ragQuery",
      "ragQueryStream",
      "intelligenceProcess",
      "cockpitHealth",
      "ollamaModels",
      "ollamaChat",
    ];
    for (const key of keys) {
      const path = getEndpoint(key);
      expect(typeof path).toBe("string");
      expect(path.startsWith("/")).toBe(true);
    }
  });
});

describe("resolveSettingValue", () => {
  it("returns static value when present", () => {
    expect(resolveSettingValue({ label: "Test", value: "hello" })).toBe(
      "hello"
    );
  });

  it("resolves api.baseUrl reference", () => {
    expect(
      resolveSettingValue({ label: "Test", valueFrom: "api.baseUrl" })
    ).toBe(appConfig.api.baseUrl);
  });

  it("resolves api.ollamaUrl reference", () => {
    expect(
      resolveSettingValue({ label: "Test", valueFrom: "api.ollamaUrl" })
    ).toBe(appConfig.api.ollamaUrl);
  });

  it("returns empty string when no value or valueFrom", () => {
    expect(resolveSettingValue({ label: "Test" })).toBe("");
  });
});
