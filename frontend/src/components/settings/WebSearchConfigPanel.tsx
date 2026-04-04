import { useState } from "react";
import { ExternalLink, Eye, EyeOff } from "lucide-react";

import type { WebSearchConfig } from "../../services/api";
import { Switch } from "../admin";

interface WebSearchConfigPanelProps {
  config: WebSearchConfig;
  onChange: (key: keyof WebSearchConfig, value: string | boolean | number) => void;
  onSaveKey: (key: keyof WebSearchConfig, value: string) => Promise<void>;
  tavilyApiKeySet: boolean;
}

const sliderBackground = (percent: number) =>
  `linear-gradient(to right, var(--accent) 0%, var(--accent) ${percent}%, var(--panel-border) ${percent}%, var(--panel-border) 100%)`;

const WebSearchConfigPanel: React.FC<WebSearchConfigPanelProps> = ({ config, onChange, onSaveKey, tavilyApiKeySet }) => {
  const [showTavilyKey, setShowTavilyKey] = useState(false);

  return (
    <div className="settings-block">
      <div className="settings-block__head">
        <h3>联网搜索</h3>
        <span>外部检索</span>
      </div>

      <div className="settings-retrieval-grid">
        <div className="settings-retrieval-cell">
          <div className="settings-retrieval-cell__title">连接配置</div>
          <div className="settings-stack">
            <div className="settings-field">
              <label>提供方</label>
              <select className="admin-select w-full px-3 py-2.5" value={config.provider} onChange={(e) => onChange("provider", e.target.value)}>
                <option value="tavily">Tavily</option>
              </select>
            </div>
            <div className="settings-field">
              <label>Tavily API Key</label>
              <div className="relative">
                <input
                  type={showTavilyKey ? "text" : "password"}
                  value={config.tavily_api_key || ""}
                  onChange={(e) => onChange("tavily_api_key", e.target.value)}
                  onBlur={() => void (config.tavily_api_key?.trim() && onSaveKey("tavily_api_key", config.tavily_api_key))}
                  className="admin-input w-full px-3 py-2.5 pr-10"
                  placeholder={tavilyApiKeySet ? "已配置，重新输入将覆盖" : "输入后自动保存"}
                />
                <button type="button" className="absolute right-2 top-1/2 -translate-y-1/2 p-1" onClick={() => setShowTavilyKey((prev) => !prev)} style={{ color: "var(--text-muted)" }}>
                  {showTavilyKey ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
              <a href="https://tavily.com" target="_blank" rel="noreferrer" className="settings-link">
                <ExternalLink size={12} />
                获取密钥
              </a>
            </div>
          </div>
        </div>

        <div className="settings-retrieval-cell">
          <div className="settings-retrieval-cell__title">搜索行为</div>
          <div className="settings-stack">
            <div className="settings-field">
              <label>深度</label>
              <select className="admin-select w-full px-3 py-2.5" value={config.search_depth} onChange={(e) => onChange("search_depth", e.target.value)}>
                <option value="basic">标准</option>
                <option value="advanced">深入</option>
              </select>
            </div>
            <div className="settings-inlineToggle">
              <div>
                <div className="settings-inlineToggle__title">答案摘要</div>
                <div className="settings-inlineToggle__desc">为搜索结果附带简要总结</div>
              </div>
              <Switch checked={config.include_answer} onChange={(checked) => onChange("include_answer", checked)} ariaLabel="切换答案摘要" />
            </div>
          </div>
        </div>

        <div className="settings-retrieval-cell">
          <div className="settings-retrieval-cell__title">结果控制</div>
          <div className="settings-sliderList">
            <div>
              <div className="settings-sliderHead"><label>结果数</label><span>{config.max_results}</span></div>
              <input type="range" min="1" max="10" value={config.max_results} onChange={(e) => onChange("max_results", Number.parseInt(e.target.value, 10))} className="settings-range" style={{ background: sliderBackground(((config.max_results - 1) / 9) * 100) }} />
            </div>
            <div>
              <div className="settings-sliderHead"><label>超时</label><span>{config.timeout_seconds}s</span></div>
              <input type="range" min="10" max="60" step="5" value={config.timeout_seconds} onChange={(e) => onChange("timeout_seconds", Number.parseInt(e.target.value, 10))} className="settings-range" style={{ background: sliderBackground(((config.timeout_seconds - 10) / 50) * 100) }} />
            </div>
          </div>
        </div>

        <div className="settings-retrieval-cell">
          <div className="settings-retrieval-cell__title">缓存策略</div>
          <div className="settings-sliderList">
            <div>
              <div className="settings-sliderHead"><label>缓存时长</label><span>{config.cache_ttl_minutes}m</span></div>
              <input type="range" min="1" max="60" value={config.cache_ttl_minutes} onChange={(e) => onChange("cache_ttl_minutes", Number.parseInt(e.target.value, 10))} className="settings-range" style={{ background: sliderBackground(((config.cache_ttl_minutes - 1) / 59) * 100) }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WebSearchConfigPanel;
