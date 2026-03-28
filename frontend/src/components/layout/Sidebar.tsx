import { NavLink, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import {
  MessageSquare,
  FolderOpen,
  Settings,
  PanelLeftClose,
  PanelLeft,
} from "lucide-react";
import { useState } from "react";

interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

interface NavItem {
  path: string;
  icon: React.ReactNode;
  label: string;
}

/**
 * 左侧导航菜单组件 - 显示聊天、会话、配置三个入口
 */
const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, onToggleCollapse }) => {
  const location = useLocation();
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  const navItems: NavItem[] = [
    { path: "/chat", icon: <MessageSquare size={22} />, label: "聊天" },
    { path: "/conversations", icon: <FolderOpen size={22} />, label: "会话" },
    { path: "/settings", icon: <Settings size={22} />, label: "配置" },
  ];

  /**
   * 判断导航项是否激活
   */
  const isActive = (path: string): boolean => {
    if (path === "/chat") {
      return (
        location.pathname === "/chat" ||
        location.pathname.startsWith("/chat/") ||
        location.pathname === "/"
      );
    }
    return location.pathname === path;
  };

  return (
    <div
      className="h-full flex flex-col glass-card overflow-hidden relative sidebar-container"
      style={{
        borderRight: "1px solid var(--glass-border)",
        width: isCollapsed ? 72 : 240,
        transition: "width 0.3s ease",
      }}
    >
      <div
        className="p-4 flex-shrink-0 flex items-center justify-between"
        style={{ borderBottom: "1px solid var(--glass-border)" }}
      >
        {!isCollapsed && (
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-primary-dark flex items-center justify-center">
              <MessageSquare size={18} className="text-white" />
            </div>
            <span
              className="text-lg font-semibold"
              style={{ color: "var(--text-primary)" }}
            >
              AI助手
            </span>
          </div>
        )}

        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={onToggleCollapse}
          className={`p-2.5 rounded-xl glass transition-colors ${isCollapsed ? "mx-auto" : ""}`}
          style={{ color: "var(--text-secondary)" }}
          aria-label={isCollapsed ? "展开侧边栏" : "折叠侧边栏"}
        >
          {isCollapsed ? <PanelLeft size={20} /> : <PanelLeftClose size={20} />}
        </motion.button>
      </div>

      <nav className="flex-1 p-3 space-y-2">
        {navItems.map((item) => {
          const active = isActive(item.path);
          return (
            <div key={item.path} className="relative">
              <NavLink
                to={item.path}
                onMouseEnter={() => setHoveredItem(item.path)}
                onMouseLeave={() => setHoveredItem(null)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative ${
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

                {active && (
                  <div className="absolute left-0 top-2 bottom-2 w-1 bg-gradient-to-b from-primary to-primary-dark rounded-r-full" />
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
