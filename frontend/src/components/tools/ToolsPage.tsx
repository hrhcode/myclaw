/**
 * 工具管理页面
 * 
 * 显示所有可用工具，支持启用/禁用工具
 */
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Wrench, Settings, ToggleLeft, ToggleRight, Loader2, Clock, Info } from 'lucide-react';
import { getTools, getToolConfig, updateToolConfig, toggleTool, type ToolInfo, type ToolListResponse, type ToolConfig } from '../../services/api';

interface ToolCardProps {
  tool: ToolInfo;
  onToggle: (name: string, enabled: boolean) => void;
}

/**
 * 工具卡片组件
 */
const ToolCard: React.FC<ToolCardProps> = ({ tool, onToggle }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-4 rounded-xl"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="font-medium" style={{ color: 'var(--text-primary)' }}>
              {tool.name}
            </h3>
            {tool.enabled ? (
              <span className="px-2 py-0.5 text-xs rounded-full bg-green-500/20 text-green-500">
                已启用
              </span>
            ) : (
              <span className="px-2 py-0.5 text-xs rounded-full bg-red-500/20 text-red-500">
                已禁用
              </span>
            )}
          </div>
          <p className="text-sm mb-3" style={{ color: 'var(--text-muted)' }}>
            {tool.description}
          </p>
          {Object.keys(tool.parameters?.properties || {}).length > 0 && (
            <div className="mt-2">
              <div className="flex items-center gap-1 text-xs mb-1" style={{ color: 'var(--text-muted)' }}>
                <Info size={12} />
                <span>参数</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {Object.entries(tool.parameters?.properties || {}).map(([key, prop]) => (
                  <span
                    key={key}
                    className="px-2 py-0.5 text-xs rounded"
                    style={{
                      background: 'var(--glass-bg)',
                      color: 'var(--text-muted)',
                      border: '1px solid var(--glass-border)'
                    }}
                  >
                    {key}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
        <button
          onClick={() => onToggle(tool.name, !tool.enabled)}
          className="p-2 rounded-lg transition-colors"
          style={{
            background: tool.enabled ? 'var(--primary)' : 'var(--glass-bg)',
            border: '1px solid var(--glass-border)'
          }}
        >
          {tool.enabled ? (
            <ToggleRight size={20} className="text-white" />
          ) : (
            <ToggleLeft size={20} style={{ color: 'var(--text-muted)' }} />
          )}
        </button>
      </div>
    </motion.div>
  );
};

/**
 * 工具管理页面组件
 */
const ToolsPage: React.FC = () => {
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [config, setConfig] = useState<ToolConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * 加载工具列表和配置
   */
  const loadData = async () => {
    try {
      setLoading(true);
      const [toolsResponse, configResponse] = await Promise.all([
        getTools(),
        getToolConfig()
      ]);
      setTools(toolsResponse.tools);
      setConfig(configResponse);
      setError(null);
    } catch (err) {
      setError('加载工具列表失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  /**
   * 切换工具启用状态
   */
  const handleToggleTool = async (name: string, enabled: boolean) => {
    try {
      await toggleTool(name, enabled);
      setTools(prev => prev.map(tool => 
        tool.name === name ? { ...tool, enabled } : tool
      ));
    } catch (err) {
      console.error('切换工具状态失败:', err);
    }
  };

  /**
   * 更新工具配置
   */
  const handleUpdateConfig = async (updates: Partial<ToolConfig>) => {
    try {
      await updateToolConfig(updates);
      setConfig(prev => prev ? { ...prev, ...updates } : null);
    } catch (err) {
      console.error('更新配置失败:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <p style={{ color: 'var(--text-muted)' }}>{error}</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-primary/20 to-primary-dark/20">
          <Wrench size={20} className="text-primary" />
        </div>
        <div>
          <h1 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
            工具管理
          </h1>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            管理 AI 可调用的工具
          </p>
        </div>
      </div>

      {/* 工具配置 */}
      {config && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-4 rounded-xl"
        >
          <div className="flex items-center gap-2 mb-4">
            <Settings size={18} className="text-primary" />
            <h2 className="font-medium" style={{ color: 'var(--text-primary)' }}>
              全局配置
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm mb-1 block" style={{ color: 'var(--text-muted)' }}>
                配置文件
              </label>
              <select
                value={config.profile}
                onChange={(e) => handleUpdateConfig({ profile: e.target.value })}
                className="w-full px-3 py-2 rounded-lg"
                style={{
                  background: 'var(--glass-bg)',
                  border: '1px solid var(--glass-border)',
                  color: 'var(--text-primary)'
                }}
              >
                <option value="minimal">minimal - 最小工具集</option>
                <option value="standard">standard - 标准工具集</option>
                <option value="full">full - 完整工具集</option>
              </select>
            </div>
            <div>
              <label className="text-sm mb-1 block" style={{ color: 'var(--text-muted)' }}>
                最大迭代次数
              </label>
              <input
                type="number"
                value={config.max_iterations}
                onChange={(e) => handleUpdateConfig({ max_iterations: parseInt(e.target.value) || 5 })}
                min={1}
                max={10}
                className="w-full px-3 py-2 rounded-lg"
                style={{
                  background: 'var(--glass-bg)',
                  border: '1px solid var(--glass-border)',
                  color: 'var(--text-primary)'
                }}
              />
            </div>
            <div>
              <label className="text-sm mb-1 block" style={{ color: 'var(--text-muted)' }}>
                超时时间（秒）
              </label>
              <input
                type="number"
                value={config.timeout_seconds}
                onChange={(e) => handleUpdateConfig({ timeout_seconds: parseInt(e.target.value) || 30 })}
                min={5}
                max={120}
                className="w-full px-3 py-2 rounded-lg"
                style={{
                  background: 'var(--glass-bg)',
                  border: '1px solid var(--glass-border)',
                  color: 'var(--text-primary)'
                }}
              />
            </div>
          </div>
        </motion.div>
      )}

      {/* 工具列表 */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Clock size={18} className="text-primary" />
          <h2 className="font-medium" style={{ color: 'var(--text-primary)' }}>
            可用工具 ({tools.length})
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {tools.map(tool => (
            <ToolCard
              key={tool.name}
              tool={tool}
              onToggle={handleToggleTool}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default ToolsPage;
