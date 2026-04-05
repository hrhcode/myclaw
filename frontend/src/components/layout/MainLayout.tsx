import type { ReactNode } from "react";
import { memo } from "react";

import { useApp } from "../../contexts/AppContext";
import ThemeToggle from "../common/ThemeToggle";
import Sidebar from "./Sidebar";

interface MainLayoutProps {
  children: ReactNode;
  headerTitle?: string;
  headerActions?: ReactNode;
  contentClassName?: string;
}

const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  headerTitle,
  headerActions,
  contentClassName = "",
}) => {
  const { sidebarCollapsed, toggleSidebar } = useApp();

  return (
    <div className={`shell ${sidebarCollapsed ? "shell--nav-collapsed" : ""}`}>
      <header className="topbar">
        <div className="topbar-left">
          {headerTitle ? (
            <span className="topbar-title">{headerTitle}</span>
          ) : null}
          {headerActions ? (
            <div className="topbar-actions">{headerActions}</div>
          ) : null}
        </div>

        <div className="topbar-status">
          <div className="pill">
            <span className="statusDot ok"></span>
            <span>系统状态</span>
            <span className="mono">已就绪</span>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <Sidebar
        isCollapsed={sidebarCollapsed}
        onToggleCollapse={toggleSidebar}
      />

      <main className={`content ${contentClassName}`.trim()}>
        {children}
      </main>
    </div>
  );
};

export default memo(MainLayout);
