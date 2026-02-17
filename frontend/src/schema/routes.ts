import type { RouteKey } from "./app-schema";
import { getRoute } from "./index";

export function getRoutes(routeIds: RouteKey[]) {
  return routeIds.map(getRoute);
}
