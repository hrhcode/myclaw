import { useEffect, useMemo, useState } from "react";
import { ChevronDown, Loader2, Search } from "lucide-react";

import MainLayout from "../layout/MainLayout";
import { getTools, toggleTool } from "../../services/api";
import type { ToolInfo } from "../../services/api";
import { PageSection, SectionCard, SegmentedTabs, Switch } from "../admin";

interface ToolCardProps {
  tool: ToolInfo;
  onToggle: (name: string, enabled: boolean) => void;
}

const ToolCard: React.FC<ToolCardProps> = ({ tool, onToggle }) => {
  const [expanded, setExpanded] = useState(false);
  const displayDescription = (tool.description || "").replace(/^\[MCP:[^\]]+\]\s*/, "");
  const paramKeys = Object.keys((tool.parameters as Record<string, unknown>)?.properties || {});
  const hasParams = paramKeys.length > 0;

  return (
    <SectionCard className="p-4">
      <div className="flex items-start justify-between gap-4">
        <div
          className={`min-w-0 flex-1 ${hasParams ? "cursor-pointer" : ""}`}
          onClick={() => hasParams && setExpanded((v) => !v)}
        >
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              {tool.name}
            </h3>
          </div>

          {displayDescription && (
            <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>
              {displayDescription}
            </p>
          )}
        </div>

        <Switch
          checked={tool.enabled}
          onChange={(checked) => onToggle(tool.name, checked)}
          ariaLabel={`切换 ${tool.name} 状态`}
        />
      </div>

      {expanded && hasParams && (
        <div className="mt-3 flex flex-wrap gap-2">
          {paramKeys.map((key) => (
            <span
              key={key}
              className="rounded-md px-2 py-1 text-xs"
              style={{
                backgroundColor: "var(--surface-subtle)",
                color: "var(--text-secondary)",
                border: "1px solid var(--panel-border)",
              }}
            >
              {key}
            </span>
          ))}
        </div>
      )}
    </SectionCard>
  );
};

interface McpServerGroupProps {
  serverName: string;
  tools: ToolInfo[];
  onToggle: (name: string, enabled: boolean) => void;
}

const McpServerGroup: React.FC<McpServerGroupProps> = ({ serverName, tools, onToggle }) => {
  const [expanded, setExpanded] = useState(true);
  const enabledCount = tools.filter((t) => t.enabled).length;

  return (
    <div className="rounded-xl" style={{ border: "1px solid var(--glass-border)" }}>
      <button
        type="button"
        className="flex w-full items-center justify-between px-4 py-3 text-left"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            {serverName}
          </span>
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            {enabledCount}/{tools.length} 启用
          </span>
        </div>
        <ChevronDown
          size={16}
          style={{
            color: "var(--text-muted)",
            transform: expanded ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.2s",
          }}
        />
      </button>
      {expanded && (
        <div className="grid grid-cols-1 gap-2 px-3 pb-3 md:grid-cols-2">
          {tools.map((tool) => (
            <ToolCard key={tool.name} tool={tool} onToggle={onToggle} />
          ))}
        </div>
      )}
    </div>
  );
};

