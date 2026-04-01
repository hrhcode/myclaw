import { AlertTriangle, Monitor } from "lucide-react";
import type { BrowserConfig } from "../../services/api";
import { SectionCard, Switch } from "../admin";

interface BrowserConfigPanelProps {
  config: BrowserConfig;
  onChange: (key: keyof BrowserConfig, value: string | boolean | number) => void;
}

const sliderBackground = (percent: number) =>
  `linear-gradient(to right, var(--accent) 0%, var(--accent) ${percent}%, var(--panel-border) ${percent}%, var(--panel-border) 100%)`;

const BrowserConfigPanel: React.FC<BrowserConfigPanelProps> = ({ config, onChange }) => {
  return (
    <SectionCard className="p-5">
      <div className="flex items-center gap-2 mb-4">
        <span className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: "var(--surface-subtle)" }}>
          <Monitor size={16} />
        </span>
        <div>
          <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            浏览器自动化配置
          </h2>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            参数修改后自动保存
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="space-y-3">
          <div>
            <label className="block text-sm mb-1" style={{ color: "var(--text-secondary)" }}>
              默认浏览器内核
            </label>
            <select className="admin-select w-full px-3 py-2.5" value={config.default_type} onChange={(e) => onChange("default_type", e.target.value)}>
              <option value="chromium">Chromium</option>
              <option value="firefox">Firefox</option>
              <option value="webkit">WebKit</option>
            </select>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm" style={{ color: "var(--text-secondary)" }}>
                使用系统浏览器
              </label>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                优先使用本机已安装浏览器
              </p>
            </div>
            <Switch
              checked={config.use_system_browser}
              onChange={(checked) => onChange("use_system_browser", checked)}
              ariaLabel="切换系统浏览器"
            />
          </div>

          {config.use_system_browser ? (
            <div>
              <label className="block text-sm mb-1" style={{ color: "var(--text-secondary)" }}>
                浏览器通道
              </label>
              <select
                className="admin-select w-full px-3 py-2.5"
                value={config.system_browser_channel}
                onChange={(e) => onChange("system_browser_channel", e.target.value)}
              >
                <option value="chrome">Google Chrome</option>
                <option value="msedge">Microsoft Edge</option>
                <option value="firefox">Firefox</option>
              </select>
            </div>
          ) : null}

          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm" style={{ color: "var(--text-secondary)" }}>
                无头模式
              </label>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                在后台运行浏览器窗口
              </p>
            </div>
            <Switch
              checked={config.headless}
              onChange={(checked) => onChange("headless", checked)}
              ariaLabel="切换无头模式"
            />
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm" style={{ color: "var(--text-secondary)" }}>
                视口宽度
              </label>
              <span className="text-xs font-mono" style={{ color: "var(--text-primary)" }}>
                {config.viewport_width}px
              </span>
            </div>
            <input
              type="range"
              min="800"
              max="1920"
              value={config.viewport_width}
              onChange={(e) => onChange("viewport_width", Number.parseInt(e.target.value, 10))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{ background: sliderBackground(((config.viewport_width - 800) / 1120) * 100) }}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm" style={{ color: "var(--text-secondary)" }}>
                视口高度
              </label>
              <span className="text-xs font-mono" style={{ color: "var(--text-primary)" }}>
                {config.viewport_height}px
              </span>
            </div>
            <input
              type="range"
              min="600"
              max="1080"
              value={config.viewport_height}
              onChange={(e) => onChange("viewport_height", Number.parseInt(e.target.value, 10))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{ background: sliderBackground(((config.viewport_height - 600) / 480) * 100) }}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm" style={{ color: "var(--text-secondary)" }}>
                操作超时
              </label>
              <span className="text-xs font-mono" style={{ color: "var(--text-primary)" }}>
                {config.timeout_ms / 1000}s
              </span>
            </div>
            <input
              type="range"
              min="5000"
              max="60000"
              step="1000"
              value={config.timeout_ms}
              onChange={(e) => onChange("timeout_ms", Number.parseInt(e.target.value, 10))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{ background: sliderBackground(((config.timeout_ms - 5000) / 55000) * 100) }}
            />
          </div>
        </div>
      </div>

      <div className="mt-4 pt-4" style={{ borderTop: "1px solid var(--panel-border)" }}>
        <div className="flex items-center justify-between mb-2">
          <div>
            <label className="text-sm" style={{ color: "var(--text-secondary)" }}>
              允许访问内网地址
            </label>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              仅在可信网络环境启用
            </p>
          </div>
          <div className="inline-flex items-center gap-2">
            {config.ssrf_allow_private ? <AlertTriangle size={14} style={{ color: "#d97706" }} /> : null}
            <Switch
              checked={config.ssrf_allow_private}
              onChange={(checked) => onChange("ssrf_allow_private", checked)}
              ariaLabel="切换内网访问"
            />
          </div>
        </div>

        <div className="mt-3">
          <label className="block text-sm mb-1" style={{ color: "var(--text-secondary)" }}>
            SSRF 白名单（逗号分隔）
          </label>
          <textarea
            className="admin-input w-full px-3 py-2.5 resize-none"
            rows={3}
            placeholder="https://example.com, https://api.example.com"
            value={config.ssrf_whitelist}
            onChange={(e) => onChange("ssrf_whitelist", e.target.value)}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-3">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm" style={{ color: "var(--text-secondary)" }}>
                最大实例数
              </label>
              <span className="text-xs font-mono" style={{ color: "var(--text-primary)" }}>
                {config.max_instances}
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="5"
              value={config.max_instances}
              onChange={(e) => onChange("max_instances", Number.parseInt(e.target.value, 10))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{ background: sliderBackground(((config.max_instances - 1) / 4) * 100) }}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm" style={{ color: "var(--text-secondary)" }}>
                空闲超时
              </label>
              <span className="text-xs font-mono" style={{ color: "var(--text-primary)" }}>
                {config.idle_timeout_ms / 1000}s
              </span>
            </div>
            <input
              type="range"
              min="60000"
              max="600000"
              step="60000"
              value={config.idle_timeout_ms}
              onChange={(e) => onChange("idle_timeout_ms", Number.parseInt(e.target.value, 10))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{ background: sliderBackground(((config.idle_timeout_ms - 60000) / 540000) * 100) }}
            />
          </div>
        </div>
      </div>
    </SectionCard>
  );
};

export default BrowserConfigPanel;
