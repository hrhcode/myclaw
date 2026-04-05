import { useMemo } from "react";
import { Plus, RefreshCw } from "lucide-react";
import TaskCard from "./TaskCard";
import { summaryCards } from "./utils";
import type { Automation, AutomationRun, AutomationStats, Conversation } from "../../types";

interface TaskListTabProps {
  automations: Automation[];
  stats: AutomationStats;
  conversations: Conversation[];
  latestRuns: Map<number, AutomationRun>;
  busy: boolean;
  onCreate: () => void;
  onRefresh: () => void;
  onToggle: (id: number) => void;
  onEdit: (id: number) => void;
  onRun: (id: number) => void;
  onDelete: (id: number) => void;
}

const TaskListTab: React.FC<TaskListTabProps> = ({
  automations,
  stats,
  latestRuns,
  busy,
  onCreate,
  onRefresh,
  onToggle,
  onEdit,
  onRun,
  onDelete,
}) => {
  const sortedAutomations = useMemo(
    () => [...automations].sort((a, b) => {
      // Enabled first, then by updated_at desc
      if (a.enabled !== b.enabled) return a.enabled ? -1 : 1;
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
    }),
    [automations]
  );

  return (
    <div className="grid gap-4">
      {/* Stats */}
      <section className="admin-summary">
        {summaryCards(stats).map((card) => (
          <div key={card.label} className="admin-summary-card">
            <div className="admin-summary-label">{card.label}</div>
            <div className="admin-summary-value">{card.value}</div>
            <div className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
              {card.hint}
            </div>
          </div>
        ))}
      </section>

      {/* Toolbar */}
      <div className="admin-toolbar">
        <button
          type="button"
          onClick={onRefresh}
          className="btn-secondary inline-flex items-center gap-2"
          disabled={busy}
        >
          <RefreshCw size={20} />
          刷新
        </button>
        <button
          type="button"
          onClick={onCreate}
          className="btn-primary inline-flex items-center gap-2"
          disabled={busy}
        >
          <Plus size={20} />
          新建任务
        </button>
      </div>

      {/* Card grid */}
      {sortedAutomations.length === 0 ? (
        <div
          className="rounded-2xl border border-dashed p-8 text-center text-sm"
          style={{ borderColor: "var(--panel-border)", color: "var(--text-muted)" }}
        >
          还没有自动化任务，点击"新建任务"开始创建。
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {sortedAutomations.map((automation) => {
            const lastRun = latestRuns.get(automation.id);
            return (
              <TaskCard
                key={automation.id}
                automation={automation}
                lastRunStatus={lastRun?.status}
                onToggle={onToggle}
                onEdit={onEdit}
                onRun={onRun}
                onDelete={onDelete}
                busy={busy}
              />
            );
          })}
        </div>
      )}
    </div>
  );
};

export default TaskListTab;
