import { NavLink, useLocation, matchPath } from "react-router-dom";
import {
  MessageCircleMore,
  FolderOpen,
  Settings,
  PanelLeftClose,
  PanelLeft,
  Brain,
  ScrollText,
  Bot,
  Wrench,
} from "lucide-react";
import { useState, useMemo } from "react";

interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

interface NavItem {
  path: string;
  icon: React.ReactNode;
  label: string;
  pattern?: string;
}

/**
 * 左侧导航菜单组件 - 显示聊天、会话、配置三个入口
 */
const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, onToggleCollapse }) => {
  const location = useLocation();
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  /**
   * 导航项配置 - 使用 useMemo 避免每次渲染重新创建数组
   */
  const navItems = useMemo<NavItem[]>(
    () => [
      {
        path: "/chat",
        icon: <MessageCircleMore size={22} />,
        label: "聊天",
        pattern: "/chat/*",
      },
      { path: "/conversations", icon: <FolderOpen size={22} />, label: "会话" },
      { path: "/memory", icon: <Brain size={22} />, label: "记忆" },
      { path: "/tools", icon: <Wrench size={22} />, label: "工具" },
      { path: "/settings", icon: <Settings size={22} />, label: "配置" },
      {
        path: "/logs",
        icon: <ScrollText size={22} />,
        label: "日志",
        pattern: "/logs/*",
      },
    ],
    [],
  );

  /**
   * 判断导航项是否激活 - 使用 useMemo 优化避免不必要的重计算
   */
  const activeItem = useMemo(() => {
    const currentPath = location.pathname;

    for (const item of navItems) {
      if (item.pattern) {
        if (matchPath(item.pattern, currentPath)) {
          return item.path;
        }
      } else if (currentPath === item.path) {
        return item.path;
      }
    }

    if (currentPath === "/") {
      return "/chat";
    }

    return null;
  }, [location, navItems]);

  return (
    <div
      className="h-full flex flex-col glass-card overflow-hidden relative sidebar-container"
      style={{
        borderRight: "1px solid var(--glass-border)",
        width: isCollapsed ? 72 : 240,
        transition: "width 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
        flexShrink: 0,
      }}
    >
      <div
        className="p-4 flex-shrink-0 flex items-center justify-between"
        style={{ borderBottom: "1px solid var(--glass-border)" }}
      >
        {!isCollapsed && (
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-primary-dark flex items-center justify-center">
              <Bot size={18} className="text-white" />
            </div>
            <span
              className="text-lg font-semibold"
              style={{ color: "var(--text-primary)" }}
            >
              MyClaw
            </span>
          </div>
        )}

        <button
          onClick={onToggleCollapse}
          className={`p-2.5 rounded-xl glass transition-colors hover:bg-white/10 ${isCollapsed ? "mx-auto" : ""}`}
          style={{ color: "var(--text-secondary)" }}
          aria-label={isCollapsed ? "展开侧边栏" : "折叠侧边栏"}
        >
          {isCollapsed ? <PanelLeft size={20} /> : <PanelLeftClose size={20} />}
        </button>
      </div>

      <nav className="flex-1 p-3 space-y-2">
        {navItems.map((item) => {
          const active = activeItem === item.path;
          return (
            <div key={item.path} className="relative">
              <NavLink
                to={item.path}
                onMouseEnter={() => setHoveredItem(item.path)}
                onMouseLeave={() => setHoveredItem(null)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative ${
                  isCollapsed ? "justify-center" : ""
                } ${
                  active
                    ? "bg-gradient-to-r from-primary/20 to-primary-dark/20"
                    : "hover:bg-white/5"
                }`}
                style={{
                  color: active ? "var(--primary)" : "var(--text-secondary)",
                }}
              >
                <span className={active ? "text-primary" : ""}>
                  {item.icon}
                </span>

                {!isCollapsed && (
                  <span className="text-sm font-medium">{item.label}</span>
                )}
              </NavLink>

              {isCollapsed && hoveredItem === item.path && (
                <div
                  className="absolute left-full top-1/2 -translate-y-1/2 ml-3 px-3 py-2 rounded-lg text-sm whitespace-nowrap z-50"
                  style={{
                    backgroundColor: "var(--glass-bg)",
                    border: "1px solid var(--glass-border)",
                    color: "var(--text-primary)",
                    boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
                  }}
                >
                  {item.label}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      <div
        className="p-4 flex-shrink-0"
        style={{ borderTop: "1px solid var(--glass-border)" }}
      >
        <div
          className={`flex items-center ${isCollapsed ? "justify-center" : "justify-between"} text-xs`}
          style={{ color: "var(--text-muted)" }}
        >
          {!isCollapsed && <span>AI对话助手</span>}
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            {!isCollapsed && <span>在线</span>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
