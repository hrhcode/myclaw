import { Settings2, Layers, SlidersHorizontal, Clock3 } from 'lucide-react';

import { SectionCard, Switch } from '../../admin';

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

const sliderBackground = (percent: number) =>
  `linear-gradient(to right, var(--accent) 0%, var(--accent) ${percent}%, var(--panel-border) ${percent}%, var(--panel-border) 100%)`;

const BlockTitle: React.FC<{ icon: React.ReactNode; title: string; desc: string }> = ({ icon, title, desc }) => (
  <div className="flex items-center gap-2 mb-4">
    <span
      className="w-8 h-8 rounded-lg flex items-center justify-center"
      style={{ backgroundColor: 'var(--surface-subtle)', color: 'var(--text-secondary)' }}
    >
      {icon}
    </span>
    <div>
      <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
        {title}
      </h3>
      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
        {desc}
      </p>
    </div>
  </div>
);

const SearchConfigPanel: React.FC<SearchConfigPanelProps> = ({ config, onChange }) => {
  const hybridEnabled = config.memory_use_hybrid === 'true';
  const mmrEnabled = config.memory_enable_mmr === 'true';
  const decayEnabled = config.memory_enable_temporal_decay === 'true';

  const topKPercent = ((Number.parseInt(config.memory_top_k, 10) - 1) / 19) * 100;
  const minScorePercent = Number.parseFloat(config.memory_min_score) * 100;
  const vectorPercent = Number.parseFloat(config.memory_vector_weight) * 100;
  const textPercent = Number.parseFloat(config.memory_text_weight) * 100;
  const mmrPercent = Number.parseFloat(config.memory_mmr_lambda) * 100;
  const halfLifePercent = ((Number.parseInt(config.memory_half_life_days, 10) - 1) / 364) * 100;

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
      <SectionCard className="p-4">
        <BlockTitle icon={<Settings2 size={16} />} title="基础检索参数" desc="控制检索结果数量和最低相关度。" />
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                检索条数
              </label>
              <span className="text-xs font-mono" style={{ color: 'var(--text-primary)' }}>
                {config.memory_top_k}
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="20"
              value={config.memory_top_k}
              onChange={(event) => onChange('memory_top_k', event.target.value)}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{ background: sliderBackground(topKPercent) }}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                最低相关度
              </label>
              <span className="text-xs font-mono" style={{ color: 'var(--text-primary)' }}>
                {config.memory_min_score}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={config.memory_min_score}
              onChange={(event) => onChange('memory_min_score', event.target.value)}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{ background: sliderBackground(minScorePercent) }}
            />
          </div>
        </div>
      </SectionCard>

      <SectionCard className="p-4">
        <div className="flex items-start justify-between gap-3 mb-4">
          <BlockTitle icon={<Layers size={16} />} title="混合检索" desc="融合向量检索和文本检索，并可调节二者权重。" />
          <Switch
            checked={hybridEnabled}
            onChange={(checked) => onChange('memory_use_hybrid', checked ? 'true' : 'false')}
            ariaLabel="切换混合检索"
          />
        </div>

        <div className={`space-y-4 ${hybridEnabled ? '' : 'opacity-55 pointer-events-none'}`}>
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                向量权重
              </label>
              <span className="text-xs font-mono" style={{ color: 'var(--text-primary)' }}>
                {config.memory_vector_weight}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={config.memory_vector_weight}
              onChange={(event) => {
                const value = Number.parseFloat(event.target.value);
                onChange('memory_vector_weight', value.toFixed(2));
                onChange('memory_text_weight', (1 - value).toFixed(2));
              }}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{ background: sliderBackground(vectorPercent) }}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                文本权重
              </label>
              <span className="text-xs font-mono" style={{ color: 'var(--text-primary)' }}>
                {config.memory_text_weight}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={config.memory_text_weight}
              onChange={(event) => {
                const value = Number.parseFloat(event.target.value);
                onChange('memory_text_weight', value.toFixed(2));
                onChange('memory_vector_weight', (1 - value).toFixed(2));
              }}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer"
              style={{ background: sliderBackground(textPercent) }}
            />
          </div>
        </div>
      </SectionCard>

      <SectionCard className="p-4">
        <div className="flex items-start justify-between gap-3 mb-4">
          <BlockTitle icon={<SlidersHorizontal size={16} />} title="MMR 重排" desc="提升返回结果的多样性。" />
          <Switch
            checked={mmrEnabled}
            onChange={(checked) => onChange('memory_enable_mmr', checked ? 'true' : 'false')}
            ariaLabel="切换 MMR 重排"
          />
        </div>
        <div className={mmrEnabled ? '' : 'opacity-55 pointer-events-none'}>
          <div className="flex items-center justify-between mb-1">
            <label className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              重排系数
            </label>
            <span className="text-xs font-mono" style={{ color: 'var(--text-primary)' }}>
              {config.memory_mmr_lambda}
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={config.memory_mmr_lambda}
            onChange={(event) => onChange('memory_mmr_lambda', event.target.value)}
            className="w-full h-2 rounded-lg appearance-none cursor-pointer"
            style={{ background: sliderBackground(mmrPercent) }}
          />
        </div>
      </SectionCard>

      <SectionCard className="p-4">
        <div className="flex items-start justify-between gap-3 mb-4">
          <BlockTitle icon={<Clock3 size={16} />} title="时间衰减" desc="越旧的记忆权重越低。" />
          <Switch
            checked={decayEnabled}
            onChange={(checked) => onChange('memory_enable_temporal_decay', checked ? 'true' : 'false')}
            ariaLabel="切换时间衰减"
          />
        </div>
        <div className={decayEnabled ? '' : 'opacity-55 pointer-events-none'}>
          <div className="flex items-center justify-between mb-1">
            <label className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              半衰期（天）
            </label>
            <span className="text-xs font-mono" style={{ color: 'var(--text-primary)' }}>
              {config.memory_half_life_days}
            </span>
          </div>
          <input
            type="range"
            min="1"
            max="365"
            value={config.memory_half_life_days}
            onChange={(event) => onChange('memory_half_life_days', event.target.value)}
            className="w-full h-2 rounded-lg appearance-none cursor-pointer"
            style={{ background: sliderBackground(halfLifePercent) }}
          />
        </div>
      </SectionCard>
    </div>
  );
};

export default SearchConfigPanel;
