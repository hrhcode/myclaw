import { useState, useEffect } from "react";
import { Star, X, Loader2 } from "lucide-react";
import {
  createLongTermMemory,
  updateLongTermMemory,
} from "../../../services/api";
import type { LongTermMemory } from "../../../types";

interface MemoryFormProps {
  memory: LongTermMemory | null;
  onSave: (memory: LongTermMemory) => void;
  onClose: () => void;
}

/**
 * 记忆表单组件
 * 用于创建和编辑长期记忆
 */
const MemoryForm: React.FC<MemoryFormProps> = ({ memory, onSave, onClose }) => {
  const [content, setContent] = useState("");
  const [key, setKey] = useState("");
  const [importance, setImportance] = useState(0.5);
  const [source, setSource] = useState("用户手动添加");
  const [customSource, setCustomSource] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (memory) {
      setContent(memory.content);
      setKey(memory.key || "");
      setImportance(memory.importance);
      setSource(memory.source || "用户手动添加");
    }
  }, [memory]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!content.trim()) {
      setError("记忆内容不能为空");
      return;
    }

    if (content.length > 5000) {
      setError("记忆内容不能超过5000字");
      return;
    }

    try {
      setIsSaving(true);
      setError("");

      const finalSource = source === "自定义" ? customSource : source;

      let savedMemory: LongTermMemory;

      if (memory) {
        savedMemory = await updateLongTermMemory(memory.id, {
          content,
          key: key || undefined,
          importance,
          source: finalSource || undefined,
        });
      } else {
        savedMemory = await createLongTermMemory(
          content,
          key || undefined,
          importance,
          finalSource || undefined,
        );
      }

      onSave(savedMemory);
    } catch (error) {
      console.error("Failed to save memory:", error);
      setError("保存失败，请重试");
    } finally {
      setIsSaving(false);
    }
  };

  const getImportanceStars = (value: number) => {
    const score = Math.round(value * 10);
    return Array.from({ length: 10 }, (_, i) => (
      <Star
        key={i}
        size={16}
        fill={i < score ? "currentColor" : "none"}
        className={i < score ? "text-yellow-400" : "text-gray-600"}
      />
    ));
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="glass-card rounded-2xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        style={{ border: "1px solid var(--glass-border)" }}
      >
        <div className="flex items-center justify-between mb-6">
          <h2
            className="text-xl font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            {memory ? "编辑记忆" : "创建记忆"}
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg transition-colors"
            style={{ color: "var(--text-secondary)" }}
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label
              className="block text-sm font-medium mb-2"
              style={{ color: "var(--text-secondary)" }}
            >
              记忆内容 <span className="text-red-400">*</span>
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="输入要保存的记忆内容..."
              rows={6}
              maxLength={5000}
              className="w-full px-4 py-3 glass-input rounded-xl resize-none"
              style={{ color: "var(--text-primary)" }}
            />
            <div className="flex justify-between mt-2">
              {error && <span className="text-sm text-red-400">{error}</span>}
              <span className="text-sm" style={{ color: "var(--text-muted)" }}>
                {content.length}/5000
              </span>
            </div>
          </div>

          <div>
            <label
              className="block text-sm font-medium mb-2"
              style={{ color: "var(--text-secondary)" }}
            >
              记忆标签/关键词
            </label>
            <input
              type="text"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="输入标签或关键词，用逗号分隔"
              className="w-full px-4 py-3 glass-input rounded-xl"
              style={{ color: "var(--text-primary)" }}
            />
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              便于记忆的分类和检索
            </p>
          </div>

          <div>
            <label
              className="block text-sm font-medium mb-2"
              style={{ color: "var(--text-secondary)" }}
            >
              重要性评分 <span className="text-red-400">*</span>
            </label>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                {getImportanceStars(importance)}
                <span
                  className="text-sm font-mono"
                  style={{ color: "var(--primary)" }}
                >
                  {(importance * 10).toFixed(0)}/10
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={importance}
                onChange={(e) => setImportance(parseFloat(e.target.value))}
                className="w-full h-2 rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, var(--primary) 0%, var(--primary) ${
                    importance * 100
                  }%, var(--glass-border) ${importance * 100}%, var(--glass-border) 100%)`,
                }}
              />
            </div>
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              记忆的重要程度，影响搜索结果的排序
            </p>
          </div>

          <div>
            <label
              className="block text-sm font-medium mb-2"
              style={{ color: "var(--text-secondary)" }}
            >
              来源
            </label>
            <select
              value={source}
              onChange={(e) => {
                setSource(e.target.value);
                if (e.target.value !== "自定义") {
                  setCustomSource("");
                }
              }}
              className="w-full px-4 py-3 glass-input rounded-xl appearance-none cursor-pointer"
              style={{ color: "var(--text-primary)" }}
            >
              <option value="用户手动添加">用户手动添加</option>
              <option value="对话总结">对话总结</option>
              <option value="系统自动提取">系统自动提取</option>
              <option value="自定义">自定义</option>
            </select>

            {source === "自定义" && (
              <input
                type="text"
                value={customSource}
                onChange={(e) => setCustomSource(e.target.value)}
                placeholder="输入自定义来源"
                className="w-full px-4 py-3 glass-input rounded-xl mt-3"
                style={{ color: "var(--text-primary)" }}
              />
            )}
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={isSaving}
              className="px-6 py-2.5 rounded-xl font-medium transition-colors"
              style={{ color: "var(--text-secondary)" }}
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="btn-primary flex items-center gap-2 px-6 py-2.5"
            >
              {isSaving ? (
                <>
                  <div className="animate-spin">
                    <Loader2 size={18} />
                  </div>
                  <span>保存中...</span>
                </>
              ) : (
                <>
                  <Star size={18} />
                  <span>{memory ? "更新记忆" : "创建记忆"}</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MemoryForm;
