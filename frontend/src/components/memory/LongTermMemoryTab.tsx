import { useCallback, useEffect, useState } from 'react';
import { Loader2, Plus, Search } from 'lucide-react';

import { useApp } from '../../contexts/AppContext';
import { deleteLongTermMemory, getLongTermMemories } from '../../services/api';
import type { LongTermMemory } from '../../types';
import { SectionCard } from '../admin';
import MemoryForm from './components/MemoryForm';
import MemoryList from './components/MemoryList';

const LongTermMemoryTab: React.FC = () => {
  const { currentSessionId, sessions } = useApp();
  const [memories, setMemories] = useState<LongTermMemory[]>([]);
  const [filteredMemories, setFilteredMemories] = useState<LongTermMemory[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'created_at' | 'importance' | 'updated_at'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [filterImportance, setFilterImportance] = useState<'all' | 'high' | 'medium' | 'low'>('all');
  const [scope, setScope] = useState<'all' | 'current'>('all');
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingMemory, setEditingMemory] = useState<LongTermMemory | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);

  const loadMemories = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await getLongTermMemories(scope === 'current' ? currentSessionId || undefined : undefined);
      setMemories(data);
    } catch (error) {
      console.error('Failed to load memories:', error);
    } finally {
      setIsLoading(false);
    }
  }, [currentSessionId, scope]);

  useEffect(() => {
    loadMemories();
  }, [loadMemories]);

  useEffect(() => {
    let next = [...memories];
    const query = searchQuery.trim().toLowerCase();

    if (query) {
      next = next.filter(
        (memory) =>
          memory.content.toLowerCase().includes(query) ||
          (memory.key && memory.key.toLowerCase().includes(query)) ||
          (memory.source && memory.source.toLowerCase().includes(query)),
      );
    }

    if (filterImportance !== 'all') {
      next = next.filter((memory) => {
        const score = memory.importance * 10;
        if (filterImportance === 'high') return score >= 8;
        if (filterImportance === 'medium') return score >= 5 && score < 8;
        return score < 5;
      });
    }

    next.sort((a, b) => {
      let value = 0;
      if (sortBy === 'created_at') {
        value = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      } else if (sortBy === 'updated_at') {
        value = new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
      } else {
        value = a.importance - b.importance;
      }
      return sortOrder === 'asc' ? value : -value;
    });

    setFilteredMemories(next);
  }, [memories, searchQuery, sortBy, sortOrder, filterImportance]);

  const handleSave = (memory: LongTermMemory) => {
    setMemories((prev) =>
      editingMemory ? prev.map((item) => (item.id === memory.id ? memory : item)) : [memory, ...prev],
    );
    setIsFormOpen(false);
    setEditingMemory(null);
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteLongTermMemory(id);
      setMemories((prev) => prev.filter((item) => item.id !== id));
      setDeleteConfirm(null);
    } catch (error) {
      console.error('Failed to delete memory:', error);
    }
  };

  const sessionLabel =
    scope === 'current' && currentSessionId
      ? sessions.find((session) => session.id === currentSessionId)?.name || `工作会话 ${currentSessionId}`
      : '全部工作会话';

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 size={36} className="text-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="admin-frame">
      <div className="admin-toolbar">
        <button
          type="button"
          className="btn-primary inline-flex items-center gap-2"
          onClick={() => {
            setEditingMemory(null);
            setIsFormOpen(true);
          }}
        >
          <Plus size={16} />
          <span>新增记忆</span>
        </button>

        <div className="relative flex-1 min-w-[220px]">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2"
            style={{ color: 'var(--text-muted)' }}
          />
          <input
            type="text"
            className="admin-input w-full pl-9 pr-3 py-2.5"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="搜索记忆内容、标签或来源"
          />
        </div>

        <select className="admin-select px-3 py-2.5" value={scope} onChange={(event) => setScope(event.target.value as 'all' | 'current')}>
          <option value="all">全部工作会话</option>
          <option value="current">当前工作会话</option>
        </select>

        <select
          className="admin-select px-3 py-2.5"
          value={filterImportance}
          onChange={(event) => setFilterImportance(event.target.value as 'all' | 'high' | 'medium' | 'low')}
        >
          <option value="all">全部重要度</option>
          <option value="high">高（8-10）</option>
          <option value="medium">中（5-7）</option>
          <option value="low">低（0-4）</option>
        </select>

        <select
          className="admin-select px-3 py-2.5"
          value={`${sortBy}-${sortOrder}`}
          onChange={(event) => {
            const [nextSortBy, nextSortOrder] = event.target.value.split('-');
            setSortBy(nextSortBy as 'created_at' | 'importance' | 'updated_at');
            setSortOrder(nextSortOrder as 'asc' | 'desc');
          }}
        >
          <option value="created_at-desc">创建时间：最新优先</option>
          <option value="created_at-asc">创建时间：最早优先</option>
          <option value="updated_at-desc">更新时间：最新优先</option>
          <option value="updated_at-asc">更新时间：最早优先</option>
          <option value="importance-desc">重要度：高到低</option>
          <option value="importance-asc">重要度：低到高</option>
        </select>
      </div>

      <SectionCard className="px-3 py-2 text-sm">
        <span style={{ color: 'var(--text-muted)' }}>
          {sessionLabel}中共有 {filteredMemories.length} 条记忆
          {memories.length !== filteredMemories.length ? `（总计 ${memories.length} 条）` : ''}
        </span>
      </SectionCard>

      <MemoryList
        memories={filteredMemories}
        sessions={sessions}
        onEdit={(memory) => {
          setEditingMemory(memory);
          setIsFormOpen(true);
        }}
        onDelete={(id) => setDeleteConfirm(id)}
      />

      {isFormOpen ? (
        <MemoryForm
          memory={editingMemory}
          defaultSessionId={currentSessionId}
          onSave={handleSave}
          onClose={() => {
            setIsFormOpen(false);
            setEditingMemory(null);
          }}
        />
      ) : null}

      {deleteConfirm !== null ? (
        <div className="fixed inset-0 bg-black/45 flex items-center justify-center z-50" onClick={() => setDeleteConfirm(null)}>
          <SectionCard className="w-full max-w-md p-5 mx-4">
            <h3 className="text-base font-semibold" style={{ color: 'var(--text-primary)' }}>
              删除记忆
            </h3>
            <p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
              删除后将无法恢复。
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button type="button" className="btn-secondary" onClick={() => setDeleteConfirm(null)}>
                取消
              </button>
              <button
                type="button"
                className="px-4 py-2 rounded-xl text-sm font-semibold"
                style={{ backgroundColor: '#dc2626', color: '#fff' }}
                onClick={() => handleDelete(deleteConfirm)}
              >
                删除
              </button>
            </div>
          </SectionCard>
        </div>
      ) : null}
    </div>
  );
};

export default LongTermMemoryTab;
