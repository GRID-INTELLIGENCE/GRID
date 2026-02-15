import { AppShell } from "@/components/layout/AppShell";
import { appConfig, routeComponents } from "@/schema";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { HashRouter, Route, Routes } from "react-router-dom";

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<AppShell />}>
          {appConfig.routes.map((route) => {
            const Component = routeComponents[route.id];
            return (
              <Route key={route.id} path={route.path} element={<Component />} />
            );
          })}
        </Route>
      </Routes>
      <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" />
    </HashRouter>
  );
}
