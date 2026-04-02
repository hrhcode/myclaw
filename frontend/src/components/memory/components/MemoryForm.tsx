import { useEffect, useState } from 'react';
import { Loader2, Star, X } from 'lucide-react';

import { createLongTermMemory, updateLongTermMemory } from '../../../services/api';
import type { LongTermMemory } from '../../../types';
import { SectionCard } from '../../admin';

interface MemoryFormProps {
  memory: LongTermMemory | null;
  defaultSessionId?: number | null;
  onSave: (memory: LongTermMemory) => void;
  onClose: () => void;
}

const SOURCE_OPTIONS = ['manual', 'conversation_summary', 'auto_extract', 'custom'] as const;

const SOURCE_LABELS: Record<(typeof SOURCE_OPTIONS)[number], string> = {
  manual: '手动',
  conversation_summary: '会话摘要',
  auto_extract: '自动提炼',
  custom: '自定义',
};

const MemoryForm: React.FC<MemoryFormProps> = ({ memory, defaultSessionId, onSave, onClose }) => {
  const [content, setContent] = useState('');
  const [key, setKey] = useState('');
  const [importance, setImportance] = useState(0.5);
  const [source, setSource] = useState<(typeof SOURCE_OPTIONS)[number]>('manual');
  const [customSource, setCustomSource] = useState('');
  const [sessionId, setSessionId] = useState<number | ''>('');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!memory) {
      setContent('');
      setKey('');
      setImportance(0.5);
      setSource('manual');
      setCustomSource('');
      setSessionId(defaultSessionId ?? '');
      return;
    }

    setContent(memory.content);
    setKey(memory.key || '');
    setImportance(memory.importance);
    setSessionId(memory.session_id ?? defaultSessionId ?? '');
    const value = memory.source || 'manual';
    if (SOURCE_OPTIONS.includes(value as (typeof SOURCE_OPTIONS)[number])) {
      setSource(value as (typeof SOURCE_OPTIONS)[number]);
      setCustomSource('');
    } else {
      setSource('custom');
      setCustomSource(value);
    }
  }, [defaultSessionId, memory]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!content.trim()) {
      setError('记忆内容不能为空。');
      return;
    }
    if (content.length > 5000) {
      setError('记忆内容不能超过 5000 个字符。');
      return;
    }

    try {
      setIsSaving(true);
      setError('');
      const finalSource = source === 'custom' ? customSource.trim() : source;
      const payload = {
        content: content.trim(),
        key: key.trim() || undefined,
        importance,
        source: finalSource || undefined,
      };
      const saved = memory
        ? await updateLongTermMemory(memory.id, payload)
        : await createLongTermMemory(
            payload.content,
            payload.key,
            payload.importance,
            payload.source,
            typeof sessionId === 'number' ? sessionId : undefined,
          );
      onSave(saved);
    } catch (err) {
      console.error('Failed to save memory:', err);
      setError('保存记忆失败，请稍后重试。');
    } finally {
      setIsSaving(false);
    }
  };

  const score = Math.round(importance * 10);

  return (
    <div className="fixed inset-0 bg-black/45 flex items-center justify-center z-50" onClick={onClose}>
      <div className="w-full max-w-2xl mx-4" onClick={(event) => event.stopPropagation()}>
        <SectionCard className="max-h-[90vh] overflow-y-auto p-5">
          <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
            {memory ? '编辑记忆' : '新增记忆'}
          </h2>
          <button type="button" className="p-2 rounded-lg" style={{ color: 'var(--text-secondary)' }} onClick={onClose}>
            <X size={18} />
          </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm mb-1" style={{ color: 'var(--text-secondary)' }}>
                内容
              </label>
              <textarea
                rows={6}
                maxLength={5000}
                className="admin-input w-full px-3 py-2.5 resize-none"
                value={content}
                onChange={(event) => setContent(event.target.value)}
                placeholder="记录稳定事实、个人偏好、关键决策，或可复用的摘要。"
              />
              <div className="mt-1 flex items-center justify-between text-xs">
                <span style={{ color: '#dc2626' }}>{error}</span>
                <span style={{ color: 'var(--text-muted)' }}>{content.length}/5000</span>
              </div>
            </div>

            <div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm mb-1" style={{ color: 'var(--text-secondary)' }}>
                    标签
                  </label>
                  <input
                    type="text"
                    className="admin-input w-full px-3 py-2.5"
                    value={key}
                    onChange={(event) => setKey(event.target.value)}
                    placeholder="例如：项目、偏好、决策"
                  />
                </div>
                <div>
                  <label className="block text-sm mb-1" style={{ color: 'var(--text-secondary)' }}>
                    工作会话 ID
                  </label>
                  <input
                    type="number"
                    className="admin-input w-full px-3 py-2.5"
                    value={sessionId}
                    onChange={(event) => setSessionId(event.target.value ? Number.parseInt(event.target.value, 10) : '')}
                    placeholder="留空则作为全局记忆"
                  />
                </div>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  重要度
                </label>
                <span className="text-xs font-mono inline-flex items-center gap-1" style={{ color: 'var(--text-primary)' }}>
                  <Star size={12} /> {score}/10
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={importance}
                onChange={(event) => setImportance(Number.parseFloat(event.target.value))}
                className="w-full h-2 rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, var(--accent) 0%, var(--accent) ${
                    importance * 100
                  }%, var(--panel-border) ${importance * 100}%, var(--panel-border) 100%)`,
                }}
              />
            </div>

            <div>
              <label className="block text-sm mb-1" style={{ color: 'var(--text-secondary)' }}>
                来源
              </label>
              <select
                className="admin-select w-full px-3 py-2.5"
                value={source}
                onChange={(event) => setSource(event.target.value as (typeof SOURCE_OPTIONS)[number])}
              >
                {SOURCE_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {SOURCE_LABELS[option]}
                  </option>
                ))}
              </select>
              {source === 'custom' ? (
                <input
                  type="text"
                  className="admin-input w-full px-3 py-2.5 mt-2"
                  value={customSource}
                  onChange={(event) => setCustomSource(event.target.value)}
                  placeholder="自定义来源名称"
                />
              ) : null}
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <button type="button" className="btn-secondary" onClick={onClose} disabled={isSaving}>
                取消
              </button>
              <button type="submit" className="btn-primary inline-flex items-center gap-2" disabled={isSaving}>
                {isSaving ? <Loader2 size={14} className="animate-spin" /> : <Star size={14} />}
                <span>{isSaving ? '保存中...' : memory ? '更新记忆' : '创建记忆'}</span>
              </button>
            </div>
          </form>
        </SectionCard>
      </div>
    </div>
  );
};

export default MemoryForm;
