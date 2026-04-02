import { useEffect, useState } from 'react';
import { Clock3, Copy, Play, Plus, RefreshCw, Save, Trash2 } from 'lucide-react';

import MainLayout from '../layout/MainLayout';
import {
  createAutomation,
  deleteAutomation,
  getAutomationRuns,
  getAutomations,
  getAutomationStats,
  getSessions,
  runAutomationNow,
  updateAutomation,
} from '../../services/api';
import type {
  Automation,
  AutomationPayload,
  AutomationRun,
  AutomationStats,
  Session,
} from '../../types';

const WEEKDAY_OPTIONS = [
  { value: '0', label: '周一' },
  { value: '1', label: '周二' },
  { value: '2', label: '周三' },
  { value: '3', label: '周四' },
  { value: '4', label: '周五' },
  { value: '5', label: '周六' },
  { value: '6', label: '周日' },
];

const TIMEZONE_SUGGESTIONS = ['Asia/Shanghai', 'UTC', 'Asia/Tokyo', 'America/Los_Angeles', 'Europe/London'];

const guessTimezone = () => {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Shanghai';
  } catch {
    return 'Asia/Shanghai';
  }
};

const getDefaultAutomationPayload = (sessionId?: number): AutomationPayload => ({
  name: '新自动化任务',
  session_id: sessionId,
  prompt: '总结最近进展，并给出当前最值得执行的下一步建议。',
  schedule_type: 'interval',
  schedule_value: '60',
  timezone: guessTimezone(),
  enabled: true,
});

const formatDateTime = (value?: string | null) => {
  if (!value) return '未设置';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
};

const formatRelative = (value?: string | null) => {
  if (!value) return '暂无';
  const timestamp = new Date(value).getTime();
  if (Number.isNaN(timestamp)) return value;
  const deltaMinutes = Math.round((timestamp - Date.now()) / 60000);
  if (Math.abs(deltaMinutes) < 1) return '刚刚';
  if (Math.abs(deltaMinutes) < 60) return deltaMinutes > 0 ? `${deltaMinutes} 分钟后` : `${Math.abs(deltaMinutes)} 分钟前`;
  const deltaHours = Math.round(deltaMinutes / 60);
  if (Math.abs(deltaHours) < 24) return deltaHours > 0 ? `${deltaHours} 小时后` : `${Math.abs(deltaHours)} 小时前`;
  const deltaDays = Math.round(deltaHours / 24);
  return deltaDays > 0 ? `${deltaDays} 天后` : `${Math.abs(deltaDays)} 天前`;
};

const getIntervalParts = (scheduleValue: string) => {
  const minutes = Number.parseInt(scheduleValue, 10);
  if (!Number.isFinite(minutes) || minutes <= 0) {
    return { amount: '60', unit: 'minutes' as const };
  }
  if (minutes % 1440 === 0) {
    return { amount: String(minutes / 1440), unit: 'days' as const };
  }
  if (minutes % 60 === 0) {
    return { amount: String(minutes / 60), unit: 'hours' as const };
  }
  return { amount: String(minutes), unit: 'minutes' as const };
};

const buildIntervalValue = (amountText: string, unit: string) => {
  const amount = Math.max(Number.parseInt(amountText || '0', 10) || 0, 1);
  if (unit === 'days') return String(amount * 1440);
  if (unit === 'hours') return String(amount * 60);
  return String(amount);
};

const getWeeklyParts = (scheduleValue: string) => {
  const [weekday = '0', time = '09:00'] = scheduleValue.split('|');
  return { weekday, time };
};

const getOnceInputValue = (scheduleValue: string) => {
  const date = new Date(scheduleValue);
  if (Number.isNaN(date.getTime())) return '';
  const offset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - offset * 60000);
  return local.toISOString().slice(0, 16);
};

const buildOnceValue = (localValue: string, timezone: string) => {
  if (!localValue) return '';
  if (timezone === 'UTC') {
    return `${localValue}:00Z`;
  }
  return localValue;
};

