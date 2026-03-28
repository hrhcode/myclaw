import { Settings, Sliders, Clock, Layers } from "lucide-react";

type MemoryConfig = {
  memory_top_k: string;
  memory_min_score: string;
  memory_use_hybrid: string;
  memory_vector_weight: string;
  memory_text_weight: string;
  memory_enable_mmr: string;
  memory_mmr_lambda: string;
  memory_enable_temporal_decay: string;
  memory_half_life_days: string;
};

interface SearchConfigPanelProps {
  config: MemoryConfig;
  onChange: (key: keyof MemoryConfig, value: string) => void;
}

/**
 * 搜索配置面板组件
 * 包含基础搜索参数、混合搜索配置、结果重排序配置和时间衰减配置
 */
const SearchConfigPanel: React.FC<SearchConfigPanelProps> = ({
  config,
  onChange,
}) => {
  const isHybridEnabled = config.memory_use_hybrid === "true";
  const isMmrEnabled = config.memory_enable_mmr === "true";
  const isTemporalDecayEnabled = config.memory_enable_temporal_decay === "true";

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        className="glass-card rounded-2xl p-5"
        style={{ border: "1px solid var(--glass-border)" }}
      >
        <div className="flex items-center gap-3 mb-5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary/20 to-primary-dark/20 flex items-center justify-center">
            <Settings size={18} className="text-primary" />
          </div>
          <div>
            <h3
              className="text-base font-semibold"
              style={{ color: "var(--text-primary)" }}
            >
              基础搜索参数
            </h3>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              控制搜索结果的基本参数
            </p>
          </div>
        </div>

        <div className="space-y-5">
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
                {config.memory_top_k}
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="20"
              value={config.memory_top_k}
              onChange={(e) => onChange("memory_top_k", e.target.value)}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${
                  ((parseInt(config.memory_top_k) - 1) / 19) * 100
                }%, var(--glass-border) ${
                  ((parseInt(config.memory_top_k) - 1) / 19) * 100
                }%, var(--glass-border) 100%)`,
              }}
            />
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              每次搜索返回的最大结果数量（1-20）
            </p>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label
                className="text-sm font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                最小相似度
              </label>
              <span
                className="text-sm font-mono"
                style={{ color: "var(--primary)" }}
              >
                {config.memory_min_score}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={config.memory_min_score}
              onChange={(e) => onChange("memory_min_score", e.target.value)}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${
                  parseFloat(config.memory_min_score) * 100
                }%, var(--glass-border) ${
                  parseFloat(config.memory_min_score) * 100
                }%, var(--glass-border) 100%)`,
              }}
            />
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              只返回相似度高于此阈值的结果（0-1）
            </p>
          </div>
        </div>
      </div>

      <div
        className="glass-card rounded-2xl p-5"
        style={{ border: "1px solid var(--glass-border)" }}
      >
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500/20 to-blue-700/20 flex items-center justify-center">
              <Layers size={18} className="text-blue-400" />
            </div>
            <div>
              <h3
                className="text-base font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                混合搜索配置
              </h3>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                向量 + 文本相似度
              </p>
            </div>
          </div>
          <button
            onClick={() =>
              onChange(
                "memory_use_hybrid",
                config.memory_use_hybrid === "true" ? "false" : "true",
              )
            }
            className={`relative w-12 h-6 rounded-full transition-colors ${
              config.memory_use_hybrid === "true"
                ? "bg-gradient-to-r from-primary to-primary-dark"
                : "bg-gray-600"
            }`}
          >
            <span
              className={`block w-4 h-4 rounded-full bg-white shadow-md transition-transform absolute top-1 ${
                config.memory_use_hybrid === "true"
                  ? "left-[calc(100%-1.25rem)]"
                  : "left-1"
              }`}
            />
          </button>
        </div>

        <div
          className={`space-y-5 ${!isHybridEnabled ? "opacity-50 pointer-events-none" : ""}`}
        >
          <div>
            <div className="flex items-center justify-between mb-2">
              <label
                className="text-sm font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                向量权重
              </label>
              <span
                className="text-sm font-mono"
                style={{ color: "var(--primary)" }}
              >
                {config.memory_vector_weight}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={config.memory_vector_weight}
              onChange={(e) => {
                onChange("memory_vector_weight", e.target.value);
                onChange(
                  "memory_text_weight",
                  (1 - parseFloat(e.target.value)).toFixed(2),
                );
              }}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${
                  parseFloat(config.memory_vector_weight) * 100
                }%, var(--glass-border) ${
                  parseFloat(config.memory_vector_weight) * 100
                }%, var(--glass-border) 100%)`,
              }}
            />
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              向量相似度权重
            </p>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label
                className="text-sm font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                文本权重
              </label>
              <span
                className="text-sm font-mono"
                style={{ color: "var(--primary)" }}
              >
                {config.memory_text_weight}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={config.memory_text_weight}
              onChange={(e) => {
                onChange("memory_text_weight", e.target.value);
                onChange(
                  "memory_vector_weight",
                  (1 - parseFloat(e.target.value)).toFixed(2),
                );
              }}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${
                  parseFloat(config.memory_text_weight) * 100
                }%, var(--glass-border) ${
                  parseFloat(config.memory_text_weight) * 100
                }%, var(--glass-border) 100%)`,
              }}
            />
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              BM25 文本相似度权重
            </p>
          </div>
        </div>
      </div>

      <div
        className="glass-card rounded-2xl p-5"
        style={{ border: "1px solid var(--glass-border)" }}
      >
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-700/20 flex items-center justify-center">
              <Sliders size={18} className="text-purple-400" />
            </div>
            <div>
              <h3
                className="text-base font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                结果重排序
              </h3>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                MMR 算法提高多样性
              </p>
            </div>
          </div>
          <button
            onClick={() =>
              onChange(
                "memory_enable_mmr",
                config.memory_enable_mmr === "true" ? "false" : "true",
              )
            }
            className={`relative w-12 h-6 rounded-full transition-colors ${
              config.memory_enable_mmr === "true"
                ? "bg-gradient-to-r from-primary to-primary-dark"
                : "bg-gray-600"
            }`}
          >
            <span
              className={`block w-4 h-4 rounded-full bg-white shadow-md transition-transform absolute top-1 ${
                config.memory_enable_mmr === "true"
                  ? "left-[calc(100%-1.25rem)]"
                  : "left-1"
              }`}
            />
          </button>
        </div>

        <div
          className={`space-y-5 ${!isMmrEnabled ? "opacity-50 pointer-events-none" : ""}`}
        >
          <div>
            <div className="flex items-center justify-between mb-2">
              <label
                className="text-sm font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                MMR 参数
              </label>
              <span
                className="text-sm font-mono"
                style={{ color: "var(--primary)" }}
              >
                {config.memory_mmr_lambda}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={config.memory_mmr_lambda}
              onChange={(e) => onChange("memory_mmr_lambda", e.target.value)}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${
                  parseFloat(config.memory_mmr_lambda) * 100
                }%, var(--glass-border) ${
                  parseFloat(config.memory_mmr_lambda) * 100
                }%, var(--glass-border) 100%)`,
              }}
            />
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              1 重相关性，0 重多样性
            </p>
          </div>
        </div>
      </div>

      <div
        className="glass-card rounded-2xl p-5"
        style={{ border: "1px solid var(--glass-border)" }}
      >
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-orange-500/20 to-orange-700/20 flex items-center justify-center">
              <Clock size={18} className="text-orange-400" />
            </div>
            <div>
              <h3
                className="text-base font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                时间衰减
              </h3>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                根据时间降低权重
              </p>
            </div>
          </div>
          <button
            onClick={() =>
              onChange(
                "memory_enable_temporal_decay",
                config.memory_enable_temporal_decay === "true"
                  ? "false"
                  : "true",
              )
            }
            className={`relative w-12 h-6 rounded-full transition-colors ${
              config.memory_enable_temporal_decay === "true"
                ? "bg-gradient-to-r from-primary to-primary-dark"
                : "bg-gray-600"
            }`}
          >
            <span
              className={`block w-4 h-4 rounded-full bg-white shadow-md transition-transform absolute top-1 ${
                config.memory_enable_temporal_decay === "true"
                  ? "left-[calc(100%-1.25rem)]"
                  : "left-1"
              }`}
            />
          </button>
        </div>

        <div
          className={`space-y-5 ${!isTemporalDecayEnabled ? "opacity-50 pointer-events-none" : ""}`}
        >
          <div>
            <div className="flex items-center justify-between mb-2">
              <label
                className="text-sm font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                半衰期
              </label>
              <span
                className="text-sm font-mono"
                style={{ color: "var(--primary)" }}
              >
                {config.memory_half_life_days} 天
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="365"
              value={config.memory_half_life_days}
              onChange={(e) =>
                onChange("memory_half_life_days", e.target.value)
              }
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${
                  ((parseInt(config.memory_half_life_days) - 1) / 364) * 100
                }%, var(--glass-border) ${
                  ((parseInt(config.memory_half_life_days) - 1) / 364) * 100
                }%, var(--glass-border) 100%)`,
              }}
            />
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              权重减半所需天数（1-365）
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SearchConfigPanel;
