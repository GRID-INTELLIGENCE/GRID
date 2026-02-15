import { Outlet } from "react-router-dom";
import { OfflineBanner } from "../ui/OfflineBanner";
import { Sidebar } from "./Sidebar";
import { TitleBar } from "./TitleBar";

export function AppShell() {
  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <TitleBar />
      <OfflineBanner />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
