import { useMemo } from "react";
import { matchPath, NavLink, useLocation } from "react-router-dom";
import {
  Database,
  Clock3,
  Logs,
  Menu,
  MessageCircleMore,
  MessageSquare,
  PlugZap,
  ScrollText,
  Settings,
  Wrench,
} from "lucide-react";

interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  pattern?: string;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, onToggleCollapse }) => {
  const location = useLocation();

  const navGroups = useMemo<NavGroup[]>(
    () => [
      {
        title: "聊天",
        items: [
          {
            path: "/chat",
            label: "聊天",
            icon: <MessageCircleMore size={20} />,
            pattern: "/chat/*",
          },
        ],
      },
      {
        title: "控制",
        items: [
          {
            path: "/conversations",
            label: "会话",
            icon: <MessageSquare size={20} />,
          },
          {
            path: "/rules",
            label: "规则",
            icon: <ScrollText size={20} />,
          },
          {
            path: "/knowledge",
            label: "知识库",
            icon: <Database size={20} />,
          },
          {
            path: "/automations",
            label: "自动化",
            icon: <Clock3 size={20} />,
          },
        ],
      },
      {
        title: "设置",
        items: [
          {
            path: "/tools",
            label: "工具",
            icon: <Wrench size={20} />,
          },
          {
            path: "/mcp",
            label: "MCP",
            icon: <PlugZap size={20} />,
          },
          {
            path: "/settings",
            label: "配置",
            icon: <Settings size={20} />,
          },
          {
            path: "/logs",
            label: "日志",
            icon: <Logs size={20} />,
            pattern: "/logs/*",
          },
        ],
      },
    ],
    [],
  );

  const activePath = useMemo(() => {
    const currentPath = location.pathname;
    for (const group of navGroups) {
      for (const item of group.items) {
        if (item.pattern && matchPath(item.pattern, currentPath)) {
          return item.path;
        }
        if (currentPath === item.path) {
          return item.path;
        }
      }
    }
    return currentPath === "/" ? "/chat" : null;
  }, [location.pathname, navGroups]);

  return (
    <aside className={`nav ${isCollapsed ? "nav--collapsed" : ""}`}>
      <div className={`nav-brand ${isCollapsed ? "nav-brand--collapsed" : ""}`}>
        {isCollapsed ? (
          <button
            className="nav-toggle-btn nav-toggle-btn--centered"
            onClick={onToggleCollapse}
            title="展开导航"
            aria-label="展开导航"
          >
            <Menu size={20} />
          </button>
        ) : (
          <>
            <div className="brand-logo">
              <img src="/myclaw.svg" alt="MyClaw" width={24} height={24} />
            </div>
            <div className="brand-text">
              <div className="brand-title">MyClaw</div>
            </div>
            <button
              className="nav-toggle-btn"
              onClick={onToggleCollapse}
              title="收起导航"
              aria-label="收起导航"
            >
              <Menu size={20} />
            </button>
          </>
        )}
      </div>
      {navGroups.map((group) => (
        <div className="nav-group" key={group.title}>
          <div className="nav-label nav-label--static">
            <span className="nav-label__text">{group.title}</span>
          </div>
          <div className="nav-group__items">
            {group.items.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={`nav-item ${activePath === item.path ? "active" : ""}`}
                title={item.label}
              >
                <span className="nav-item__icon">{item.icon}</span>
                <span className="nav-item__text">{item.label}</span>
              </NavLink>
            ))}
          </div>
        </div>
      ))}
    </aside>
  );
};

export default Sidebar;
