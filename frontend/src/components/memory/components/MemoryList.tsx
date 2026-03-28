import { useState } from "react";
import { Star, Edit3, Trash2 } from "lucide-react";
import type { LongTermMemory } from "../../../types";

interface MemoryListProps {
  memories: LongTermMemory[];
  onEdit: (memory: LongTermMemory) => void;
  onDelete: (id: number) => void;
}

/**
 * 记忆列表组件
 * 显示所有长期记忆
 */
const MemoryList: React.FC<MemoryListProps> = ({
  memories,
  onEdit,
  onDelete,
}) => {
  if (memories.length === 0) {
    return (
      <div className="text-center py-12">
        <Star
          size={48}
          className="mx-auto mb-4 opacity-50"
          style={{ color: "var(--text-muted)" }}
        />
        <p style={{ color: "var(--text-muted)" }}>暂无记忆</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {memories.map((memory) => (
        <MemoryCard
          key={memory.id}
          memory={memory}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
};

interface MemoryCardProps {
  memory: LongTermMemory;
  onEdit: (memory: LongTermMemory) => void;
  onDelete: (id: number) => void;
}

/**
 * 记忆卡片组件
 * 显示单条长期记忆
 */
const MemoryCard: React.FC<MemoryCardProps> = ({
  memory,
  onEdit,
  onDelete,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const content = memory.content;
  const shouldTruncate = content.length > 200 && !isExpanded;

  const getImportanceColor = (importance: number) => {
    const score = importance * 10;
    if (score >= 8) return "text-red-400";
    if (score >= 5) return "text-yellow-400";
    return "text-blue-400";
  };

  const getImportanceStars = (importance: number) => {
    const score = Math.round(importance * 10);
    return Array.from({ length: 10 }, (_, i) => (
      <Star
        key={i}
        size={14}
        fill={i < score ? "currentColor" : "none"}
        className={i < score ? getImportanceColor(importance) : "text-gray-600"}
      />
    ));
  };

  return (
    <div
      className="glass-card rounded-2xl p-6"
      style={{ border: "1px solid var(--glass-border)" }}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex items-center gap-1">
              {getImportanceStars(memory.importance)}
            </div>
            <span
              className="text-xs font-mono"
              style={{ color: "var(--text-muted)" }}
            >
              {(memory.importance * 10).toFixed(0)}/10
            </span>
            {memory.key && (
              <span
                className="px-2 py-0.5 rounded text-xs font-medium"
                style={{
                  backgroundColor: "rgba(147, 51, 234, 0.2)",
                  color: "rgba(147, 51, 234, 1)",
                }}
              >
                {memory.key}
              </span>
            )}
            {memory.source && (
              <span
                className="px-2 py-0.5 rounded text-xs"
                style={{
                  backgroundColor: "rgba(59, 130, 246, 0.2)",
                  color: "rgba(59, 130, 246, 1)",
                }}
              >
                {memory.source}
              </span>
            )}
          </div>

          <p
            className="text-sm leading-relaxed"
            style={{ color: "var(--text-primary)" }}
          >
            {shouldTruncate ? content.substring(0, 200) + "..." : content}
          </p>

          {content.length > 200 && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-sm mt-2 font-medium transition-colors"
              style={{ color: "var(--primary)" }}
            >
              {isExpanded ? "收起" : "展开"}
            </button>
          )}

          <div
            className="flex items-center gap-4 mt-4 text-xs"
            style={{ color: "var(--text-muted)" }}
          >
            <span>
              创建于 {new Date(memory.created_at).toLocaleString("zh-CN")}
            </span>
            <span>
              更新于 {new Date(memory.updated_at).toLocaleString("zh-CN")}
            </span>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => onEdit(memory)}
            className="p-2 rounded-lg transition-colors"
            style={{ color: "var(--text-secondary)" }}
            title="编辑"
          >
            <Edit3 size={16} />
          </button>
          <button
            onClick={() => onDelete(memory.id)}
            className="p-2 rounded-lg transition-colors text-red-400 hover:text-red-300"
            title="删除"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default MemoryList;
