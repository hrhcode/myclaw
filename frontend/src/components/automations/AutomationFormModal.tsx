import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { Clock3, X, Save } from "lucide-react";
import Switch from "../admin/Switch";
import {
  WEEKDAY_OPTIONS,
  normalizeConversationTitle,
  getDefaultAutomationPayload,
  getIntervalParts,
  buildIntervalValue,
  parseFixedParts,
  buildFixedSchedule,
} from "./utils";
import type { FixedMode } from "./utils";
import type { Automation, AutomationPayload, Conversation } from "../../types";

interface AutomationFormModalProps {
  open: boolean;
  automation: Automation | null;  // null = 新建
  conversations: Conversation[];
  onClose: () => void;
  onSave: (payload: AutomationPayload, id?: number) => Promise<void>;
}

type FormDraft = AutomationPayload & { id?: number; fixedMode: FixedMode; fixedTime: string; fixedWeekday: string; fixedDay: string };

const DEFAULT_FIXED_TIME = "09:00";

const resolveInitialDraft = (automation: Automation | null, conversations: Conversation[]): FormDraft => {
  if (automation) {
    const fixed = parseFixedParts(automation.schedule_type, automation.schedule_value);
    if (fixed) {
      return {
        ...automation,
        schedule_type: "fixed",
        schedule_value: automation.schedule_value,
        fixedMode: fixed.mode,
        fixedTime: fixed.time,
        fixedWeekday: fixed.weekday ?? "0",
        fixedDay: fixed.day ?? "1",
      };
    }
    return {
      ...automation,
      fixedMode: "daily",
      fixedTime: DEFAULT_FIXED_TIME,
      fixedWeekday: "0",
      fixedDay: "1",
    };
  }
  const def = getDefaultAutomationPayload(conversations[0]?.id);
  return {
    ...def,
    fixedMode: "daily",
    fixedTime: DEFAULT_FIXED_TIME,
    fixedWeekday: "0",
    fixedDay: "1",
  };
};

const MONTH_DAYS = Array.from({ length: 28 }, (_, i) => String(i + 1));

