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
}

const sliderBackground = (percent: number) =>
  `linear-gradient(to right, var(--accent) 0%, var(--accent) ${percent}%, var(--panel-border) ${percent}%, var(--panel-border) 100%)`;

const SearchConfigPanel: React.FC<SearchConfigPanelProps> = ({ config, full, onChange }) => {
  const hybridEnabled = config.memory_use_hybrid === "true";
  const mmrEnabled = config.memory_enable_mmr === "true";
  const decayEnabled = config.memory_enable_temporal_decay === "true";

  return (
    <div className={`settings-block${full ? " settings-block--full" : ""}`}>
      <div className="settings-block__head"><h3>知识检索</h3><span>RAG 配置</span></div>
      <div className="settings-retrieval-grid">
        <div className="settings-retrieval-cell">
          <div className="settings-retrieval-cell__title">基础召回</div>
          <div className="settings-sliderList">
            <div><div className="settings-sliderHead"><label>返回条数</label><span>{config.memory_top_k}</span></div><input type="range" min="1" max="20" value={config.memory_top_k} onChange={(event) => onChange("memory_top_k", event.target.value)} className="settings-range" style={{ background: sliderBackground(((Number.parseInt(config.memory_top_k, 10) - 1) / 19) * 100) }} /></div>
            <div><div className="settings-sliderHead"><label>最低分数</label><span>{config.memory_min_score}</span></div><input type="range" min="0" max="1" step="0.01" value={config.memory_min_score} onChange={(event) => onChange("memory_min_score", event.target.value)} className="settings-range" style={{ background: sliderBackground(Number.parseFloat(config.memory_min_score) * 100) }} /></div>
          </div>
        </div>

        <div className="settings-retrieval-cell">
          <div className="settings-inlineToggle"><div><div className="settings-inlineToggle__title">混合检索</div><div className="settings-inlineToggle__desc">语义向量 + 关键词匹配</div></div><Switch checked={hybridEnabled} onChange={(checked) => onChange("memory_use_hybrid", checked ? "true" : "false")} ariaLabel="切换混合检索" /></div>
          <div className={hybridEnabled ? "settings-sliderList" : "settings-sliderList opacity-55 pointer-events-none"}>
            <div><div className="settings-sliderHead"><label>向量权重</label><span>{config.memory_vector_weight}</span></div><input type="range" min="0" max="1" step="0.01" value={config.memory_vector_weight} onChange={(event) => { const value = Number.parseFloat(event.target.value); onChange("memory_vector_weight", value.toFixed(2)); onChange("memory_text_weight", (1 - value).toFixed(2)); }} className="settings-range" style={{ background: sliderBackground(Number.parseFloat(config.memory_vector_weight) * 100) }} /></div>
            <div><div className="settings-sliderHead"><label>关键词权重</label><span>{config.memory_text_weight}</span></div><input type="range" min="0" max="1" step="0.01" value={config.memory_text_weight} onChange={(event) => { const value = Number.parseFloat(event.target.value); onChange("memory_text_weight", value.toFixed(2)); onChange("memory_vector_weight", (1 - value).toFixed(2)); }} className="settings-range" style={{ background: sliderBackground(Number.parseFloat(config.memory_text_weight) * 100) }} /></div>
          </div>
        </div>

        <div className="settings-retrieval-cell">
          <div className="settings-inlineToggle"><div><div className="settings-inlineToggle__title">MMR 去重</div><div className="settings-inlineToggle__desc">减少相似内容重复出现</div></div><Switch checked={mmrEnabled} onChange={(checked) => onChange("memory_enable_mmr", checked ? "true" : "false")} ariaLabel="切换 MMR 去重" /></div>
          <div className={mmrEnabled ? "settings-sliderList" : "settings-sliderList opacity-55 pointer-events-none"}>
            <div><div className="settings-sliderHead"><label>多样性</label><span>{config.memory_mmr_lambda}</span></div><input type="range" min="0" max="1" step="0.01" value={config.memory_mmr_lambda} onChange={(event) => onChange("memory_mmr_lambda", event.target.value)} className="settings-range" style={{ background: sliderBackground(Number.parseFloat(config.memory_mmr_lambda) * 100) }} /></div>
          </div>
        </div>

        <div className="settings-retrieval-cell">
          <div className="settings-inlineToggle"><div><div className="settings-inlineToggle__title">时间衰减</div><div className="settings-inlineToggle__desc">优先召回更近的知识</div></div><Switch checked={decayEnabled} onChange={(checked) => onChange("memory_enable_temporal_decay", checked ? "true" : "false")} ariaLabel="切换时间衰减" /></div>
          <div className={decayEnabled ? "settings-sliderList" : "settings-sliderList opacity-55 pointer-events-none"}>
            <div><div className="settings-sliderHead"><label>半衰期</label><span>{config.memory_half_life_days}d</span></div><input type="range" min="1" max="365" value={config.memory_half_life_days} onChange={(event) => onChange("memory_half_life_days", event.target.value)} className="settings-range" style={{ background: sliderBackground(((Number.parseInt(config.memory_half_life_days, 10) - 1) / 364) * 100) }} /></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SearchConfigPanel;
