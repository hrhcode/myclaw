import React from "react";
import { Globe, Eye, EyeOff, ExternalLink } from "lucide-react";
import type { WebSearchConfig } from "../../services/api";

interface WebSearchConfigPanelProps {
  config: WebSearchConfig;
  onChange: (
    key: keyof WebSearchConfig,
    value: string | boolean | number,
  ) => void;
  onSaveKey: (key: keyof WebSearchConfig, value: string) => Promise<void>;
  tavilyApiKeySet: boolean;
}

/**
 * 网络搜索配置面板组件
 * 仅支持 Tavily 搜索引擎
 * 实时保存配置，API Key 在失焦时保存
 */
const WebSearchConfigPanel: React.FC<WebSearchConfigPanelProps> = ({
  config,
  onChange,
  onSaveKey,
  tavilyApiKeySet,
}) => {
  const [showTavilyKey, setShowTavilyKey] = React.useState(false);

  const providers = [
    { id: "tavily", name: "Tavily", description: "专为 AI 应用设计的搜索引擎" },
  ];

  const currentProvider = providers.find((p) => p.id === config.provider);

  /**
   * 处理 API Key 输入框失焦事件
   */
  const handleKeyBlur = async (value: string) => {
    if (value.trim()) {
      try {
        await onSaveKey("tavily_api_key", value);
      } catch (error) {
        console.error(`Failed to save tavily_api_key:`, error);
      }
    }
  };

  return (
    <div
      className="glass-card rounded-2xl p-6"
      style={{ border: "1px solid var(--glass-border)" }}
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500/20 to-green-700/20 flex items-center justify-center">
          <Globe size={20} className="text-green-400" />
        </div>
        <div>
          <h2
            className="text-lg font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            网络搜索配置
          </h2>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            配置网络搜索服务（配置自动保存）
          </p>
        </div>
      </div>

      <div className="space-y-5">
        <div>
          <label
            className="block text-sm font-medium mb-2"
            style={{ color: "var(--text-secondary)" }}
          >
            搜索引擎提供商
          </label>
          <select
            value={config.provider}
            onChange={(e) => onChange("provider", e.target.value)}
            className="w-full px-4 py-3 glass-input rounded-xl appearance-none cursor-pointer"
            style={{
              color: "var(--text-primary)",
              backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='${encodeURIComponent("var(--text-muted)")}'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
              backgroundRepeat: "no-repeat",
              backgroundPosition: "right 1rem center",
              backgroundSize: "1.5rem",
            }}
          >
            {providers.map((provider) => (
              <option key={provider.id} value={provider.id}>
                {provider.name}
              </option>
            ))}
          </select>
          {currentProvider && (
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              {currentProvider.description}
            </p>
          )}
        </div>

        <div>
          <label
            className="block text-sm font-medium mb-2"
            style={{ color: "var(--text-secondary)" }}
          >
            Tavily API Key
          </label>
          <div className="relative">
            <input
              type={showTavilyKey ? "text" : "password"}
              value={config.tavily_api_key || ""}
              onChange={(e) => onChange("tavily_api_key", e.target.value)}
              onBlur={() => handleKeyBlur(config.tavily_api_key || "")}
              placeholder={
                tavilyApiKeySet
                  ? "••••••••••••••••（已设置）"
                  : "请输入您的 Tavily API Key"
              }
              className="w-full px-4 py-3 pr-12 glass-input rounded-xl"
              style={{ color: "var(--text-primary)" }}
            />
            <button
              type="button"
              onClick={() => setShowTavilyKey(!showTavilyKey)}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 transition-colors"
              style={{ color: "var(--text-muted)" }}
            >
              {showTavilyKey ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          <div className="mt-2 flex items-center gap-1">
            <ExternalLink size={12} style={{ color: "var(--text-muted)" }} />
            <a
              href="https://tavily.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs hover:underline"
              style={{ color: "var(--primary)" }}
            >
              获取 API Key: tavily.com
            </a>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <label
                className="text-sm font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                搜索结果数量
              </label>
              <span
                className="text-sm font-mono"
                style={{ color: "var(--primary)" }}
              >
                {config.max_results}
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              value={config.max_results}
              onChange={(e) =>
                onChange("max_results", parseInt(e.target.value))
              }
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${
                  ((config.max_results - 1) / 9) * 100
                }%, var(--glass-border) ${
                  ((config.max_results - 1) / 9) * 100
                }%, var(--glass-border) 100%)`,
              }}
            />
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              每次搜索返回的最大结果数量
            </p>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label
                className="text-sm font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                超时时间（秒）
              </label>
              <span
                className="text-sm font-mono"
                style={{ color: "var(--primary)" }}
              >
                {config.timeout_seconds}s
              </span>
            </div>
            <input
              type="range"
              min="10"
              max="60"
              step="5"
              value={config.timeout_seconds}
              onChange={(e) =>
                onChange("timeout_seconds", parseInt(e.target.value))
              }
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${
                  ((config.timeout_seconds - 10) / 50) * 100
                }%, var(--glass-border) ${
                  ((config.timeout_seconds - 10) / 50) * 100
                }%, var(--glass-border) 100%)`,
              }}
            />
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              搜索请求超时时间
            </p>
          </div>
        </div>

        <div>
          <label
            className="block text-sm font-medium mb-2"
            style={{ color: "var(--text-secondary)" }}
          >
            搜索深度
          </label>
          <select
            value={config.search_depth}
            onChange={(e) => onChange("search_depth", e.target.value)}
            className="w-full px-4 py-3 glass-input rounded-xl appearance-none cursor-pointer"
            style={{
              color: "var(--text-primary)",
              backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='${encodeURIComponent("var(--text-muted)")}'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
              backgroundRepeat: "no-repeat",
              backgroundPosition: "right 1rem center",
              backgroundSize: "1.5rem",
            }}
          >
            <option value="basic">Basic - 快速搜索</option>
            <option value="advanced">Advanced - 深度搜索</option>
          </select>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <label
              className="text-sm font-medium"
              style={{ color: "var(--text-secondary)" }}
            >
              启用 AI 生成答案
            </label>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              让 Tavily AI 为搜索结果生成摘要答案
            </p>
          </div>
          <button
            onClick={() => onChange("include_answer", !config.include_answer)}
            className={`relative w-12 h-6 rounded-full transition-colors ${
              config.include_answer
                ? "bg-gradient-to-r from-primary to-primary-dark"
                : "bg-gray-600"
            }`}
          >
            <span
              className={`block w-4 h-4 rounded-full bg-white shadow-md transition-transform absolute top-1 ${
                config.include_answer ? "left-[calc(100%-1.25rem)]" : "left-1"
              }`}
            />
          </button>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <label
              className="text-sm font-medium"
              style={{ color: "var(--text-secondary)" }}
            >
              缓存时间（分钟）
            </label>
            <span
              className="text-sm font-mono"
              style={{ color: "var(--primary)" }}
            >
              {config.cache_ttl_minutes} 分钟
            </span>
          </div>
          <input
            type="range"
            min="1"
            max="60"
            value={config.cache_ttl_minutes}
            onChange={(e) =>
              onChange("cache_ttl_minutes", parseInt(e.target.value))
            }
            className="w-full h-2 rounded-lg appearance-none cursor-pointer"
            style={{
              background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${
                ((config.cache_ttl_minutes - 1) / 59) * 100
              }%, var(--glass-border) ${
                ((config.cache_ttl_minutes - 1) / 59) * 100
              }%, var(--glass-border) 100%)`,
            }}
          />
          <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
            搜索结果缓存过期时间
          </p>
        </div>
      </div>
    </div>
  );
};

export default WebSearchConfigPanel;
