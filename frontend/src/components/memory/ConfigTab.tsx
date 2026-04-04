import { useCallback, useEffect, useRef, useState } from 'react';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

import { getConfig, setConfig } from '../../services/api';
import { SectionCard } from '../admin';
import SearchConfigPanel from './components/SearchConfigPanel';

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

const DEFAULT_CONFIG: MemoryConfig = {
  memory_top_k: '5',
  memory_min_score: '0.5',
  memory_use_hybrid: 'true',
  memory_vector_weight: '0.7',
  memory_text_weight: '0.3',
  memory_enable_mmr: 'true',
  memory_mmr_lambda: '0.7',
  memory_enable_temporal_decay: 'true',
  memory_half_life_days: '30',
};

const CONFIG_KEYS = Object.keys(DEFAULT_CONFIG) as (keyof MemoryConfig)[];

const ConfigTab: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [isAutoSaving, setIsAutoSaving] = useState(false);
  const [saveState, setSaveState] = useState<'idle' | 'saved' | 'error'>('idle');
  const [saveErrorText, setSaveErrorText] = useState('');
  const [config, setConfigState] = useState<MemoryConfig>(DEFAULT_CONFIG);

  const loadedRef = useRef(false);
  const lastSavedConfigRef = useRef<MemoryConfig>(DEFAULT_CONFIG);
  const autoSaveTimerRef = useRef<number | null>(null);

  const loadConfig = useCallback(async () => {
    try {
      setIsLoading(true);
      const entries = await Promise.all(
        CONFIG_KEYS.map(async (key) => {
          try {
            const value = await getConfig(key);
            return [key, value] as const;
          } catch {
            return [key, DEFAULT_CONFIG[key]] as const;
          }
        }),
      );

      const loaded = entries.reduce((acc, [key, value]) => ({ ...acc, [key]: value }), DEFAULT_CONFIG);

      setConfigState(loaded);
      lastSavedConfigRef.current = loaded;
      loadedRef.current = true;
      setSaveState('idle');
    } catch (error) {
      console.error('Failed to load config:', error);
      setSaveState('error');
      setSaveErrorText('加载记忆配置失败');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadConfig();
  }, [loadConfig]);

  useEffect(() => {
    if (!loadedRef.current) return;

    if (autoSaveTimerRef.current !== null) {
      window.clearTimeout(autoSaveTimerRef.current);
    }

    autoSaveTimerRef.current = window.setTimeout(async () => {
      const changedKeys = CONFIG_KEYS.filter((key) => config[key] !== lastSavedConfigRef.current[key]);
      if (changedKeys.length === 0) return;

      try {
        setIsAutoSaving(true);
        setSaveState('idle');
        await Promise.all(changedKeys.map((key) => setConfig(key, config[key])));
        lastSavedConfigRef.current = config;
        setSaveState('saved');
        setSaveErrorText('');
      } catch (error) {
        console.error('Failed to auto save memory config:', error);
        setSaveState('error');
        setSaveErrorText('自动保存失败，请稍后重试');
      } finally {
        setIsAutoSaving(false);
      }
    }, 500);

    return () => {
      if (autoSaveTimerRef.current !== null) {
        window.clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, [config]);

  const handleConfigChange = (key: keyof MemoryConfig, value: string) => {
    setConfigState((prev) => ({ ...prev, [key]: value }));
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 size={45} className="text-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="admin-frame">
      <SectionCard className="px-3 py-2">
        <div className="flex items-center gap-2 text-sm">
          {isAutoSaving ? (
            <>
              <Loader2 size={19} className="animate-spin" style={{ color: 'var(--accent)' }} />
              <span style={{ color: 'var(--text-secondary)' }}>检测到配置变更，正在自动保存...</span>
            </>
          ) : saveState === 'saved' ? (
            <>
              <CheckCircle size={19} style={{ color: '#16a34a' }} />
              <span style={{ color: '#16a34a' }}>已自动保存</span>
            </>
          ) : saveState === 'error' ? (
            <>
              <AlertCircle size={19} style={{ color: '#dc2626' }} />
              <span style={{ color: '#dc2626' }}>{saveErrorText || '保存失败'}</span>
            </>
          ) : (
            <span style={{ color: 'var(--text-muted)' }}>修改配置后会自动保存</span>
          )}
        </div>
      </SectionCard>

      <SearchConfigPanel config={config} onChange={handleConfigChange} />
    </div>
  );
};

export default ConfigTab;
