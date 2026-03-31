import React from "react";
import { Monitor, AlertTriangle } from "lucide-react";
import type { BrowserConfig } from "../../services/api";

interface BrowserConfigPanelProps {
  config: BrowserConfig;
  onChange: (
    key: keyof BrowserConfig,
    value: string | boolean | number,
  ) => void;
}

/**
 * 浏览器配置面板组件
 * 支持配置浏览器自动化工具的各项参数
 * 实时保存配置
 */
const BrowserConfigPanel: React.FC<BrowserConfigPanelProps> = ({
  config,
  onChange,
}) => {
  const browserTypes = [
    { id: "chromium", name: "Chromium", description: "推荐使用，性能优秀" },
    { id: "firefox", name: "Firefox", description: "Mozilla Firefox 浏览器" },
    { id: "webkit", name: "WebKit", description: "Safari 内核浏览器" },
  ];

  const systemBrowserChannels = [
    { id: "chrome", name: "Google Chrome" },
    { id: "msedge", name: "Microsoft Edge" },
    { id: "firefox", name: "Firefox" },
  ];

  const currentBrowserType = browserTypes.find(
    (b) => b.id === config.default_type,
  );

  return (
    <div
      className="glass-card rounded-2xl p-6"
      style={{ border: "1px solid var(--glass-border)" }}
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-blue-700/20 flex items-center justify-center">
          <Monitor size={20} className="text-blue-400" />
        </div>
        <div>
          <h2
            className="text-lg font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            浏览器自动化配置
          </h2>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            配置浏览器自动化工具参数（配置自动保存）
          </p>
        </div>
      </div>

      <div className="space-y-6">
        <div className="space-y-5">
          <h3
            className="text-sm font-semibold pb-2 border-b"
            style={{
              color: "var(--text-secondary)",
              borderColor: "var(--glass-border)",
            }}
          >
            基础配置
          </h3>

          <div>
            <label
              className="block text-sm font-medium mb-2"
              style={{ color: "var(--text-secondary)" }}
            >
              默认浏览器类型
            </label>
            <select
              value={config.default_type}
              onChange={(e) => onChange("default_type", e.target.value)}
              className="w-full px-4 py-3 glass-input rounded-xl appearance-none cursor-pointer"
              style={{
                color: "var(--text-primary)",
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='${encodeURIComponent("var(--text-muted)")}'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
                backgroundRepeat: "no-repeat",
                backgroundPosition: "right 1rem center",
                backgroundSize: "1.5rem",
              }}
            >
              {browserTypes.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.name}
                </option>
              ))}
            </select>
            {currentBrowserType && (
              <p
                className="mt-2 text-xs"
                style={{ color: "var(--text-muted)" }}
              >
                {currentBrowserType.description}
              </p>
            )}
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label
                className="text-sm font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                使用系统浏览器
              </label>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                使用系统已安装的浏览器，无需下载额外浏览器
              </p>
            </div>
            <button
              onClick={() =>
                onChange("use_system_browser", !config.use_system_browser)
              }
              className={`relative w-12 h-6 rounded-full transition-colors ${
                config.use_system_browser
                  ? "bg-gradient-to-r from-primary to-primary-dark"
                  : "bg-gray-600"
              }`}
            >
              <span
                className={`block w-4 h-4 rounded-full bg-white shadow-md transition-transform absolute top-1 ${
                  config.use_system_browser
                    ? "left-[calc(100%-1.25rem)]"
                    : "left-1"
                }`}
              />
            </button>
          </div>

          {config.use_system_browser && (
            <div>
              <label
                className="block text-sm font-medium mb-2"
                style={{ color: "var(--text-secondary)" }}
              >
                系统浏览器通道
              </label>
              <select
                value={config.system_browser_channel}
                onChange={(e) =>
                  onChange("system_browser_channel", e.target.value)
                }
                className="w-full px-4 py-3 glass-input rounded-xl appearance-none cursor-pointer"
                style={{
                  color: "var(--text-primary)",
                  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='${encodeURIComponent("var(--text-muted)")}'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
                  backgroundRepeat: "no-repeat",
                  backgroundPosition: "right 1rem center",
                  backgroundSize: "1.5rem",
                }}
              >
                {systemBrowserChannels.map((channel) => (
                  <option key={channel.id} value={channel.id}>
                    {channel.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="space-y-5">
          <h3
            className="text-sm font-semibold pb-2 border-b"
            style={{
              color: "var(--text-secondary)",
              borderColor: "var(--glass-border)",
            }}
          >
            性能配置
          </h3>

          <div className="flex items-center justify-between">
            <div>
              <label
                className="text-sm font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                无头模式
              </label>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                无头模式下浏览器不显示窗口，适合服务器环境
              </p>
            </div>
            <button
              onClick={() => onChange("headless", !config.headless)}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                config.headless
                  ? "bg-gradient-to-r from-primary to-primary-dark"
                  : "bg-gray-600"
              }`}
            >
              <span
                className={`block w-4 h-4 rounded-full bg-white shadow-md transition-transform absolute top-1 ${
                  config.headless ? "left-[calc(100%-1.25rem)]" : "left-1"
                }`}
              />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label
                  className="text-sm font-medium"
                  style={{ color: "var(--text-secondary)" }}
                >
                  视口宽度
                </label>
                <span
                  className="text-sm font-mono"
                  style={{ color: "var(--primary)" }}
                >
                  {config.viewport_width}px
                </span>
              </div>
              <input
                type="range"
                min="800"
                max="1920"
                value={config.viewport_width}
                onChange={(e) =>
                  onChange("viewport_width", parseInt(e.target.value))
                }
                className="w-full h-2 rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${
                    ((config.viewport_width - 800) / 1120) * 100
                  }%, var(--glass-border) ${
                    ((config.viewport_width - 800) / 1120) * 100
                  }%, var(--glass-border) 100%)`,
                }}
              />
              <p
                className="mt-2 text-xs"
                style={{ color: "var(--text-muted)" }}
              >
                浏览器窗口宽度（像素）
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label
                  className="text-sm font-medium"
                  style={{ color: "var(--text-secondary)" }}
                >
                  视口高度
                </label>
                <span
                  className="text-sm font-mono"
                  style={{ color: "var(--primary)" }}
                >
                  {config.viewport_height}px
                </span>
              </div>
              <input
                type="range"
                min="600"
                max="1080"
                value={config.viewport_height}
                onChange={(e) =>
                  onChange("viewport_height", parseInt(e.target.value))
                }
                className="w-full h-2 rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${
                    ((config.viewport_height - 600) / 480) * 100
                  }%, var(--glass-border) ${
                    ((config.viewport_height - 600) / 480) * 100
                  }%, var(--glass-border) 100%)`,
                }}
              />
              <p
                className="mt-2 text-xs"
                style={{ color: "var(--text-muted)" }}
              >
                浏览器窗口高度（像素）
              </p>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label
                className="text-sm font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                超时时间
              </label>
              <span
                className="text-sm font-mono"
                style={{ color: "var(--primary)" }}
              >
                {config.timeout_ms / 1000}s
              </span>
            </div>
            <input
              type="range"
              min="5000"
              max="60000"
              step="1000"
              value={config.timeout_ms}
              onChange={(e) => onChange("timeout_ms", parseInt(e.target.value))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${
                  ((config.timeout_ms - 5000) / 55000) * 100
                }%, var(--glass-border) ${
                  ((config.timeout_ms - 5000) / 55000) * 100
                }%, var(--glass-border) 100%)`,
              }}
            />
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              浏览器操作超时时间（毫秒）
            </p>
          </div>
        </div>

        <div className="space-y-5">
          <h3
            className="text-sm font-semibold pb-2 border-b"
            style={{
              color: "var(--text-secondary)",
              borderColor: "var(--glass-border)",
            }}
          >
            安全配置
          </h3>

          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <label
                  className="text-sm font-medium"
                  style={{ color: "var(--text-secondary)" }}
                >
                  允许访问内网
                </label>
                {config.ssrf_allow_private && (
                  <AlertTriangle size={14} className="text-yellow-500" />
                )}
              </div>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                允许浏览器访问内网地址（如 192.168.x.x）
              </p>
              {config.ssrf_allow_private && (
                <p className="text-xs text-yellow-500 mt-1">
                  ⚠️ 启用此选项可能存在安全风险
                </p>
              )}
            </div>
            <button
              onClick={() =>
                onChange("ssrf_allow_private", !config.ssrf_allow_private)
              }
              className={`relative w-12 h-6 rounded-full transition-colors ${
                config.ssrf_allow_private
                  ? "bg-gradient-to-r from-yellow-500 to-yellow-600"
                  : "bg-gray-600"
              }`}
            >
              <span
                className={`block w-4 h-4 rounded-full bg-white shadow-md transition-transform absolute top-1 ${
                  config.ssrf_allow_private
                    ? "left-[calc(100%-1.25rem)]"
                    : "left-1"
                }`}
              />
            </button>
          </div>

          <div>
            <label
              className="block text-sm font-medium mb-2"
              style={{ color: "var(--text-secondary)" }}
            >
              URL 白名单
            </label>
            <textarea
              value={config.ssrf_whitelist}
              onChange={(e) => onChange("ssrf_whitelist", e.target.value)}
              placeholder="https://example.com, https://api.example.com"
              rows={3}
              className="w-full px-4 py-3 glass-input rounded-xl resize-none"
              style={{ color: "var(--text-primary)" }}
            />
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              允许访问的 URL 列表，多个 URL 用逗号分隔
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label
                  className="text-sm font-medium"
                  style={{ color: "var(--text-secondary)" }}
                >
                  最大实例数
                </label>
                <span
                  className="text-sm font-mono"
                  style={{ color: "var(--primary)" }}
                >
                  {config.max_instances}
                </span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                value={config.max_instances}
                onChange={(e) =>
                  onChange("max_instances", parseInt(e.target.value))
                }
                className="w-full h-2 rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${
                    ((config.max_instances - 1) / 4) * 100
                  }%, var(--glass-border) ${
                    ((config.max_instances - 1) / 4) * 100
                  }%, var(--glass-border) 100%)`,
                }}
              />
              <p
                className="mt-2 text-xs"
                style={{ color: "var(--text-muted)" }}
              >
                同时运行的最大浏览器实例数量
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label
                  className="text-sm font-medium"
                  style={{ color: "var(--text-secondary)" }}
                >
                  空闲超时
                </label>
                <span
                  className="text-sm font-mono"
                  style={{ color: "var(--primary)" }}
                >
                  {config.idle_timeout_ms / 1000}s
                </span>
              </div>
              <input
                type="range"
                min="60000"
                max="600000"
                step="60000"
                value={config.idle_timeout_ms}
                onChange={(e) =>
                  onChange("idle_timeout_ms", parseInt(e.target.value))
                }
                className="w-full h-2 rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${
                    ((config.idle_timeout_ms - 60000) / 540000) * 100
                  }%, var(--glass-border) ${
                    ((config.idle_timeout_ms - 60000) / 540000) * 100
                  }%, var(--glass-border) 100%)`,
                }}
              />
              <p
                className="mt-2 text-xs"
                style={{ color: "var(--text-muted)" }}
              >
                浏览器空闲超时时间（毫秒）
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BrowserConfigPanel;
