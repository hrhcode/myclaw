import type { ReactNode } from "react";
import { memo } from "react";

import { useApp } from "../../contexts/AppContext";
import ThemeToggle from "../common/ThemeToggle";
import Sidebar from "./Sidebar";

interface MainLayoutProps {
  children: ReactNode;
  headerTitle?: string;
  headerSubtitle?: string;
  headerActions?: ReactNode;
  contentClassName?: string;
}

const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  headerTitle,
  headerSubtitle,
  headerActions,
  contentClassName = "",
}) => {
  const { sidebarCollapsed, toggleSidebar } = useApp();

  return (
    <div className={`shell ${sidebarCollapsed ? "shell--nav-collapsed" : ""}`}>
      <header className="topbar">
        <div className="topbar-left">
          <button
            className="nav-collapse-toggle"
            onClick={toggleSidebar}
            aria-label={sidebarCollapsed ? "展开导航" : "收起导航"}
            title={sidebarCollapsed ? "展开导航" : "收起导航"}
          >
            <span className="nav-collapse-toggle__icon">≡</span>
          </button>
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
        {headerTitle || headerActions ? (
          <section className="content-header">
            <div>
              {headerTitle ? (
                <div className="page-title">{headerTitle}</div>
              ) : null}
            </div>
            {headerActions ? (
              <div className="page-meta">{headerActions}</div>
            ) : null}
          </section>
        ) : null}

        {children}
      </main>
    </div>
  );
};

export default memo(MainLayout);