const AutomationFormModal: React.FC<AutomationFormModalProps> = ({
  open,
  automation,
  conversations,
  onClose,
  onSave,
}) => {
  const [draft, setDraft] = useState<FormDraft>(() => resolveInitialDraft(automation, conversations));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setDraft(resolveInitialDraft(automation, conversations));
      setError(null);
    }
  }, [open, automation, conversations]);

  if (!open) return null;

  const setDraftValue = (patch: Partial<FormDraft>) => {
    setDraft((prev) => ({ ...prev, ...patch }));
  };

  const canSave = Boolean(
    draft.name.trim() && draft.prompt.trim() && draft.conversation_id && draft.schedule_value.trim()
  );

  const handleSave = async () => {
    if (!canSave) return;
    try {
      setBusy(true);
      setError(null);

      let scheduleType = draft.schedule_type;
      let scheduleValue = draft.schedule_value;

      // 定点触发 → 映射为后端真实类型
      if (scheduleType === "fixed") {
        const result = buildFixedSchedule(draft.fixedMode, draft.fixedTime, draft.fixedWeekday, draft.fixedDay);
        scheduleType = result.schedule_type;
        scheduleValue = result.schedule_value;
      }

      await onSave(
        {
          name: draft.name.trim(),
          conversation_id: draft.conversation_id,
          prompt: draft.prompt.trim(),
          schedule_type: scheduleType,
          schedule_value: scheduleValue,
          timezone: draft.timezone,
          enabled: draft.enabled,
        },
        automation?.id,
      );
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setBusy(false);
    }
  };

  const renderScheduleEditor = () => {
    // 间隔触发：沿用现有逻辑
    if (draft.schedule_type === "interval") {
      const { amount, unit } = getIntervalParts(draft.schedule_value);
      return (
        <>
          <input
            type="number"
            min="1"
            value={amount}
            onChange={(e) => setDraftValue({ schedule_value: buildIntervalValue(e.target.value, unit) })}
            className="admin-input h-10 w-full px-3"
          />
          <select
            value={unit}
            onChange={(e) => setDraftValue({ schedule_value: buildIntervalValue(amount, e.target.value) })}
            className="admin-select h-10 w-full px-3"
          >
            <option value="minutes">分钟</option>
            <option value="hours">小时</option>
            <option value="days">天</option>
          </select>
        </>
      );
    }

    // 定点触发
    if (draft.schedule_type === "fixed") {
      return (
        <>
          {/* 频率子模式 */}
          <select
            value={draft.fixedMode}
            onChange={(e) => setDraftValue({ fixedMode: e.target.value as FixedMode })}
            className="admin-select h-10 w-full px-3"
          >
            <option value="daily">每天</option>
            <option value="weekly">每周</option>
            <option value="monthly">每月</option>
          </select>

          {/* 每周：追加星期几选择 */}
          {draft.fixedMode === "weekly" && (
            <select
              value={draft.fixedWeekday}
              onChange={(e) => setDraftValue({ fixedWeekday: e.target.value })}
              className="admin-select h-10 w-full px-3"
            >
              {WEEKDAY_OPTIONS.map((item) => (
                <option key={item.value} value={item.value}>{item.label}</option>
              ))}
            </select>
          )}

          {/* 每月：追加日期选择 */}
          {draft.fixedMode === "monthly" && (
            <select
              value={draft.fixedDay}
              onChange={(e) => setDraftValue({ fixedDay: e.target.value })}
              className="admin-select h-10 w-full px-3"
            >
              {MONTH_DAYS.map((d) => (
                <option key={d} value={d}>{d} 号</option>
              ))}
            </select>
          )}

          {/* 时间选择 */}
          <input
            type="time"
            value={draft.fixedTime}
            onChange={(e) => setDraftValue({ fixedTime: e.target.value })}
            className="admin-input h-10 w-full px-3"
          />
        </>
      );
    }

    // 兜底（理论上不会到这里）
    return (
      <input
        type="text"
        value={draft.schedule_value}
        onChange={(e) => setDraftValue({ schedule_value: e.target.value })}
        className="admin-input h-10 w-full px-3"
      />
    );
  };

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={onClose}>
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative mx-4 flex w-full max-w-2xl flex-col rounded-2xl glass-card shadow-2xl"
        style={{ border: "1px solid var(--glass-border)", maxHeight: "85vh" }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-6 py-4"
          style={{ borderBottom: "1px solid var(--glass-border)" }}
        >
          <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
            {automation ? "编辑自动化任务" : "新建自动化任务"}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 transition-colors hover:bg-white/10"
            style={{ color: "var(--text-muted)" }}
            aria-label="关闭"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {error && (
            <div className="warning-banner px-4 py-3 mb-4 text-sm" style={{ color: "var(--text-secondary)" }}>
              {error}
            </div>
          )}

          <div className="grid gap-4">
            {/* Name + Enabled */}
            <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_180px]">
              <label className="grid gap-2">
                <span className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>任务名称</span>
                <input
                  type="text"
                  value={draft.name}
                  onChange={(e) => setDraftValue({ name: e.target.value })}
                  className="admin-input h-11 px-3"
                  placeholder="例如：每日工作总结"
                />
              </label>
              <div className="grid gap-2">
                <span className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>启用状态</span>
                <div
                  className="flex h-11 items-center justify-between rounded-xl border px-3"
                  style={{ borderColor: "var(--panel-border)", background: "var(--input-bg)" }}
                >
                  <span className="text-sm" style={{ color: "var(--text-primary)" }}>
                    {draft.enabled ? "已启用" : "已停用"}
                  </span>
                  <Switch
                    checked={draft.enabled}
                    onChange={() => setDraftValue({ enabled: !draft.enabled })}
                    ariaLabel="切换启用状态"
                  />
                </div>
              </div>
            </div>

            {/* Conversation */}
            <label className="grid gap-2">
              <span className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>目标会话</span>
              <select
                value={draft.conversation_id ?? ""}
                onChange={(e) => setDraftValue({ conversation_id: Number(e.target.value) })}
                className="admin-select h-11 px-3"
              >
                <option value="" disabled>请选择目标会话</option>
                {conversations.map((c) => (
                  <option key={c.id} value={c.id}>
                    {normalizeConversationTitle(c.title)}
                  </option>
                ))}
              </select>
            </label>

            {/* Schedule */}
            <div className="grid gap-3 rounded-2xl border p-4" style={{ borderColor: "var(--panel-border)" }}>
              <div className="flex items-center gap-2 text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                <Clock3 size={20} />
                调度设置
              </div>
              <div className="grid gap-3 lg:grid-cols-[160px_minmax(0,1fr)]">
                {/* 调度方式：间隔触发 / 定点触发 */}
                <select
                  value={draft.schedule_type}
                  onChange={(e) => {
                    const nextType = e.target.value;
                    if (nextType === "interval") {
                      setDraftValue({
                        schedule_type: "interval",
                        schedule_value: "60",
                      });
                    } else {
                      setDraftValue({
                        schedule_type: "fixed",
                        fixedMode: "daily",
                        fixedTime: DEFAULT_FIXED_TIME,
                        fixedWeekday: "0",
                        fixedDay: "1",
                        schedule_value: DEFAULT_FIXED_TIME,
                      });
                    }
                  }}
                  className="admin-select h-10 px-3"
                >
                  <option value="interval">间隔触发</option>
                  <option value="fixed">定点触发</option>
                </select>

                <div className={`grid gap-3 ${
                  draft.schedule_type === "interval"
                    ? "md:grid-cols-2"
                    : draft.schedule_type === "fixed" && (draft.fixedMode === "weekly" || draft.fixedMode === "monthly")
                      ? "md:grid-cols-3"
                      : "md:grid-cols-2"
                }`}>
                  {renderScheduleEditor()}
                </div>
              </div>
            </div>

            {/* Prompt */}
            <label className="grid gap-2">
              <span className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>执行提示词</span>
              <textarea
                value={draft.prompt}
                onChange={(e) => setDraftValue({ prompt: e.target.value })}
                rows={6}
                className="admin-input min-h-[120px] resize-y px-3 py-3"
                placeholder="描述自动化执行时要让 AI 完成的任务。"
              />
            </label>
          </div>
        </div>

        {/* Footer */}
        <div
          className="flex items-center justify-end gap-3 px-6 py-4"
          style={{ borderTop: "1px solid var(--glass-border)" }}
        >
          <button
            type="button"
            onClick={onClose}
            className="glass rounded-xl px-4 py-2.5 text-sm font-medium"
            style={{ color: "var(--text-secondary)" }}
          >
            取消
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="btn-primary inline-flex items-center gap-2"
            disabled={busy || !canSave}
            style={{ opacity: busy || !canSave ? 0.5 : 1 }}
          >
            <Save size={16} />
            保存
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
};

export default AutomationFormModal;
