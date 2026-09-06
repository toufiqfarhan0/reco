import React from "react";
import { Routes, Route, Navigate, MemoryRouter, useInRouterContext } from "react-router-dom";
import { LandingPage } from "@/pages/LandingPage";
import { ConsolePage } from "@/pages/ConsolePage";
import { ArchitecturePage } from "@/pages/ArchitecturePage";

export interface AppProps {
  initialViewMode?: "overview" | "console";
  initialEntries?: string[];
  initialPage?: "landing" | "console";
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/console" element={<ConsolePage />} />
      <Route path="/architecture" element={<ArchitecturePage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App({ initialViewMode, initialEntries, initialPage }: AppProps = {}) {
  const isInRouter = useInRouterContext();

  if (!isInRouter) {
    const isConsole = initialViewMode === "console" || initialPage === "console";
    const entries = initialEntries || (isConsole ? ["/console"] : ["/"]);
    return (
      <MemoryRouter initialEntries={entries}>
        <AppRoutes />
      </MemoryRouter>
    );
  }

  return <AppRoutes />;
}

export { App as EngineeringConsolePage };
