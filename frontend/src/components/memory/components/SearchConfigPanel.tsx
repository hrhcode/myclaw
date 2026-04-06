import { Switch } from "../../admin";

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
  full?: boolean;
  onChange: (key: keyof MemoryConfig, value: string) => void;
  autoExtract?: boolean;
  memoryThreshold?: number;
  onAutoExtractChange?: (enabled: boolean) => void;
  onThresholdChange?: (value: number) => void;
}

const sliderBackground = (percent: number) =>
  `linear-gradient(to right, var(--accent) 0%, var(--accent) ${percent}%, var(--panel-border) ${percent}%, var(--panel-border) 100%)`;

const SearchConfigPanel: React.FC<SearchConfigPanelProps> = ({ config, full, onChange, autoExtract, memoryThreshold, onAutoExtractChange, onThresholdChange }) => {
  const hybridEnabled = config.memory_use_hybrid === "true";
  const mmrEnabled = config.memory_enable_mmr === "true";
  const decayEnabled = config.memory_enable_temporal_decay === "true";
  const autoExtractEnabled = autoExtract === true;

  const showAutoExtract = onAutoExtractChange && onThresholdChange && autoExtract !== undefined && memoryThreshold !== undefined;

  return (
    <div className={`settings-block${full ? " settings-block--full" : ""}`}>
      <div className="settings-block__head"><h3>记忆系统</h3><span>RAG + 自动提取</span></div>
      <div className="memory-config-grid">
        <div className="memory-config-col">
          {showAutoExtract ? (
            <section className="memory-config-section">
              <div className="memory-config-section__header">
                <span className="memory-config-section__label">自动提取</span>
                <span className="memory-config-section__hint">对话结束时自动保存有价值的信息</span>
              </div>
              <div className="memory-config-section__body">
                <div className="memory-config-row">
                  <span className="memory-config-row__label">启用</span>
                  <Switch checked={autoExtractEnabled} onChange={(checked) => onAutoExtractChange!(checked)} ariaLabel="切换自动记忆提取" />
                </div>
                <div className={`memory-config-row${!autoExtractEnabled ? " opacity-55 pointer-events-none" : ""}`}>
                  <span className="memory-config-row__label">阈值</span>
                  <div className="memory-config-slider">
                    <input type="range" min="2" max="20" value={memoryThreshold} onChange={(event) => onThresholdChange!(Number.parseInt(event.target.value, 10))} className="settings-range" style={{ background: sliderBackground(((memoryThreshold! - 2) / 18) * 100) }} />
                    <span className="memory-config-slider__value">{memoryThreshold}</span>
                  </div>
                </div>
              </div>
            </section>
          ) : null}

          <section className="memory-config-section">
            <div className="memory-config-section__header">
              <span className="memory-config-section__label">召回</span>
              <span className="memory-config-section__hint">控制返回结果的数量和质量</span>
            </div>
            <div className="memory-config-section__body">
              <div className="memory-config-row">
                <span className="memory-config-row__label">返回条数</span>
                <div className="memory-config-slider">
                  <input type="range" min="1" max="20" value={config.memory_top_k} onChange={(event) => onChange("memory_top_k", event.target.value)} className="settings-range" style={{ background: sliderBackground(((Number.parseInt(config.memory_top_k, 10) - 1) / 19) * 100) }} />
                  <span className="memory-config-slider__value">{config.memory_top_k}</span>
                </div>
              </div>
              <div className="memory-config-row">
                <span className="memory-config-row__label">最低分数</span>
                <div className="memory-config-slider">
                  <input type="range" min="0" max="1" step="0.01" value={config.memory_min_score} onChange={(event) => onChange("memory_min_score", event.target.value)} className="settings-range" style={{ background: sliderBackground(Number.parseFloat(config.memory_min_score) * 100) }} />
                  <span className="memory-config-slider__value">{config.memory_min_score}</span>
                </div>
              </div>
            </div>
          </section>

          <section className="memory-config-section">
            <div className="memory-config-section__header">
              <span className="memory-config-section__label">混合检索</span>
              <span className="memory-config-section__hint">语义向量 + 关键词匹配</span>
            </div>
            <div className="memory-config-section__body">
              <div className="memory-config-row">
                <span className="memory-config-row__label">启用</span>
                <Switch checked={hybridEnabled} onChange={(checked) => onChange("memory_use_hybrid", checked ? "true" : "false")} ariaLabel="切换混合检索" />
              </div>
              <div className={`memory-config-row${!hybridEnabled ? " opacity-55 pointer-events-none" : ""}`}>
                <span className="memory-config-row__label">向量权重</span>
                <div className="memory-config-slider">
                  <input type="range" min="0" max="1" step="0.01" value={config.memory_vector_weight} onChange={(event) => { const value = Number.parseFloat(event.target.value); onChange("memory_vector_weight", value.toFixed(2)); onChange("memory_text_weight", (1 - value).toFixed(2)); }} className="settings-range" style={{ background: sliderBackground(Number.parseFloat(config.memory_vector_weight) * 100) }} />
                  <span className="memory-config-slider__value">{config.memory_vector_weight}</span>
                </div>
              </div>
              <div className={`memory-config-row${!hybridEnabled ? " opacity-55 pointer-events-none" : ""}`}>
                <span className="memory-config-row__label">关键词权重</span>
                <div className="memory-config-slider">
                  <input type="range" min="0" max="1" step="0.01" value={config.memory_text_weight} onChange={(event) => { const value = Number.parseFloat(event.target.value); onChange("memory_text_weight", value.toFixed(2)); onChange("memory_vector_weight", (1 - value).toFixed(2)); }} className="settings-range" style={{ background: sliderBackground(Number.parseFloat(config.memory_text_weight) * 100) }} />
                  <span className="memory-config-slider__value">{config.memory_text_weight}</span>
                </div>
              </div>
            </div>
          </section>
        </div>

        <div className="memory-config-col">
          <section className="memory-config-section">
            <div className="memory-config-section__header">
              <span className="memory-config-section__label">MMR 去重</span>
              <span className="memory-config-section__hint">减少相似内容重复出现</span>
            </div>
            <div className="memory-config-section__body">
              <div className="memory-config-row">
                <span className="memory-config-row__label">启用</span>
                <Switch checked={mmrEnabled} onChange={(checked) => onChange("memory_enable_mmr", checked ? "true" : "false")} ariaLabel="切换 MMR 去重" />
              </div>
              <div className={`memory-config-row${!mmrEnabled ? " opacity-55 pointer-events-none" : ""}`}>
                <span className="memory-config-row__label">多样性</span>
                <div className="memory-config-slider">
                  <input type="range" min="0" max="1" step="0.01" value={config.memory_mmr_lambda} onChange={(event) => onChange("memory_mmr_lambda", event.target.value)} className="settings-range" style={{ background: sliderBackground(Number.parseFloat(config.memory_mmr_lambda) * 100) }} />
                  <span className="memory-config-slider__value">{config.memory_mmr_lambda}</span>
                </div>
              </div>
            </div>
          </section>

          <section className="memory-config-section">
            <div className="memory-config-section__header">
              <span className="memory-config-section__label">时间衰减</span>
              <span className="memory-config-section__hint">优先召回更近的知识</span>
            </div>
            <div className="memory-config-section__body">
              <div className="memory-config-row">
                <span className="memory-config-row__label">启用</span>
                <Switch checked={decayEnabled} onChange={(checked) => onChange("memory_enable_temporal_decay", checked ? "true" : "false")} ariaLabel="切换时间衰减" />
              </div>
              <div className={`memory-config-row${!decayEnabled ? " opacity-55 pointer-events-none" : ""}`}>
                <span className="memory-config-row__label">半衰期</span>
                <div className="memory-config-slider">
                  <input type="range" min="1" max="365" value={config.memory_half_life_days} onChange={(event) => onChange("memory_half_life_days", event.target.value)} className="settings-range" style={{ background: sliderBackground(((Number.parseInt(config.memory_half_life_days, 10) - 1) / 364) * 100) }} />
                  <span className="memory-config-slider__value">{config.memory_half_life_days}d</span>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default SearchConfigPanel;
