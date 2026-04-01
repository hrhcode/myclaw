import { useEffect, useState } from "react";
import { Loader2, Star, X } from "lucide-react";
import { createLongTermMemory, updateLongTermMemory } from "../../../services/api";
import type { LongTermMemory } from "../../../types";
import { SectionCard } from "../../admin";

interface MemoryFormProps {
  memory: LongTermMemory | null;
  onSave: (memory: LongTermMemory) => void;
  onClose: () => void;
}

const SOURCE_OPTIONS = ["用户手动添加", "对话总结", "系统自动提取", "自定义"] as const;

const MemoryForm: React.FC<MemoryFormProps> = ({ memory, onSave, onClose }) => {
  const [content, setContent] = useState("");
  const [key, setKey] = useState("");
  const [importance, setImportance] = useState(0.5);
  const [source, setSource] = useState<(typeof SOURCE_OPTIONS)[number]>("用户手动添加");
  const [customSource, setCustomSource] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!memory) return;
    setContent(memory.content);
    setKey(memory.key || "");
    setImportance(memory.importance);
    const value = memory.source || "用户手动添加";
    if (SOURCE_OPTIONS.includes(value as (typeof SOURCE_OPTIONS)[number])) {
      setSource(value as (typeof SOURCE_OPTIONS)[number]);
      setCustomSource("");
    } else {
      setSource("自定义");
      setCustomSource(value);
    }
  }, [memory]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!content.trim()) {
      setError("记忆内容不能为空");
      return;
    }
    if (content.length > 5000) {
      setError("记忆内容不能超过 5000 字");
      return;
    }

    try {
      setIsSaving(true);
      setError("");
      const finalSource = source === "自定义" ? customSource.trim() : source;
      const payload = {
        content: content.trim(),
        key: key.trim() || undefined,
        importance,
        source: finalSource || undefined,
      };
      const saved = memory
        ? await updateLongTermMemory(memory.id, payload)
        : await createLongTermMemory(payload.content, payload.key, payload.importance, payload.source);
      onSave(saved);
    } catch (err) {
      console.error("Failed to save memory:", err);
      setError("保存失败，请稍后重试");
    } finally {
      setIsSaving(false);
    }
  };

  const score = Math.round(importance * 10);

  return (
    <div className="fixed inset-0 bg-black/45 flex items-center justify-center z-50" onClick={onClose}>
      <SectionCard className="w-full max-w-2xl max-h-[90vh] overflow-y-auto p-5 mx-4" >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
            {memory ? "编辑记忆" : "新建记忆"}
          </h2>
          <button type="button" className="p-2 rounded-lg" style={{ color: "var(--text-secondary)" }} onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm mb-1" style={{ color: "var(--text-secondary)" }}>
              内容
            </label>
            <textarea
              rows={6}
              maxLength={5000}
              className="admin-input w-full px-3 py-2.5 resize-none"
              value={content}
              onChange={(event) => setContent(event.target.value)}
              placeholder="输入要保存的长期记忆"
            />
            <div className="mt-1 flex items-center justify-between text-xs">
              <span style={{ color: "#dc2626" }}>{error}</span>
              <span style={{ color: "var(--text-muted)" }}>{content.length}/5000</span>
            </div>
          </div>

          <div>
            <label className="block text-sm mb-1" style={{ color: "var(--text-secondary)" }}>
              标签
            </label>
            <input
              type="text"
              className="admin-input w-full px-3 py-2.5"
              value={key}
              onChange={(event) => setKey(event.target.value)}
              placeholder="例如：偏好, 目标, 项目"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm" style={{ color: "var(--text-secondary)" }}>
                重要性
              </label>
              <span className="text-xs font-mono inline-flex items-center gap-1" style={{ color: "var(--text-primary)" }}>
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
            <label className="block text-sm mb-1" style={{ color: "var(--text-secondary)" }}>
              来源
            </label>
            <select
              className="admin-select w-full px-3 py-2.5"
              value={source}
              onChange={(event) => setSource(event.target.value as (typeof SOURCE_OPTIONS)[number])}
            >
              {SOURCE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {source === "自定义" ? (
              <input
                type="text"
                className="admin-input w-full px-3 py-2.5 mt-2"
                value={customSource}
                onChange={(event) => setCustomSource(event.target.value)}
                placeholder="输入自定义来源"
              />
            ) : null}
          </div>

          <div className="pt-2 flex justify-end gap-2">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={isSaving}>
              取消
            </button>
            <button type="submit" className="btn-primary inline-flex items-center gap-2" disabled={isSaving}>
              {isSaving ? <Loader2 size={14} className="animate-spin" /> : <Star size={14} />}
              <span>{isSaving ? "保存中..." : memory ? "更新记忆" : "创建记忆"}</span>
            </button>
          </div>
        </form>
      </SectionCard>
    </div>
  );
};

export default MemoryForm;