const ToolsPage: React.FC = () => {
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"builtin" | "mcp">("builtin");
  const [searchQuery, setSearchQuery] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      const toolsResponse = await getTools();
      setTools(toolsResponse.tools);
      setError(null);
    } catch (err) {
      setError("加载工具列表失败");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, []);

  const handleToggleTool = async (name: string, enabled: boolean) => {
    try {
      await toggleTool(name, enabled);
      setTools((prev) => prev.map((tool) => (tool.name === name ? { ...tool, enabled } : tool)));
    } catch (err) {
      console.error("切换工具状态失败", err);
    }
  };

  const builtinTools = useMemo(() => tools.filter((t) => t.source === "builtin"), [tools]);
  const mcpTools = useMemo(() => tools.filter((t) => t.source === "mcp"), [tools]);

  // 搜索过滤
  const matchesSearch = (tool: ToolInfo) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const desc = (tool.description || "").replace(/^\[MCP:[^\]]+\]\s*/, "").toLowerCase();
    return tool.name.toLowerCase().includes(q) || desc.includes(q);
  };

  const filteredBuiltin = useMemo(() => builtinTools.filter(matchesSearch), [builtinTools, searchQuery]);
  const filteredMcp = useMemo(() => mcpTools.filter(matchesSearch), [mcpTools, searchQuery]);

  // MCP 按服务器分组（过滤后）
  const mcpGroups = useMemo(() => {
    const groups = new Map<string, ToolInfo[]>();
    for (const tool of filteredMcp) {
      const key = tool.mcp_server_name || "其他 MCP";
      const list = groups.get(key);
      if (list) {
        list.push(tool);
      } else {
        groups.set(key, [tool]);
      }
    }
    return groups;
  }, [filteredMcp]);

  if (loading) {
    return (
      <MainLayout headerTitle="工具">
        <div className="flex h-full items-center justify-center">
          <Loader2 size={50} className="animate-spin text-primary" />
        </div>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout headerTitle="工具">
        <div className="flex h-full items-center justify-center">
          <p style={{ color: "var(--text-muted)" }}>{error}</p>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout headerTitle="工具">
      <div className="admin-page">
        <div className="admin-frame">
          <div className="admin-summary">
            <div className="admin-summary-card">
              <div className="admin-summary-label">工具总数</div>
              <div className="admin-summary-value">{tools.length}</div>
            </div>
            <div className="admin-summary-card">
              <div className="admin-summary-label">已启用</div>
              <div className="admin-summary-value">{tools.filter((t) => t.enabled).length}</div>
            </div>
            <div className="admin-summary-card">
              <div className="admin-summary-label">内置工具</div>
              <div className="admin-summary-value">{builtinTools.length}</div>
            </div>
            <div className="admin-summary-card">
              <div className="admin-summary-label">MCP 工具</div>
              <div className="admin-summary-value">{mcpTools.length}</div>
            </div>
          </div>

          <div className="admin-toolbar mb-4">
            <SegmentedTabs
              tabs={[
                { key: "builtin", label: `内置工具 (${builtinTools.length})` },
                { key: "mcp", label: `MCP 工具 (${mcpTools.length})` },
              ]}
              activeKey={activeTab}
              onChange={(key) => {
                setActiveTab(key as "builtin" | "mcp");
                setSearchQuery("");
              }}
            />
            <div className="relative min-w-[220px] flex-1">
              <Search
                size={20}
                className="absolute left-3 top-1/2 -translate-y-1/2"
                style={{ color: "var(--text-muted)" }}
              />
              <input
                type="text"
                className="admin-input w-full py-2.5 pl-9 pr-3"
                placeholder={activeTab === "builtin" ? "搜索内置工具…" : "搜索 MCP 工具…"}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>

          {activeTab === "builtin" ? (
            <PageSection
              title="内置工具"
              description="系统自带的工具，提供基础能力。"
              hideHeader
            >
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {filteredBuiltin.map((tool) => (
                  <ToolCard key={tool.name} tool={tool} onToggle={handleToggleTool} />
                ))}
                {filteredBuiltin.length === 0 && (
                  <div className="col-span-2 py-6 text-center text-sm" style={{ color: "var(--text-muted)" }}>
                    {searchQuery.trim() ? "没有匹配的内置工具。" : "暂无内置工具。"}
                  </div>
                )}
              </div>
            </PageSection>
          ) : (
            <PageSection
              title="MCP 工具"
              description="通过 MCP 服务集成的外部工具，可在 MCP 页面管理服务。"
              hideHeader
            >
              {mcpGroups.size > 0 ? (
                <div className="space-y-3">
                  {[...mcpGroups.entries()].map(([serverName, serverTools]) => (
                    <McpServerGroup
                      key={serverName}
                      serverName={serverName}
                      tools={serverTools}
                      onToggle={handleToggleTool}
                    />
                  ))}
                </div>
              ) : (
                <div className="py-6 text-center text-sm" style={{ color: "var(--text-muted)" }}>
                  {searchQuery.trim() ? "没有匹配的 MCP 工具。" : "暂无 MCP 工具。请先在 MCP 页面添加服务。"}
                </div>
              )}
            </PageSection>
          )}
        </div>
      </div>
    </MainLayout>
  );
};

export default ToolsPage;
