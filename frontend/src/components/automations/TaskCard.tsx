import { Edit3, Play, Trash2 } from "lucide-react";
import SectionCard from "../admin/SectionCard";
import Switch from "../admin/Switch";
import StatusBadge from "../admin/StatusBadge";
import { formatSchedule, formatRelative, getRunTone, formatRunStatus } from "./utils";
import type { Automation } from "../../types";

interface TaskCardProps {
  automation: Automation;
  lastRunStatus?: string | null;
  onToggle: (id: number) => void;
  onEdit: (id: number) => void;
  onRun: (id: number) => void;
  onDelete: (id: number) => void;
  busy: boolean;
}

const TaskCard: React.FC<TaskCardProps> = ({
  automation,
  lastRunStatus,
  onToggle,
  onEdit,
  onRun,
  onDelete,
  busy,
}) => {
  const promptPreview = automation.prompt.length > 60
    ? `${automation.prompt.slice(0, 60)}…`
    : automation.prompt;

  return (
    <SectionCard className="p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="text-sm font-semibold truncate" style={{ color: "var(--text-primary)" }}>
            {automation.name}
          </div>
          <div className="mt-1 text-xs line-clamp-2" style={{ color: "var(--text-muted)" }}>
            {promptPreview}
          </div>
        </div>
        <Switch
          checked={automation.enabled}
          onChange={() => onToggle(automation.id)}
          ariaLabel="切换启用状态"
        />
      </div>

      <div className="grid gap-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>
        <div className="flex items-center gap-1.5">
          <span>⏰</span>
          <span>{formatSchedule(automation)}</span>
        </div>
        <div>
          下次执行: {automation.enabled ? formatRelative(automation.next_run_at) : "已停用"}
        </div>
        <div className="flex items-center gap-2">
          <span>上次执行: {formatRelative(automation.last_run_at)}</span>
          {lastRunStatus && (
            <StatusBadge tone={getRunTone(lastRunStatus)}>
              {formatRunStatus(lastRunStatus)}
            </StatusBadge>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 pt-1 border-t" style={{ borderColor: "var(--panel-border)" }}>
        <button
          type="button"
          onClick={() => onEdit(automation.id)}
          className="btn-secondary inline-flex items-center gap-1.5 text-xs px-3 py-1.5"
          disabled={busy}
        >
          <Edit3 size={14} />
          编辑
        </button>
        <button
          type="button"
          onClick={() => onRun(automation.id)}
          className="btn-secondary inline-flex items-center gap-1.5 text-xs px-3 py-1.5"
          disabled={busy}
        >
          <Play size={14} />
          立即执行
        </button>
        <button
          type="button"
          onClick={() => onDelete(automation.id)}
          className="btn-secondary inline-flex items-center gap-1.5 text-xs px-3 py-1.5"
          disabled={busy}
          style={{ marginLeft: "auto" }}
        >
          <Trash2 size={14} />
          删除
        </button>
      </div>
    </SectionCard>
  );
};

export default TaskCard;
