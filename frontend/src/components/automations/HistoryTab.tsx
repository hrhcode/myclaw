import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { RefreshCw, ExternalLink } from "lucide-react";
import StatusBadge from "../admin/StatusBadge";
import { formatRunStatus, getRunTone } from "./utils";
import type { AutomationRun } from "../../types";

interface HistoryTabProps {
  runs: AutomationRun[];
  loading: boolean;
  busy: boolean;
  onRefresh: () => void;
}

interface DateGroup {
  date: string;
  runs: AutomationRun[];
}

const HistoryTab: React.FC<HistoryTabProps> = ({ runs, loading, busy, onRefresh }) => {
  const navigate = useNavigate();

  const groups: DateGroup[] = useMemo(() => {
    const map = new Map<string, AutomationRun[]>();
    for (const run of runs) {
      const date = new Date(run.triggered_at).toLocaleDateString("zh-CN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      });
      const existing = map.get(date);
      if (existing) {
        existing.push(run);
      } else {
        map.set(date, [run]);
      }
    }
    return Array.from(map.entries()).map(([date, runs]) => ({ date, runs }));
  }, [runs]);

  const formatTime = (value: string) => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  };

  const handleViewConversation = async (run: AutomationRun) => {
    const conversationId = run.conversation_id;
    const runId = run.run_id;

    if (conversationId && runId) {
      navigate(`/chat/${conversationId}?highlight=${runId}`);
    } else if (conversationId) {
      navigate(`/chat/${conversationId}`);
    } else if (runId) {
      // conversation_id 可能为 null（历史数据），通过 run_id 反查
      try {
        const { getAgentRunByRunId } = await import("../../services/api");
        const info = await getAgentRunByRunId(runId);
        if (info.conversation_id) {
          navigate(`/chat/${info.conversation_id}?highlight=${runId}`);
        }
      } catch {
        // 静默失败
      }
    }
  };

  return (
    <div className="grid gap-4">
      {/* Toolbar */}
      <div className="admin-toolbar">
        <button
          type="button"
          onClick={onRefresh}
          className="btn-secondary inline-flex items-center gap-2"
          disabled={busy || loading}
        >
          <RefreshCw size={20} />
          刷新
        </button>
        <div className="text-xs" style={{ color: "var(--text-muted)" }}>
          共 {runs.length} 条执行记录
        </div>
      </div>

      {/* Timeline */}
      {loading ? (
        <div
          className="admin-card p-6 text-sm text-center"
          style={{ color: "var(--text-muted)" }}
        >
          加载中...
        </div>
      ) : groups.length === 0 ? (
        <div
          className="rounded-2xl border border-dashed p-8 text-center text-sm"
          style={{ borderColor: "var(--panel-border)", color: "var(--text-muted)" }}
        >
          暂无执行记录。
        </div>
      ) : (
        <div className="grid gap-6">
          {groups.map((group) => (
            <div key={group.date}>
              <div
                className="mb-3 text-sm font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                {group.date}
              </div>
              <div className="grid gap-2">
                {group.runs.map((run) => (
                  <div
                    key={run.id}
                    className="admin-card grid gap-1 px-4 py-3"
                  >
                    <div className="flex items-center gap-4">
                      {/* Time */}
                      <div
                        className="w-12 shrink-0 text-sm font-medium"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {formatTime(run.triggered_at)}
                      </div>

                      {/* Status dot */}
                      <StatusBadge tone={getRunTone(run.status)}>
                        {formatRunStatus(run.status)}
                      </StatusBadge>

                      {/* Task name */}
                      <div
                        className="min-w-0 flex-1 text-sm font-medium truncate"
                        style={{ color: "var(--text-primary)" }}
                      >
                        {run.automation_name || `任务 #${run.automation_id}`}
                      </div>

                      {/* Trigger mode */}
                      <div
                        className="shrink-0 text-xs"
                        style={{ color: "var(--text-muted)" }}
                      >
                        {run.trigger_mode === "manual" ? "手动触发" : "定时触发"}
                      </div>

                      {/* Duration or error */}
                      <div
                        className="shrink-0 text-xs"
                        style={{ color: run.error ? "#dc2626" : "var(--text-muted)" }}
                      >
                        {run.error ? (
                          <span title={run.error}>错误</span>
                        ) : run.completed_at ? (
                          (() => {
                            const start = new Date(run.triggered_at).getTime();
                            const end = new Date(run.completed_at).getTime();
                            const seconds = Math.round((end - start) / 1000);
                            if (seconds < 60) return `${seconds}秒`;
                            return `${Math.round(seconds / 60)}分钟`;
                          })()
                        ) : (
                          "进行中"
                        )}
                      </div>

                      {/* View conversation link */}
                      {run.run_id && (
                        <button
                          type="button"
                          onClick={() => handleViewConversation(run)}
                          className="shrink-0 rounded-lg p-1.5 transition-colors hover:bg-white/10"
                          style={{ color: "var(--text-muted)" }}
                          title="查看会话"
                        >
                          <ExternalLink size={14} />
                        </button>
                      )}
                    </div>

                    {/* AI response snippet */}
                    {run.response_snippet && (
                      <div
                        className="ml-16 text-xs truncate"
                        style={{ color: "var(--text-muted)" }}
                        title={run.response_snippet}
                      >
                        {run.response_snippet}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default HistoryTab;