const formatSchedule = (automation: Automation) => {
  if (automation.schedule_type === 'once') {
    return `单次执行 · ${formatDateTime(automation.schedule_value)}`;
  }
  if (automation.schedule_type === 'interval') {
    const { amount, unit } = getIntervalParts(automation.schedule_value);
    const unitLabel = unit === 'days' ? '天' : unit === 'hours' ? '小时' : '分钟';
    return `每 ${amount} ${unitLabel}`;
  }
  if (automation.schedule_type === 'daily') {
    return `每天 ${automation.schedule_value}`;
  }
  if (automation.schedule_type === 'weekly') {
    const { weekday, time } = getWeeklyParts(automation.schedule_value);
    const weekdayLabel = WEEKDAY_OPTIONS.find((item) => item.value === weekday)?.label ?? `周${weekday}`;
    return `${weekdayLabel} ${time}`;
  }
  return `Cron · ${automation.schedule_value}`;
};

const formatRunStatus = (status: string) => {
  if (status === 'success') return '成功';
  if (status === 'failed') return '失败';
  if (status === 'running') return '执行中';
  return status;
};

const metricCards = (stats: AutomationStats) => [
  { label: '自动化总数', value: stats.total, hint: `${stats.enabled} 启用 / ${stats.disabled} 停用` },
  { label: '当前运行', value: stats.running, hint: stats.due_now > 0 ? `${stats.due_now} 个任务已到执行时间` : '暂无到点任务' },
  { label: '最近失败', value: stats.failed_recently, hint: stats.last_run_at ? `最近一次执行 ${formatRelative(stats.last_run_at)}` : '暂无执行记录' },
  { label: '下一次调度', value: stats.next_run_at ? formatRelative(stats.next_run_at) : '暂无', hint: stats.next_run_at ? formatDateTime(stats.next_run_at) : '没有启用中的未来任务' },
];

