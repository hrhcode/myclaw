import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Loader2, Wrench } from "lucide-react";

import MainLayout from "../layout/MainLayout";
import { getTools, toggleTool } from "../../services/api";
import type { ToolInfo } from "../../services/api";
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

          {Object.keys(tool.parameters?.properties || {}).length > 0 ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {Object.keys(tool.parameters?.properties || {}).map((key) => (
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
          ) : null}
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  if (loading) {
    return (
      <MainLayout headerTitle="工具">
        <div className="flex h-full items-center justify-center">
          <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>
            <Loader2 size={50} className="text-primary" />
          </motion.div>
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
              <div className="admin-summary-value">{tools.filter((tool) => tool.enabled).length}</div>
            </div>
          </div>

          <PageSection
            title="可用工具"
            description="按需开关工具能力，不影响现有接口行为。"
            actions={
              <div className="inline-flex items-center gap-2 text-xs" style={{ color: "var(--text-muted)" }}>
                <Wrench size={18} />
                <span>{tools.length} 项</span>
              </div>
            }
          >
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
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
