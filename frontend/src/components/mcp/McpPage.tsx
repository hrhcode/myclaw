import { useEffect, useState } from "react";
import { FileJson, Loader2, Plus, RefreshCw, Trash2 } from "lucide-react";

import MainLayout from "../layout/MainLayout";
import { PageSection, SectionCard, Switch } from "../admin";
import { deleteMcpServer, getMcpServers, getMcpStats, probeAllMcpServers, toggleMcpServer } from "../../services/api";
import type { McpServer, McpStats } from "../../types";
import JsonImportDialog from "./JsonImportDialog";

interface McpCardProps {
  server: McpServer;
  onToggle: (server: McpServer, enabled: boolean) => void;
  onDelete: (server: McpServer) => void;
}

const McpCard: React.FC<McpCardProps> = ({ server, onToggle, onDelete }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <SectionCard className="p-4">
      <div className="flex items-start justify-between gap-4">
        <div
          className="min-w-0 flex-1 cursor-pointer"
          onClick={() => setExpanded((v) => !v)}
        >
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              {server.name}
            </h3>
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{
                backgroundColor: server.status === "connected" ? "#22c55e" : "#ef4444",
              }}
            />
            {server.tool_names.length > 0 && (
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                {server.tool_names.length} 个工具
              </span>
            )}
          </div>
          {server.description && (
            <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>
              {server.description}
            </p>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Switch
            checked={server.enabled}
            onChange={(checked) => onToggle(server, checked)}
            ariaLabel={`切换 ${server.name} 状态`}
          />
          <button
            type="button"
            onClick={() => onDelete(server)}
            className="btn-secondary p-1.5"
            aria-label={`删除 ${server.name}`}
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>
      {expanded && server.tool_names.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {server.tool_names.map((name) => (
            <span
              key={name}
              className="rounded-md px-2 py-0.5 text-xs"
              style={{
                backgroundColor: "var(--surface-subtle)",
                color: "var(--text-secondary)",
                border: "1px solid var(--glass-border)",
              }}
            >
              {name}
            </span>
          ))}
        </div>
      )}
    </SectionCard>
  );
};

let hasProbed = false;

const McpPage: React.FC = () => {
  const [servers, setServers] = useState<McpServer[]>([]);
  const [stats, setStats] = useState<McpStats>({ total: 0, enabled: 0, resources: 0, alerts: 0 });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showImport, setShowImport] = useState(false);

  const loadPage = async () => {
    const [serverData, statsData] = await Promise.all([getMcpServers(), getMcpStats()]);
    setServers(serverData);
    setStats(statsData);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const probed = await probeAllMcpServers();
      setServers(probed);
      setStats(await getMcpStats());
    } catch (err) {
      setError(err instanceof Error ? err.message : "刷新 MCP 服务状态失败");
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    void (async () => {
      try {
        setLoading(true);
        await loadPage();
      } catch (err) {
        setError(err instanceof Error ? err.message : "加载 MCP 服务失败");
      } finally {
        setLoading(false);
      }
      if (hasProbed) return;
      hasProbed = true;
      // 首次加载：后台探测联通状态，不阻塞页面渲染
      setRefreshing(true);
      try {
        const probed = await probeAllMcpServers();
        setServers(probed);
        setStats(await getMcpStats());
      } catch {
        // 探测失败不影响页面显示
      } finally {
        setRefreshing(false);
      }
    })();
  }, []);

  const handleToggle = async (server: McpServer, enabled: boolean) => {
    setServers((prev) => prev.map((s) => (s.id === server.id ? { ...s, enabled } : s)));
    try {
      await toggleMcpServer(server.id, enabled);
      setStats(await getMcpStats());
    } catch (err) {
      setServers((prev) => prev.map((s) => (s.id === server.id ? { ...s, enabled: !enabled } : s)));
      setError(err instanceof Error ? err.message : "切换 MCP 服务状态失败");
    }
  };

  const handleDelete = async (server: McpServer) => {
    if (!window.confirm(`确认删除 MCP 服务"${server.name}"吗？`)) return;
    try {
      await deleteMcpServer(server.id);
      await loadPage();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除 MCP 服务失败");
    }
  };

  const handleImported = () => {
    void loadPage();
  };

  if (loading) {
    return (
      <MainLayout headerTitle="MCP">
        <div className="flex h-full items-center justify-center">
          <Loader2 size={50} className="animate-spin text-primary" />
        </div>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout headerTitle="MCP">
        <div className="flex h-full items-center justify-center">
          <p style={{ color: "var(--text-muted)" }}>{error}</p>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout headerTitle="MCP">
      <div className="admin-page">
        <div className="admin-frame">
          <div className="admin-summary">
            <div className="admin-summary-card">
              <div className="admin-summary-label">MCP 服务</div>
              <div className="admin-summary-value">{stats.total}</div>
            </div>
            <div className="admin-summary-card">
              <div className="admin-summary-label">已启用</div>
              <div className="admin-summary-value">{stats.enabled}</div>
            </div>
          </div>

          <div className="admin-toolbar mb-4">
            <button
              type="button"
              onClick={() => void handleRefresh()}
              className="btn-secondary inline-flex items-center gap-2"
              disabled={refreshing}
            >
              {refreshing ? <Loader2 size={18} className="animate-spin" /> : <RefreshCw size={18} />}
              {refreshing ? "探测中…" : "刷新"}
            </button>
            <button
              type="button"
              onClick={() => setShowImport(true)}
              className="btn-primary inline-flex items-center gap-2"
            >
              <Plus size={18} />
              <FileJson size={18} />
              添加
            </button>
          </div>

          <PageSection
            title="MCP 服务"
            description="配置外部 MCP 服务，启用后即可在对话中使用。"
            actions={
              <div className="inline-flex items-center gap-2 text-xs" style={{ color: "var(--text-muted)" }}>
                <span>{servers.length} 项</span>
              </div>
            }
          >
            {servers.length > 0 ? (
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {servers.map((server) => (
                  <McpCard key={server.id} server={server} onToggle={handleToggle} onDelete={handleDelete} />
                ))}
              </div>
            ) : (
              <SectionCard className="p-6">
                <div className="text-sm" style={{ color: "var(--text-muted)" }}>
                  当前还没有 MCP 服务。点击上方「添加」通过 JSON 导入。
                </div>
              </SectionCard>
            )}
          </PageSection>
        </div>
      </div>

      <JsonImportDialog
        open={showImport}
        onClose={() => setShowImport(false)}
        onImported={handleImported}
      />
    </MainLayout>
  );
};

export default McpPage;
