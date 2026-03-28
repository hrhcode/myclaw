import type { ReactNode } from "react";
import { memo } from "react";
import Sidebar from "./Sidebar";
import ThemeToggle from "../common/ThemeToggle";
import { useApp } from "../../contexts/AppContext";

interface MainLayoutProps {
  children: ReactNode;
  showHeader?: boolean;
  headerTitle?: string;
}

/**
 * 主布局组件 - 包含侧边栏、顶部栏和内容区域
 */
const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  showHeader = true,
  headerTitle,
}) => {
  const { sidebarCollapsed, toggleSidebar } = useApp();

  return (
    <div className="app-container flex h-screen overflow-hidden">
      <div className="app-bg-glow" />

      <Sidebar
        isCollapsed={sidebarCollapsed}
        onToggleCollapse={toggleSidebar}
      />

      <div className="main-content flex-1 flex flex-col overflow-hidden">
        {showHeader && (
          <header className="navbar h-16 flex items-center justify-between px-6 flex-shrink-0">
            <div className="flex items-center gap-3">
              {headerTitle && (
                <h1
                  className="text-lg font-semibold"
                  style={{ color: "var(--text-primary)" }}
                >
                  {headerTitle}
                </h1>
              )}
            </div>

            <div className="flex items-center gap-3">
              <ThemeToggle />
            </div>
          </header>
        )}

        <div className="flex-1 overflow-hidden">{children}</div>
      </div>
    </div>
  );
};

export default memo(MainLayout);
