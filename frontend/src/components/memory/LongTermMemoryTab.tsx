import { useState, useEffect, useCallback } from "react";
import { Plus, Search, Loader2 } from "lucide-react";
import MemoryList from "./components/MemoryList";
import MemoryForm from "./components/MemoryForm";
import { getLongTermMemories, deleteLongTermMemory } from "../../services/api";
import type { LongTermMemory } from "../../types";

/**
 * 长期记忆标签页组件
 * 包含记忆列表、搜索、创建/编辑/删除功能
 */
const LongTermMemoryTab: React.FC = () => {
  const [memories, setMemories] = useState<LongTermMemory[]>([]);
  const [filteredMemories, setFilteredMemories] = useState<LongTermMemory[]>(
    [],
  );
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<
    "created_at" | "importance" | "updated_at"
  >("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [filterImportance, setFilterImportance] = useState<
    "all" | "high" | "medium" | "low"
  >("all");
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingMemory, setEditingMemory] = useState<LongTermMemory | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);

  const loadMemories = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await getLongTermMemories();
      setMemories(data);
    } catch (error) {
      console.error("Failed to load memories:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMemories();
  }, [loadMemories]);

  useEffect(() => {
    let filtered = [...memories];

    if (searchQuery) {
      filtered = filtered.filter(
        (memory) =>
          memory.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (memory.key &&
            memory.key.toLowerCase().includes(searchQuery.toLowerCase())),
      );
    }

    if (filterImportance !== "all") {
      filtered = filtered.filter((memory) => {
        const importance = memory.importance * 10;
        if (filterImportance === "high") return importance >= 8;
        if (filterImportance === "medium")
          return importance >= 5 && importance < 8;
        if (filterImportance === "low") return importance < 5;
        return true;
      });
    }

    filtered.sort((a, b) => {
      let comparison = 0;
      if (sortBy === "created_at") {
        comparison =
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      } else if (sortBy === "importance") {
        comparison = a.importance - b.importance;
      } else if (sortBy === "updated_at") {
        comparison =
          new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
      }
      return sortOrder === "asc" ? comparison : -comparison;
    });

    setFilteredMemories(filtered);
  }, [memories, searchQuery, sortBy, sortOrder, filterImportance]);

  const handleCreate = () => {
    setEditingMemory(null);
    setIsFormOpen(true);
  };

  const handleEdit = (memory: LongTermMemory) => {
    setEditingMemory(memory);
    setIsFormOpen(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteLongTermMemory(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
      setDeleteConfirm(null);
    } catch (error) {
      console.error("Failed to delete memory:", error);
    }
  };

  const handleSave = (memory: LongTermMemory) => {
    if (editingMemory) {
      setMemories((prev) => prev.map((m) => (m.id === memory.id ? memory : m)));
    } else {
      setMemories((prev) => [memory, ...prev]);
    }
    setIsFormOpen(false);
    setEditingMemory(null);
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin">
          <Loader2 size={40} className="text-primary" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <button
          onClick={handleCreate}
          className="btn-primary flex items-center gap-2"
        >
          <Plus size={16} />
          <span>创建记忆</span>
        </button>

        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2"
              style={{ color: "var(--text-muted)" }}
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索记忆..."
              className="w-full pl-10 pr-4 py-2.5 glass-input rounded-xl"
              style={{ color: "var(--text-primary)" }}
            />
          </div>
        </div>

        <select
          value={filterImportance}
          onChange={(e) =>
            setFilterImportance(
              e.target.value as "all" | "high" | "medium" | "low",
            )
          }
          className="px-4 py-2.5 glass-input rounded-xl cursor-pointer"
          style={{ color: "var(--text-primary)" }}
        >
          <option value="all">全部重要性</option>
          <option value="high">高重要性</option>
          <option value="medium">中重要性</option>
          <option value="low">低重要性</option>
        </select>

        <select
          value={`${sortBy}-${sortOrder}`}
          onChange={(e) => {
            const [sort, order] = e.target.value.split("-");
            setSortBy(sort as "created_at" | "importance" | "updated_at");
            setSortOrder(order as "asc" | "desc");
          }}
          className="px-4 py-2.5 glass-input rounded-xl cursor-pointer"
          style={{ color: "var(--text-primary)" }}
        >
          <option value="created_at-desc">最新创建</option>
          <option value="created_at-asc">最早创建</option>
          <option value="importance-desc">重要性高到低</option>
          <option value="importance-asc">重要性低到高</option>
          <option value="updated_at-desc">最新更新</option>
          <option value="updated_at-asc">最早更新</option>
        </select>
      </div>

      <div className="mb-4">
        <div
          className="flex items-center gap-2 text-sm"
          style={{ color: "var(--text-muted)" }}
        >
          <span>共 {filteredMemories.length} 条记忆</span>
          {memories.length !== filteredMemories.length && (
            <span>（从 {memories.length} 条中筛选）</span>
          )}
        </div>
      </div>

      <MemoryList
        memories={filteredMemories}
        onEdit={handleEdit}
        onDelete={(id) => setDeleteConfirm(id)}
      />

      {isFormOpen && (
        <MemoryForm
          memory={editingMemory}
          onSave={handleSave}
          onClose={() => {
            setIsFormOpen(false);
            setEditingMemory(null);
          }}
        />
      )}

      {deleteConfirm !== null && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setDeleteConfirm(null)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="glass-card rounded-2xl p-6 max-w-md w-full mx-4"
            style={{ border: "1px solid var(--glass-border)" }}
          >
            <h3
              className="text-lg font-semibold mb-4"
              style={{ color: "var(--text-primary)" }}
            >
              确认删除
            </h3>
            <p className="mb-6" style={{ color: "var(--text-secondary)" }}>
              确定要删除这条记忆吗？此操作无法撤销。
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-6 py-2.5 rounded-xl font-medium transition-colors"
                style={{ color: "var(--text-secondary)" }}
              >
                取消
              </button>
              <button
                onClick={() => handleDelete(deleteConfirm)}
                className="px-6 py-2.5 rounded-xl font-medium bg-red-500 hover:bg-red-600 text-white transition-colors"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LongTermMemoryTab;
