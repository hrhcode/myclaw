import { useState } from "react";
import { ExternalLink, Eye, EyeOff, Globe } from "lucide-react";
import type { WebSearchConfig } from "../../services/api";
import { SectionCard, Switch } from "../admin";

interface WebSearchConfigPanelProps {
  config: WebSearchConfig;
  onChange: (key: keyof WebSearchConfig, value: string | boolean | number) => void;
  onSaveKey: (key: keyof WebSearchConfig, value: string) => Promise<void>;
  tavilyApiKeySet: boolean;
}

const sliderBackground = (percent: number) =>
  `linear-gradient(to right, var(--accent) 0%, var(--accent) ${percent}%, var(--panel-border) ${percent}%, var(--panel-border) 100%)`;

const WebSearchConfigPanel: React.FC<WebSearchConfigPanelProps> = ({
  config,
  onChange,
  onSaveKey,
  tavilyApiKeySet,
}) => {
  const [showTavilyKey, setShowTavilyKey] = useState(false);

  const handleKeyBlur = async () => {
    if (config.tavily_api_key?.trim()) {
      try {
        await onSaveKey("tavily_api_key", config.tavily_api_key);
      } catch (error) {
        console.error("Failed to save tavily_api_key:", error);
      }
    }
  };

  return (
    <SectionCard className="p-5">
      <div className="flex items-center gap-2 mb-4">
        <span className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: "var(--surface-subtle)" }}>
          <Globe size={16} />
        </span>
        <div>
          <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            联网搜索配置
          </h2>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            搜索参数实时保存，API Key 失焦保存
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="space-y-3">
          <div>
            <label className="block text-sm mb-1" style={{ color: "var(--text-secondary)" }}>
              搜索提供商
            </label>
            <select className="admin-select w-full px-3 py-2.5" value={config.provider} onChange={(e) => onChange("provider", e.target.value)}>
              <option value="tavily">Tavily</option>
            </select>
          </div>

          <div>
            <label className="block text-sm mb-1" style={{ color: "var(--text-secondary)" }}>
              Tavily API Key
            </label>
            <div className="relative">
              <input
                type={showTavilyKey ? "text" : "password"}
                value={config.tavily_api_key || ""}
                onChange={(e) => onChange("tavily_api_key", e.target.value)}
                onBlur={handleKeyBlur}
                className="admin-input w-full px-3 py-2.5 pr-10"
                placeholder={tavilyApiKeySet ? "已设置，输入可覆盖" : "输入后失焦自动保存"}
              />
              <button
                type="button"
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1"
                onClick={() => setShowTavilyKey((prev) => !prev)}
                style={{ color: "var(--text-muted)" }}
              >
                {showTavilyKey ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            <a
              href="https://tavily.com"
              target="_blank"
              rel="noreferrer"
              className="mt-1 inline-flex items-center gap-1 text-xs"
              style={{ color: "var(--accent)" }}
            >
              <ExternalLink size={12} />
              获取 Tavily API Key
            </a>
          </div>

          <div>
            <label className="block text-sm mb-1" style={{ color: "var(--text-secondary)" }}>
              搜索深度
            </label>
            <select className="admin-select w-full px-3 py-2.5" value={config.search_depth} onChange={(e) => onChange("search_depth", e.target.value)}>
              <option value="basic">Basic（快速）</option>
              <option value="advanced">Advanced（更深）</option>
            </select>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm" style={{ color: "var(--text-secondary)" }}>
                生成答案摘要
              </label>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                由 Tavily 提供答案总结
              </p>
            </div>
            <Switch
              checked={config.include_answer}
              onChange={(checked) => onChange("include_answer", checked)}
              ariaLabel="切换答案摘要"
            />
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm" style={{ color: "var(--text-secondary)" }}>
                结果数量
              </label>
              <span className="text-xs font-mono" style={{ color: "var(--text-primary)" }}>
                {config.max_results}
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              value={config.max_results}
              onChange={(e) => onChange("max_results", Number.parseInt(e.target.value, 10))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{ background: sliderBackground(((config.max_results - 1) / 9) * 100) }}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm" style={{ color: "var(--text-secondary)" }}>
                请求超时（秒）
              </label>
              <span className="text-xs font-mono" style={{ color: "var(--text-primary)" }}>
                {config.timeout_seconds}s
              </span>
            </div>
            <input
              type="range"
              min="10"
              max="60"
              step="5"
              value={config.timeout_seconds}
              onChange={(e) => onChange("timeout_seconds", Number.parseInt(e.target.value, 10))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{ background: sliderBackground(((config.timeout_seconds - 10) / 50) * 100) }}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm" style={{ color: "var(--text-secondary)" }}>
                缓存时长（分钟）
              </label>
              <span className="text-xs font-mono" style={{ color: "var(--text-primary)" }}>
                {config.cache_ttl_minutes}
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="60"
              value={config.cache_ttl_minutes}
              onChange={(e) => onChange("cache_ttl_minutes", Number.parseInt(e.target.value, 10))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{ background: sliderBackground(((config.cache_ttl_minutes - 1) / 59) * 100) }}
            />
          </div>
        </div>
      </div>
    </SectionCard>
  );
};

export default WebSearchConfigPanel;
