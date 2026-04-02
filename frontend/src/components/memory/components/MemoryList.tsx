import { useState } from 'react';
import { Edit3, Star, Trash2 } from 'lucide-react';

import type { LongTermMemory, Session } from '../../../types';
import { SectionCard } from '../../admin';

interface MemoryListProps {
  memories: LongTermMemory[];
  sessions: Session[];
  onEdit: (memory: LongTermMemory) => void;
  onDelete: (id: number) => void;
}

const formatDate = (value: string) =>
  new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });

const getImportanceTone = (importance: number) => {
  const score = Math.round(importance * 10);
  if (score >= 8) return { color: '#dc2626', label: '高' };
  if (score >= 5) return { color: '#d97706', label: '中' };
  return { color: '#2563eb', label: '低' };
};

const getSourceKind = (source?: string | null) => {
  if (!source) return '手动';
  if (source.includes('auto_extract')) return '自动提炼';
  if (source.includes('manual')) return '手动';
  return '自定义';
};

const MemoryList: React.FC<MemoryListProps> = ({ memories, sessions, onEdit, onDelete }) => {
  if (memories.length === 0) {
    return (
      <SectionCard className="py-12 text-center">
        <Star size={40} className="mx-auto mb-3" style={{ color: 'var(--text-muted)' }} />
        <p style={{ color: 'var(--text-muted)' }}>还没有长期记忆，先创建一条来积累长期上下文吧。</p>
      </SectionCard>
    );
  }

  return (
    <div className="grid gap-3">
      {memories.map((memory) => (
        <MemoryCard key={memory.id} memory={memory} sessions={sessions} onEdit={onEdit} onDelete={onDelete} />
      ))}
    </div>
  );
};

interface MemoryCardProps {
  memory: LongTermMemory;
  sessions: Session[];
  onEdit: (memory: LongTermMemory) => void;
  onDelete: (id: number) => void;
}

const MemoryCard: React.FC<MemoryCardProps> = ({ memory, sessions, onEdit, onDelete }) => {
  const [expanded, setExpanded] = useState(false);
  const shouldTruncate = memory.content.length > 220 && !expanded;
  const tone = getImportanceTone(memory.importance);
  const score = Math.round(memory.importance * 10);
  const sessionName = memory.session_id
    ? sessions.find((session) => session.id === memory.session_id)?.name || `工作会话 ${memory.session_id}`
    : '全局';

  return (
    <SectionCard className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-semibold"
              style={{
                backgroundColor: 'var(--surface-subtle)',
                color: tone.color,
                border: '1px solid var(--panel-border)',
              }}
            >
              <Star size={12} />
              <span>重要度 {score}/10（{tone.label}）</span>
            </span>
            {memory.key ? (
              <span className="px-2 py-0.5 rounded-md text-xs" style={{ backgroundColor: 'var(--surface-subtle)', color: 'var(--text-secondary)' }}>
                标签：{memory.key}
              </span>
            ) : null}
            <span className="px-2 py-0.5 rounded-md text-xs" style={{ backgroundColor: 'var(--surface-subtle)', color: 'var(--text-secondary)' }}>
              会话：{sessionName}
            </span>
            <span className="px-2 py-0.5 rounded-md text-xs" style={{ backgroundColor: 'var(--surface-subtle)', color: 'var(--text-secondary)' }}>
              类型：{getSourceKind(memory.source)}
            </span>
            {memory.source ? (
              <span className="px-2 py-0.5 rounded-md text-xs" style={{ backgroundColor: 'var(--surface-subtle)', color: 'var(--text-secondary)' }}>
                来源：{memory.source}
              </span>
            ) : null}
          </div>

          <p className="text-sm leading-7" style={{ color: 'var(--text-primary)' }}>
            {shouldTruncate ? `${memory.content.slice(0, 220)}...` : memory.content}
          </p>

          {memory.content.length > 220 ? (
            <button
              type="button"
              className="mt-1 text-xs font-semibold"
              style={{ color: 'var(--accent)' }}
              onClick={() => setExpanded((prev) => !prev)}
            >
              {expanded ? '收起' : '展开'}
            </button>
          ) : null}

          <div className="mt-3 text-xs flex flex-wrap gap-3" style={{ color: 'var(--text-muted)' }}>
            <span>创建时间：{formatDate(memory.created_at)}</span>
            <span>更新时间：{formatDate(memory.updated_at)}</span>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            type="button"
            className="p-2 rounded-lg"
            style={{ color: 'var(--text-secondary)' }}
            onClick={() => onEdit(memory)}
            title="编辑记忆"
          >
            <Edit3 size={16} />
          </button>
          <button
            type="button"
            className="p-2 rounded-lg"
            style={{ color: '#dc2626' }}
            onClick={() => onDelete(memory.id)}
            title="删除记忆"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>
    </SectionCard>
  );
};

export default MemoryList;
