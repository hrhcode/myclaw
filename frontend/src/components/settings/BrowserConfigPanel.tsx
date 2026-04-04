import { AlertTriangle } from "lucide-react";

import type { BrowserConfig } from "../../services/api";
import { Switch } from "../admin";

interface BrowserConfigPanelProps {
  config: BrowserConfig;
  wide?: boolean;
  onChange: (key: keyof BrowserConfig, value: string | boolean | number) => void;
}

const sliderBackground = (percent: number) =>
  `linear-gradient(to right, var(--accent) 0%, var(--accent) ${percent}%, var(--panel-border) ${percent}%, var(--panel-border) 100%)`;

const BrowserConfigPanel: React.FC<BrowserConfigPanelProps> = ({ config, wide, onChange }) => (
  <div className={`settings-block${wide ? " settings-block--wide" : ""}`}>
    <div className="settings-block__head">
      <h3>浏览器自动化</h3>
      <span>执行环境</span>
    </div>

    <div className="settings-retrieval-grid">
      <div className="settings-retrieval-cell">
        <div className="settings-retrieval-cell__title">浏览器引擎</div>
        <div className="settings-stack">
          <div className="settings-field">
            <label>内核</label>
            <select className="admin-select w-full px-3 py-2.5" value={config.default_type} onChange={(e) => onChange("default_type", e.target.value)}>
              <option value="chromium">Chromium</option>
              <option value="firefox">Firefox</option>
              <option value="webkit">WebKit</option>
            </select>
          </div>
          <div className="settings-inlineToggle">
            <div>
              <div className="settings-inlineToggle__title">系统浏览器</div>
              <div className="settings-inlineToggle__desc">优先复用本机浏览器</div>
            </div>
            <Switch checked={config.use_system_browser} onChange={(checked) => onChange("use_system_browser", checked)} ariaLabel="切换系统浏览器" />
          </div>
          {config.use_system_browser ? (
            <div className="settings-field">
              <label>通道</label>
              <select className="admin-select w-full px-3 py-2.5" value={config.system_browser_channel} onChange={(e) => onChange("system_browser_channel", e.target.value)}>
                <option value="chrome">Chrome</option>
                <option value="msedge">Edge</option>
                <option value="firefox">Firefox</option>
              </select>
            </div>
          ) : null}
        </div>
      </div>

      <div className="settings-retrieval-cell">
        <div className="settings-retrieval-cell__title">运行选项</div>
        <div className="settings-stack">
          <div className="settings-inlineToggle">
            <div>
              <div className="settings-inlineToggle__title">无头模式</div>
              <div className="settings-inlineToggle__desc">后台运行浏览器窗口</div>
            </div>
            <Switch checked={config.headless} onChange={(checked) => onChange("headless", checked)} ariaLabel="切换无头模式" />
          </div>
          <div className="settings-inlineToggle">
            <div>
              <div className="settings-inlineToggle__title">内网访问</div>
              <div className="settings-inlineToggle__desc">只在可信环境中开启</div>
            </div>
            <div className="inline-flex items-center gap-2">
              {config.ssrf_allow_private ? <AlertTriangle size={14} style={{ color: "#d97706" }} /> : null}
              <Switch checked={config.ssrf_allow_private} onChange={(checked) => onChange("ssrf_allow_private", checked)} ariaLabel="切换内网访问" />
            </div>
          </div>
          <div className="settings-field">
            <label>SSRF 白名单</label>
            <textarea className="admin-input w-full resize-none px-3 py-2.5" rows={2} placeholder="多个地址用英文逗号分隔" value={config.ssrf_whitelist} onChange={(e) => onChange("ssrf_whitelist", e.target.value)} />
          </div>
        </div>
      </div>

      <div className="settings-retrieval-cell">
        <div className="settings-retrieval-cell__title">视窗参数</div>
        <div className="settings-sliderList">
          <div>
            <div className="settings-sliderHead"><label>宽度</label><span>{config.viewport_width}px</span></div>
            <input type="range" min="800" max="1920" value={config.viewport_width} onChange={(e) => onChange("viewport_width", Number.parseInt(e.target.value, 10))} className="settings-range" style={{ background: sliderBackground(((config.viewport_width - 800) / 1120) * 100) }} />
          </div>
          <div>
            <div className="settings-sliderHead"><label>高度</label><span>{config.viewport_height}px</span></div>
            <input type="range" min="600" max="1080" value={config.viewport_height} onChange={(e) => onChange("viewport_height", Number.parseInt(e.target.value, 10))} className="settings-range" style={{ background: sliderBackground(((config.viewport_height - 600) / 480) * 100) }} />
          </div>
        </div>
      </div>

      <div className="settings-retrieval-cell">
        <div className="settings-retrieval-cell__title">资源控制</div>
        <div className="settings-sliderList">
          <div>
            <div className="settings-sliderHead"><label>超时</label><span>{config.timeout_ms / 1000}s</span></div>
            <input type="range" min="5000" max="60000" step="1000" value={config.timeout_ms} onChange={(e) => onChange("timeout_ms", Number.parseInt(e.target.value, 10))} className="settings-range" style={{ background: sliderBackground(((config.timeout_ms - 5000) / 55000) * 100) }} />
          </div>
          <div>
            <div className="settings-sliderHead"><label>实例数</label><span>{config.max_instances}</span></div>
            <input type="range" min="1" max="5" value={config.max_instances} onChange={(e) => onChange("max_instances", Number.parseInt(e.target.value, 10))} className="settings-range" style={{ background: sliderBackground(((config.max_instances - 1) / 4) * 100) }} />
          </div>
          <div>
            <div className="settings-sliderHead"><label>空闲超时</label><span>{config.idle_timeout_ms / 1000}s</span></div>
            <input type="range" min="60000" max="600000" step="60000" value={config.idle_timeout_ms} onChange={(e) => onChange("idle_timeout_ms", Number.parseInt(e.target.value, 10))} className="settings-range" style={{ background: sliderBackground(((config.idle_timeout_ms - 60000) / 540000) * 100) }} />
          </div>
        </div>
      </div>
    </div>
  </div>
);

export default BrowserConfigPanel;
