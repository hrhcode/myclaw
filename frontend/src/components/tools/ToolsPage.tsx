import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Loader2, Wrench } from "lucide-react";
import MainLayout from "../layout/MainLayout";
import {
  getTools,
  getToolConfig,
  updateToolConfig,
  toggleTool,
} from "../../services/api";
import type { ToolInfo, ToolConfig } from "../../services/api";
import { PageSection, SectionCard, StatusBadge, Switch } from "../admin";

interface ToolCardProps {
  tool: ToolInfo;
  onToggle: (name: string, enabled: boolean) => void;
}

const ToolCard: React.FC<ToolCardProps> = ({ tool, onToggle }) => {
  return (
    <SectionCard className="p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              {tool.name}
            </h3>
            <StatusBadge tone={tool.enabled ? "success" : "danger"}>
              {tool.enabled ? "启用" : "禁用"}
            </StatusBadge>
          </div>

          <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>
            {tool.description}
          </p>

          {Object.keys(tool.parameters?.properties || {}).length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {Object.keys(tool.parameters?.properties || {}).map((key) => (
                <span
                  key={key}
                  className="px-2 py-1 rounded-md text-xs"
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
        </div>

        <Switch
          checked={tool.enabled}
          onChange={(checked) => onToggle(tool.name, checked)}
          ariaLabel={`切换 ${tool.name} 状态`}
        />
      </div>
    </SectionCard>
  );
};

const ToolsPage: React.FC = () => {
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [config, setConfig] = useState<ToolConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [toolsResponse, configResponse] = await Promise.all([
        getTools(),
        getToolConfig(),
      ]);
      setTools(toolsResponse.tools);
      setConfig(configResponse);
      setError(null);
    } catch (err) {
      setError("加载工具列表失败");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleToggleTool = async (name: string, enabled: boolean) => {
    try {
      await toggleTool(name, enabled);
      setTools((prev) =>
        prev.map((tool) => (tool.name === name ? { ...tool, enabled } : tool)),
      );
    } catch (err) {
      console.error("切换工具状态失败:", err);
    }
  };

  const handleUpdateConfig = async (updates: Partial<ToolConfig>) => {
    try {
      await updateToolConfig(updates);
      setConfig((prev) => (prev ? { ...prev, ...updates } : null));
    } catch (err) {
      console.error("更新工具配置失败:", err);
    }
  };

  if (loading) {
    return (
      <MainLayout headerTitle="工具">
        <div className="h-full flex items-center justify-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          >
            <Loader2 size={40} className="text-primary" />
          </motion.div>
        </div>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout headerTitle="工具">
        <div className="h-full flex items-center justify-center">
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
              <div className="admin-summary-value">
                {tools.filter((tool) => tool.enabled).length}
              </div>
            </div>
          </div>

          {config && (
            <PageSection
              title="全局配置"
              description="配置工具集合和执行限制参数"
              tight
            >
              <SectionCard className="p-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs mb-1" style={{ color: "var(--text-muted)" }}>
                      配置档
                    </label>
                    <select
                      value={config.profile}
                      onChange={(e) => handleUpdateConfig({ profile: e.target.value })}
                      className="admin-select w-full px-3 py-2"
                    >
                      <option value="minimal">minimal - 最小工具集</option>
                      <option value="standard">standard - 标准工具集</option>
                      <option value="full">full - 完整工具集</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs mb-1" style={{ color: "var(--text-muted)" }}>
                      最大迭代次数
                    </label>
                    <input
                      type="number"
                      value={config.max_iterations}
                      min={1}
                      max={10}
                      onChange={(e) =>
                        handleUpdateConfig({
                          max_iterations: Number.parseInt(e.target.value, 10) || 5,
                        })
                      }
                      className="admin-input w-full px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-xs mb-1" style={{ color: "var(--text-muted)" }}>
                      超时秒数
                    </label>
                    <input
                      type="number"
                      value={config.timeout_seconds}
                      min={5}
                      max={120}
                      onChange={(e) =>
                        handleUpdateConfig({
                          timeout_seconds: Number.parseInt(e.target.value, 10) || 30,
                        })
                      }
                      className="admin-input w-full px-3 py-2"
                    />
                  </div>
                </div>
              </SectionCard>
            </PageSection>
          )}

          <PageSection
            title="可用工具"
            description="按需开关工具能力，不影响现有接口行为"
            actions={
              <div className="inline-flex items-center gap-2 text-xs" style={{ color: "var(--text-muted)" }}>
                <Wrench size={14} />
                <span>{tools.length} 项</span>
              </div>
            }
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {tools.map((tool) => (
                <motion.div key={tool.name} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                  <ToolCard tool={tool} onToggle={handleToggleTool} />
                </motion.div>
              ))}
            </div>
          </PageSection>
        </div>
      </div>
    </MainLayout>
  );
};

export default ToolsPage;
