import { useMemo } from "react";
import { matchPath, NavLink, useLocation } from "react-router-dom";
import {
  BookText,
  Bot,
  Brain,
  Clock3,
  Logs,
  MessageSquare,
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

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed }) => {
  const location = useLocation();

  const navGroups = useMemo<NavGroup[]>(
    () => [
      {
        title: "聊天",
        items: [
          {
            path: "/chat",
            label: "对话",
            icon: <MessageSquare size={16} />,
            pattern: "/chat/*",
          },
        ],
      },
      {
        title: "管理",
        items: [
          {
            path: "/conversations",
            label: "会话",
            icon: <BookText size={16} />,
          },
          {
            path: "/automations",
            label: "自动化",
            icon: <Clock3 size={16} />,
          },
          {
            path: "/knowledge",
            label: "知识库",
            icon: <Brain size={16} />,
          },
        ],
      },
      {
        title: "系统",
        items: [
          {
            path: "/tools",
            label: "工具",
            icon: <Wrench size={16} />,
          },
          {
            path: "/settings",
            label: "设置",
            icon: <Settings size={16} />,
          },
          {
            path: "/logs",
            label: "日志",
            icon: <Logs size={16} />,
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

      <div className="nav-group">
        <div className="nav-label nav-label--static">
          <span className="nav-label__text">智能体</span>
        </div>
        <div className="nav-group__items">
          <div className="nav-item" title="MyClaw 核心">
            <span className="nav-item__icon">
              <Bot size={16} />
            </span>
            <span className="nav-item__text">MyClaw 核心</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