const AutomationsPage: React.FC = () => {
  const [automations, setAutomations] = useState<Automation[]>([]);
  const [stats, setStats] = useState<AutomationStats>({
    total: 0,
    enabled: 0,
    disabled: 0,
    due_now: 0,
    running: 0,
    failed_recently: 0,
    next_run_at: null,
    last_run_at: null,
  });
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedAutomationId, setSelectedAutomationId] = useState<number | null>(null);
  const [draft, setDraft] = useState<Automation | null>(null);
  const [runs, setRuns] = useState<AutomationRun[]>([]);
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'enabled' | 'disabled'>('all');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const selectedAutomation = automations.find((item) => item.id === selectedAutomationId) || null;
  const visibleAutomations = automations.filter((item) => {
    const matchesQuery =
      item.name.toLowerCase().includes(query.toLowerCase()) ||
      item.prompt.toLowerCase().includes(query.toLowerCase());
    const matchesStatus =
      statusFilter === 'all' || (statusFilter === 'enabled' ? item.enabled : !item.enabled);
    return matchesQuery && matchesStatus;
  });

  const refreshPage = async (preferredAutomationId?: number | null) => {
    const [automationData, statsData, sessionsData] = await Promise.all([
      getAutomations(),
      getAutomationStats(),
      getSessions(),
    ]);
    setAutomations(automationData);
    setStats(statsData);
    setSessions(sessionsData);
    setSelectedAutomationId((previousId) => {
      const nextId = preferredAutomationId ?? previousId;
      if (nextId && automationData.some((item) => item.id === nextId)) {
        return nextId;
      }
      return automationData[0]?.id ?? null;
    });
  };

  useEffect(() => {
    void (async () => {
      try {
        await refreshPage();
      } catch (loadError) {
        console.error('Failed to load automations', loadError);
        setError(loadError instanceof Error ? loadError.message : '加载自动化失败');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    setDraft(selectedAutomation ? { ...selectedAutomation } : null);
  }, [selectedAutomationId, selectedAutomation?.updated_at]);

  useEffect(() => {
    if (!selectedAutomationId) {
      setRuns([]);
      return;
    }
    void getAutomationRuns(selectedAutomationId)
      .then(setRuns)
      .catch((loadError) => {
        console.error('Failed to load automation runs', loadError);
        setError(loadError instanceof Error ? loadError.message : '加载运行记录失败');
      });
  }, [selectedAutomationId]);

  const setDraftValue = (patch: Partial<Automation>) => {
    setDraft((current) => (current ? { ...current, ...patch } : current));
  };

  const selectAutomation = (automationId: number) => {
    setNotice(null);
    setError(null);
    setSelectedAutomationId(automationId);
  };

  const handleCreate = async () => {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const defaultSessionId = sessions.find((item) => item.is_default)?.id ?? sessions[0]?.id;
      const created = await createAutomation(getDefaultAutomationPayload(defaultSessionId));
      await refreshPage(created.id);
      setNotice('已创建新的自动化任务。');
    } catch (createError) {
      console.error('Failed to create automation', createError);
      setError(createError instanceof Error ? createError.message : '创建自动化失败');
    } finally {
      setBusy(false);
    }
  };

  const handleClone = async () => {
    if (!draft) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const created = await createAutomation({
        name: `${draft.name}（副本）`,
        session_id: draft.session_id,
        prompt: draft.prompt,
        schedule_type: draft.schedule_type,
        schedule_value: draft.schedule_value,
        timezone: draft.timezone,
        enabled: draft.enabled,
      });
      await refreshPage(created.id);
      setNotice('已复制当前自动化任务。');
    } catch (cloneError) {
      console.error('Failed to clone automation', cloneError);
      setError(cloneError instanceof Error ? cloneError.message : '复制自动化失败');
    } finally {
      setBusy(false);
    }
  };

  const handleSave = async () => {
    if (!draft) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await updateAutomation(draft.id, {
        name: draft.name,
        session_id: draft.session_id,
        prompt: draft.prompt,
        schedule_type: draft.schedule_type,
        schedule_value: draft.schedule_value,
        timezone: draft.timezone,
        enabled: draft.enabled,
      });
      await refreshPage(updated.id);
      setNotice('自动化配置已保存。');
    } catch (saveError) {
      console.error('Failed to save automation', saveError);
      setError(saveError instanceof Error ? saveError.message : '保存自动化失败');
    } finally {
      setBusy(false);
    }
  };

  const handleRunNow = async () => {
    if (!draft) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const result = await runAutomationNow(draft.id);
      await refreshPage(draft.id);
      setRuns(await getAutomationRuns(draft.id));
      setNotice(result.run_id ? `已触发手动执行，运行编号 ${result.run_id}。` : '已触发手动执行。');
    } catch (runError) {
      console.error('Failed to run automation', runError);
      setError(runError instanceof Error ? runError.message : '触发执行失败');
    } finally {
      setBusy(false);
    }
  };

  const handleToggleEnabled = async () => {
    if (!draft) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await updateAutomation(draft.id, { enabled: !draft.enabled });
      await refreshPage(updated.id);
      setNotice(updated.enabled ? '已启用自动化任务。' : '已停用自动化任务。');
    } catch (toggleError) {
      console.error('Failed to toggle automation', toggleError);
      setError(toggleError instanceof Error ? toggleError.message : '切换自动化状态失败');
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    if (!draft) return;
    if (!window.confirm(`确定删除自动化任务“${draft.name}”吗？`)) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await deleteAutomation(draft.id);
      await refreshPage(null);
      setNotice('自动化任务已删除。');
    } catch (deleteError) {
      console.error('Failed to delete automation', deleteError);
      setError(deleteError instanceof Error ? deleteError.message : '删除自动化失败');
    } finally {
      setBusy(false);
    }
  };

  const renderScheduleEditor = () => {
    if (!draft) return null;

    if (draft.schedule_type === 'interval') {
      const intervalParts = getIntervalParts(draft.schedule_value);
      return (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-[1fr,180px]">
          <label className="space-y-2">
            <span className="text-sm font-medium text-[var(--text-primary)]">间隔数值</span>
            <input
              className="admin-input w-full px-3 py-2"
              value={intervalParts.amount}
              onChange={(event) =>
                setDraftValue({
                  schedule_value: buildIntervalValue(event.target.value, intervalParts.unit),
                })
              }
            />
          </label>
          <label className="space-y-2">
            <span className="text-sm font-medium text-[var(--text-primary)]">时间单位</span>
            <select
              className="admin-select w-full px-3 py-2"
              value={intervalParts.unit}
              onChange={(event) =>
                setDraftValue({
                  schedule_value: buildIntervalValue(intervalParts.amount, event.target.value),
                })
              }
            >
              <option value="minutes">分钟</option>
              <option value="hours">小时</option>
              <option value="days">天</option>
            </select>
          </label>
        </div>
      );
    }

    if (draft.schedule_type === 'daily') {
      return (
        <label className="space-y-2">
          <span className="text-sm font-medium text-[var(--text-primary)]">每天执行时间</span>
          <input
            type="time"
            className="admin-input w-full px-3 py-2"
            value={draft.schedule_value}
            onChange={(event) => setDraftValue({ schedule_value: event.target.value })}
          />
        </label>
      );
    }

    if (draft.schedule_type === 'weekly') {
      const { weekday, time } = getWeeklyParts(draft.schedule_value);
      return (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-[180px,1fr]">
          <label className="space-y-2">
            <span className="text-sm font-medium text-[var(--text-primary)]">星期</span>
            <select
              className="admin-select w-full px-3 py-2"
              value={weekday}
              onChange={(event) => setDraftValue({ schedule_value: `${event.target.value}|${time}` })}
            >
              {WEEKDAY_OPTIONS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-2">
            <span className="text-sm font-medium text-[var(--text-primary)]">执行时间</span>
            <input
              type="time"
              className="admin-input w-full px-3 py-2"
              value={time}
              onChange={(event) => setDraftValue({ schedule_value: `${weekday}|${event.target.value}` })}
            />
          </label>
        </div>
      );
    }

    if (draft.schedule_type === 'once') {
      return (
        <label className="space-y-2">
          <span className="text-sm font-medium text-[var(--text-primary)]">执行时间</span>
          <input
            type="datetime-local"
            className="admin-input w-full px-3 py-2"
            value={getOnceInputValue(draft.schedule_value)}
            onChange={(event) =>
              setDraftValue({ schedule_value: buildOnceValue(event.target.value, draft.timezone) })
            }
          />
        </label>
      );
    }

    return (
      <label className="space-y-2">
        <span className="text-sm font-medium text-[var(--text-primary)]">Cron 表达式</span>
        <input
          className="admin-input w-full px-3 py-2"
          value={draft.schedule_value}
          onChange={(event) => setDraftValue({ schedule_value: event.target.value })}
          placeholder="0 9 * * 1-5"
        />
      </label>
    );
  };

  return (
    <MainLayout
      headerTitle="自动化"
      headerSubtitle="像控制台一样管理定时任务、执行会话和运行历史。"
      headerActions={
        <div className="flex flex-wrap gap-2">
          <button type="button" className="btn" onClick={() => void refreshPage(selectedAutomationId)} disabled={busy}>
            <RefreshCw size={14} />
            刷新
          </button>
          <button type="button" className="btn primary" onClick={() => void handleCreate()} disabled={busy}>
            <Plus size={14} />
            新建自动化
          </button>
        </div>
      }
    >
      <div className="admin-page">
        <div className="admin-frame flex h-full flex-col gap-4 overflow-y-auto p-4">
          {error ? <div className="callout danger text-sm">{error}</div> : null}
          {notice ? <div className="callout text-sm">{notice}</div> : null}

          <section className="grid grid-cols-1 gap-4 xl:grid-cols-4">
            {metricCards(stats).map((card) => (
              <div key={card.label} className="admin-summary-card rounded-2xl p-4">
                <div className="text-xs uppercase tracking-[0.16em] text-[var(--text-muted)]">{card.label}</div>
                <div className="mt-3 text-2xl font-semibold text-[var(--text-primary)]">{card.value}</div>
                <div className="mt-2 text-sm text-[var(--text-muted)]">{card.hint}</div>
              </div>
            ))}
          </section>

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-[360px,1fr]">
            <aside className="admin-card rounded-3xl p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-lg font-semibold text-[var(--text-primary)]">任务列表</div>
                  <div className="text-sm text-[var(--text-muted)]">快速筛选、定位和操作你的自动化。</div>
                </div>
                <div className="rounded-full border border-[var(--panel-border)] px-3 py-1 text-xs text-[var(--text-muted)]">
                  {visibleAutomations.length} / {automations.length}
                </div>
              </div>

              <div className="mt-4 space-y-3">
                <input
                  className="admin-input w-full px-3 py-2"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="搜索名称或提示词"
                />
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { value: 'all', label: '全部' },
                    { value: 'enabled', label: '启用中' },
                    { value: 'disabled', label: '已停用' },
                  ].map((item) => (
                    <button
                      key={item.value}
                      type="button"
                      className="btn-secondary"
                      style={{
                        background: statusFilter === item.value ? 'var(--accent-soft)' : undefined,
                        borderColor: statusFilter === item.value ? 'var(--accent)' : undefined,
                        color: statusFilter === item.value ? 'var(--text-primary)' : undefined,
                      }}
                      onClick={() => setStatusFilter(item.value as typeof statusFilter)}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="mt-4 space-y-3">
                {loading ? (
                  <div className="rounded-2xl border border-[var(--panel-border)] p-4 text-sm text-[var(--text-muted)]">
                    正在加载自动化任务...
                  </div>
                ) : null}
                {!loading && visibleAutomations.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-[var(--panel-border)] p-4 text-sm text-[var(--text-muted)]">
                    当前筛选条件下没有任务。
                  </div>
                ) : null}
                {visibleAutomations.map((automation) => {
                  const session = sessions.find((item) => item.id === automation.session_id);
                  const isSelected = automation.id === selectedAutomationId;
                  return (
                    <button
                      key={automation.id}
                      type="button"
                      className="w-full rounded-2xl border p-4 text-left transition"
                      style={{
                        borderColor: isSelected ? 'var(--accent)' : 'var(--panel-border)',
                        background: isSelected ? 'var(--accent-soft)' : 'var(--bg-secondary)',
                      }}
                      onClick={() => selectAutomation(automation.id)}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="truncate font-semibold text-[var(--text-primary)]">{automation.name}</div>
                          <div className="mt-1 text-xs text-[var(--text-muted)]">{formatSchedule(automation)}</div>
                        </div>
                        <span
                          className="rounded-full px-2 py-1 text-[11px]"
                          style={{
                            background: automation.enabled ? 'rgba(34,197,94,0.14)' : 'rgba(239,68,68,0.12)',
                            color: automation.enabled ? '#22c55e' : '#ef4444',
                          }}
                        >
                          {automation.enabled ? '启用' : '停用'}
                        </span>
                      </div>
                      <div className="mt-3 grid gap-1 text-xs text-[var(--text-muted)]">
                        <div>会话：{session?.name || `#${automation.session_id}`}</div>
                        <div>下次执行：{formatDateTime(automation.next_run_at)}</div>
                        <div>最近执行：{formatDateTime(automation.last_run_at)}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </aside>

            <section className="space-y-4">
              {draft ? (
                <>
                  <div className="glass-card rounded-3xl p-5">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <div className="text-xl font-semibold text-[var(--text-primary)]">{draft.name}</div>
                        <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-[var(--text-muted)]">
                          <span className="inline-flex items-center gap-1">
                            <Clock3 size={14} />
                            {formatSchedule(draft)}
                          </span>
                          <span>时区：{draft.timezone}</span>
                          <span>下次执行：{formatRelative(draft.next_run_at)}</span>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button type="button" className="btn" onClick={() => void handleClone()} disabled={busy}>
                          <Copy size={14} />
                          复制
                        </button>
                        <button type="button" className="btn" onClick={() => void handleRunNow()} disabled={busy}>
                          <Play size={14} />
                          立即执行
                        </button>
                        <button type="button" className="btn" onClick={() => void handleToggleEnabled()} disabled={busy}>
                          {draft.enabled ? '停用' : '启用'}
                        </button>
                        <button type="button" className="btn primary" onClick={() => void handleSave()} disabled={busy}>
                          <Save size={14} />
                          保存
                        </button>
                        <button type="button" className="btn" onClick={() => void handleDelete()} disabled={busy}>
                          <Trash2 size={14} />
                          删除
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 gap-4 2xl:grid-cols-[1.2fr,0.8fr]">
                    <div className="glass-card rounded-3xl p-5">
                      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                        <label className="space-y-2 lg:col-span-2">
                          <span className="text-sm font-medium text-[var(--text-primary)]">任务名称</span>
                          <input
                            className="admin-input w-full px-3 py-2"
                            value={draft.name}
                            onChange={(event) => setDraftValue({ name: event.target.value })}
                          />
                        </label>
                        <label className="space-y-2">
                          <span className="text-sm font-medium text-[var(--text-primary)]">执行会话</span>
                          <select
                            className="admin-select w-full px-3 py-2"
                            value={draft.session_id}
                            onChange={(event) => setDraftValue({ session_id: Number.parseInt(event.target.value, 10) })}
                          >
                            {sessions.map((session) => (
                              <option key={session.id} value={session.id}>
                                {session.name}
                                {session.is_default ? '（默认）' : ''}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label className="space-y-2">
                          <span className="text-sm font-medium text-[var(--text-primary)]">状态</span>
                          <select
                            className="admin-select w-full px-3 py-2"
                            value={draft.enabled ? 'enabled' : 'disabled'}
                            onChange={(event) => setDraftValue({ enabled: event.target.value === 'enabled' })}
                          >
                            <option value="enabled">启用</option>
                            <option value="disabled">停用</option>
                          </select>
                        </label>
                      </div>

                      <div className="mt-6 rounded-2xl border border-[var(--panel-border)] p-4">
                        <div className="text-sm font-semibold uppercase tracking-[0.14em] text-[var(--text-muted)]">
                          调度策略
                        </div>
                        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
                          <label className="space-y-2">
                            <span className="text-sm font-medium text-[var(--text-primary)]">调度类型</span>
                            <select
                              className="admin-select w-full px-3 py-2"
                              value={draft.schedule_type}
                              onChange={(event) => {
                                const nextType = event.target.value;
                                const nextValue =
                                  nextType === 'once'
                                    ? buildOnceValue(new Date(Date.now() + 3600000).toISOString().slice(0, 16), draft.timezone)
                                    : nextType === 'interval'
                                      ? '60'
                                      : nextType === 'daily'
                                        ? '09:00'
                                        : nextType === 'weekly'
                                          ? '0|09:00'
                                          : '0 9 * * 1-5';
                                setDraftValue({ schedule_type: nextType, schedule_value: nextValue });
                              }}
                            >
                              <option value="interval">固定间隔</option>
                              <option value="daily">每天</option>
                              <option value="weekly">每周</option>
                              <option value="once">单次</option>
                              <option value="cron">Cron 表达式</option>
                            </select>
                          </label>
                          <label className="space-y-2">
                            <span className="text-sm font-medium text-[var(--text-primary)]">时区</span>
                            <input
                              className="admin-input w-full px-3 py-2"
                              list="automation-timezones"
                              value={draft.timezone}
                              onChange={(event) => setDraftValue({ timezone: event.target.value })}
                            />
                          </label>
                        </div>
                        <div className="mt-4">{renderScheduleEditor()}</div>
                      </div>

                      <label className="mt-6 block space-y-2">
                        <span className="text-sm font-medium text-[var(--text-primary)]">任务提示词</span>
                        <textarea
                          className="admin-input min-h-[220px] w-full px-3 py-3"
                          value={draft.prompt}
                          onChange={(event) => setDraftValue({ prompt: event.target.value })}
                          placeholder="描述自动化每次执行时希望 AI 完成的内容。"
                        />
                      </label>
                    </div>

                    <div className="space-y-4">
                      <div className="glass-card rounded-3xl p-5">
                        <div className="text-lg font-semibold text-[var(--text-primary)]">运行概览</div>
                        <div className="mt-4 grid gap-3 text-sm text-[var(--text-muted)]">
                          <div className="rounded-2xl border border-[var(--panel-border)] p-4">
                            <div className="text-xs uppercase tracking-[0.16em]">最近执行</div>
                            <div className="mt-2 text-base text-[var(--text-primary)]">{formatDateTime(draft.last_run_at)}</div>
                          </div>
                          <div className="rounded-2xl border border-[var(--panel-border)] p-4">
                            <div className="text-xs uppercase tracking-[0.16em]">下一次执行</div>
                            <div className="mt-2 text-base text-[var(--text-primary)]">{formatDateTime(draft.next_run_at)}</div>
                          </div>
                          <div className="rounded-2xl border border-[var(--panel-border)] p-4">
                            <div className="text-xs uppercase tracking-[0.16em]">工作会话</div>
                            <div className="mt-2 text-base text-[var(--text-primary)]">
                              {sessions.find((item) => item.id === draft.session_id)?.name || `#${draft.session_id}`}
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="glass-card rounded-3xl p-5">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <div className="text-lg font-semibold text-[var(--text-primary)]">最近运行记录</div>
                            <div className="text-sm text-[var(--text-muted)]">查看任务是否真正执行、失败在哪里。</div>
                          </div>
                          <button
                            type="button"
                            className="btn"
                            onClick={() => selectedAutomationId && void getAutomationRuns(selectedAutomationId).then(setRuns)}
                            disabled={!selectedAutomationId || busy}
                          >
                            <RefreshCw size={14} />
                            刷新记录
                          </button>
                        </div>

                        <div className="mt-4 space-y-3">
                          {runs.length === 0 ? (
                            <div className="rounded-2xl border border-dashed border-[var(--panel-border)] p-4 text-sm text-[var(--text-muted)]">
                              这条自动化还没有运行记录。
                            </div>
                          ) : null}
                          {runs.map((run) => (
                            <div key={run.id} className="rounded-2xl border border-[var(--panel-border)] p-4">
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <div className="font-medium text-[var(--text-primary)]">{formatRunStatus(run.status)}</div>
                                <div className="text-xs text-[var(--text-muted)]">
                                  {run.trigger_mode === 'manual' ? '手动触发' : '定时触发'}
                                </div>
                              </div>
                              <div className="mt-2 space-y-1 text-xs text-[var(--text-muted)]">
                                <div>触发时间：{formatDateTime(run.triggered_at)}</div>
                                <div>完成时间：{formatDateTime(run.completed_at)}</div>
                                {run.run_id ? <div>运行编号：{run.run_id}</div> : null}
                                {run.error ? <div className="text-red-400">错误：{run.error}</div> : null}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="glass-card rounded-3xl p-10 text-center text-sm text-[var(--text-muted)]">
                  先选择一个自动化任务，或者新建一个任务开始配置。
                </div>
              )}
            </section>
          </div>
        </div>
      </div>

      <datalist id="automation-timezones">
        {TIMEZONE_SUGGESTIONS.map((timezone) => (
          <option key={timezone} value={timezone} />
        ))}
      </datalist>
    </MainLayout>
  );
};

export default AutomationsPage;
