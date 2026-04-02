import { useEffect, useMemo, useState } from 'react';
import { Clock3, Copy, Play, Plus, RefreshCw, Save, Trash2 } from 'lucide-react';

import MainLayout from '../layout/MainLayout';
import StatusBadge from '../admin/StatusBadge';
import Switch from '../admin/Switch';
import {
  clearAutomationRuns,
  createAutomation,
  deleteAutomation,
  getAutomationRuns,
  getAutomations,
  getAutomationStats,
  getConversations,
  runAutomationNow,
  updateAutomation,
} from '../../services/api';
import type {
  Automation,
  AutomationPayload,
  AutomationRun,
  AutomationStats,
  Conversation,
} from '../../types';

type AutomationDraft = AutomationPayload &
  Partial<
    Pick<
      Automation,
      'id' | 'session_id' | 'last_run_at' | 'next_run_at' | 'created_at' | 'updated_at'
    >
  >;

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

const normalizeConversationTitle = (title: string) => {
  if (!title || title === 'New Chat') return '新会话';
  return title;
};

const getDefaultAutomationPayload = (conversationId?: number): AutomationPayload => ({
  name: '新自动化任务',
  conversation_id: conversationId,
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
  if (timezone === 'UTC') return `${localValue}:00Z`;
  return localValue;
};

const formatSchedule = (automation: Pick<AutomationDraft, 'schedule_type' | 'schedule_value'>) => {
  if (automation.schedule_type === 'once') return `单次 · ${formatDateTime(automation.schedule_value)}`;
  if (automation.schedule_type === 'interval') {
    const { amount, unit } = getIntervalParts(automation.schedule_value);
    const unitLabel = unit === 'days' ? '天' : unit === 'hours' ? '小时' : '分钟';
    return `每 ${amount} ${unitLabel}`;
  }
  if (automation.schedule_type === 'daily') return `每天 ${automation.schedule_value}`;
  if (automation.schedule_type === 'weekly') {
    const { weekday, time } = getWeeklyParts(automation.schedule_value);
    const weekdayLabel = WEEKDAY_OPTIONS.find((item) => item.value === weekday)?.label ?? weekday;
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

const getRunTone = (status: string): 'success' | 'danger' | 'warning' | 'neutral' => {
  if (status === 'success') return 'success';
  if (status === 'failed') return 'danger';
  if (status === 'running') return 'warning';
  return 'neutral';
};

const summaryCards = (stats: AutomationStats) => [
  { label: '总任务数', value: stats.total, hint: `${stats.enabled} 启用 / ${stats.disabled} 停用` },
  { label: '执行中', value: stats.running, hint: stats.due_now > 0 ? `${stats.due_now} 个任务到点` : '暂无待执行任务' },
  { label: '最近失败', value: stats.failed_recently, hint: stats.last_run_at ? `最近执行 ${formatRelative(stats.last_run_at)}` : '暂无运行记录' },
  { label: '下一次调度', value: stats.next_run_at ? formatRelative(stats.next_run_at) : '暂无', hint: stats.next_run_at ? formatDateTime(stats.next_run_at) : '没有未来任务' },
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
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedAutomationId, setSelectedAutomationId] = useState<number | null>(null);
  const [draft, setDraft] = useState<AutomationDraft | null>(null);
  const [runs, setRuns] = useState<AutomationRun[]>([]);
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'enabled' | 'disabled'>('all');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const selectedAutomation = automations.find((item) => item.id === selectedAutomationId) || null;
  const activeConversation = draft ? conversations.find((item) => item.id === draft.conversation_id) || null : null;

  const visibleAutomations = useMemo(
    () =>
      automations.filter((item) => {
        const conversationTitle = conversations.find((conversation) => conversation.id === item.conversation_id)?.title || '';
        const normalizedQuery = query.trim().toLowerCase();
        const matchesQuery =
          normalizedQuery.length === 0 ||
          item.name.toLowerCase().includes(normalizedQuery) ||
          item.prompt.toLowerCase().includes(normalizedQuery) ||
          conversationTitle.toLowerCase().includes(normalizedQuery);
        const matchesStatus =
          statusFilter === 'all' || (statusFilter === 'enabled' ? item.enabled : !item.enabled);
        return matchesQuery && matchesStatus;
      }),
    [automations, conversations, query, statusFilter],
  );

  const refreshPage = async (preferredAutomationId?: number | null) => {
    const [automationData, statsData, conversationData] = await Promise.all([
      getAutomations(),
      getAutomationStats(),
      getConversations(),
    ]);
    setAutomations(automationData);
    setStats(statsData);
    setConversations(conversationData);
    setSelectedAutomationId((previousId) => {
      const nextId = preferredAutomationId ?? previousId;
      if (nextId && automationData.some((item) => item.id === nextId)) return nextId;
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

  const setDraftValue = (patch: Partial<AutomationDraft>) => {
    setDraft((current) => (current ? { ...current, ...patch } : current));
  };

  const handleCreate = async () => {
    try {
      setBusy(true);
      setError(null);
      const baseConversationId = draft?.conversation_id ?? conversations[0]?.id;
      if (!baseConversationId) throw new Error('请先创建至少一个会话，再创建自动化任务。');
      const created = await createAutomation(getDefaultAutomationPayload(baseConversationId));
      await refreshPage(created.id);
    } catch (actionError) {
      console.error('Failed to create automation', actionError);
      setError(actionError instanceof Error ? actionError.message : '创建自动化失败');
    } finally {
      setBusy(false);
    }
  };

  const handleClone = async () => {
    if (!draft?.conversation_id) return;
    try {
      setBusy(true);
      setError(null);
      const cloned = await createAutomation({
        name: `${draft.name} 副本`,
        conversation_id: draft.conversation_id,
        prompt: draft.prompt,
        schedule_type: draft.schedule_type,
        schedule_value: draft.schedule_value,
        timezone: draft.timezone,
        enabled: draft.enabled,
      });
      await refreshPage(cloned.id);
    } catch (actionError) {
      console.error('Failed to clone automation', actionError);
      setError(actionError instanceof Error ? actionError.message : '复制自动化失败');
    } finally {
      setBusy(false);
    }
  };

  const handleSave = async () => {
    if (!draft?.id || !draft.conversation_id) return;
    try {
      setBusy(true);
      setError(null);
      await updateAutomation(draft.id, {
        name: draft.name.trim(),
        conversation_id: draft.conversation_id,
        prompt: draft.prompt.trim(),
        schedule_type: draft.schedule_type,
        schedule_value: draft.schedule_value,
        timezone: draft.timezone,
        enabled: draft.enabled,
      });
      await refreshPage(draft.id);
    } catch (actionError) {
      console.error('Failed to save automation', actionError);
      setError(actionError instanceof Error ? actionError.message : '保存自动化失败');
    } finally {
      setBusy(false);
    }
  };

  const handleRunNow = async () => {
    if (!draft?.id) return;
    try {
      setBusy(true);
      setError(null);
      await runAutomationNow(draft.id);
      await refreshPage(draft.id);
      setRuns(await getAutomationRuns(draft.id));
    } catch (actionError) {
      console.error('Failed to run automation', actionError);
      setError(actionError instanceof Error ? actionError.message : '立即执行失败');
    } finally {
      setBusy(false);
    }
  };

  const handleToggleEnabled = async () => {
    if (!draft?.id) return;
    const previousEnabled = draft.enabled;
    const nextEnabled = !previousEnabled;
    try {
      setBusy(true);
      setError(null);
      setDraftValue({ enabled: nextEnabled });
      await updateAutomation(draft.id, { enabled: nextEnabled });
      await refreshPage(draft.id);
    } catch (actionError) {
      console.error('Failed to toggle automation', actionError);
      setError(actionError instanceof Error ? actionError.message : '切换启用状态失败');
      setDraftValue({ enabled: previousEnabled });
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    if (!draft?.id) return;
    const confirmed = window.confirm(`确认删除自动化任务“${draft.name}”吗？`);
    if (!confirmed) return;
    try {
      setBusy(true);
      setError(null);
      const currentId = draft.id;
      await deleteAutomation(currentId);
      setRuns([]);
      await refreshPage(currentId);
    } catch (actionError) {
      console.error('Failed to delete automation', actionError);
      setError(actionError instanceof Error ? actionError.message : '删除自动化失败');
    } finally {
      setBusy(false);
    }
  };

  const handleClearRuns = async () => {
    if (!draft?.id) return;
    const confirmed = window.confirm('确认清空这条自动化任务的历史运行记录吗？');
    if (!confirmed) return;
    try {
      setBusy(true);
      setError(null);
      await clearAutomationRuns(draft.id);
      setRuns([]);
      await refreshPage(draft.id);
    } catch (actionError) {
      console.error('Failed to clear automation runs', actionError);
      setError(actionError instanceof Error ? actionError.message : '清空运行记录失败');
    } finally {
      setBusy(false);
    }
  };

  const renderScheduleEditor = () => {
    if (!draft) return null;

    if (draft.schedule_type === 'interval') {
      const { amount, unit } = getIntervalParts(draft.schedule_value);
      return (
        <>
          <input
            type="number"
            min="1"
            value={amount}
            onChange={(event) => setDraftValue({ schedule_value: buildIntervalValue(event.target.value, unit) })}
            className="admin-input h-10 w-full px-3"
          />
          <select
            value={unit}
            onChange={(event) => setDraftValue({ schedule_value: buildIntervalValue(amount, event.target.value) })}
            className="admin-select h-10 w-full px-3"
          >
            <option value="minutes">分钟</option>
            <option value="hours">小时</option>
            <option value="days">天</option>
          </select>
        </>
      );
    }

    if (draft.schedule_type === 'daily') {
      return (
        <input
          type="time"
          value={draft.schedule_value || '09:00'}
          onChange={(event) => setDraftValue({ schedule_value: event.target.value })}
          className="admin-input h-10 w-full px-3"
        />
      );
    }

    if (draft.schedule_type === 'weekly') {
      const { weekday, time } = getWeeklyParts(draft.schedule_value);
      return (
        <>
          <select
            value={weekday}
            onChange={(event) => setDraftValue({ schedule_value: `${event.target.value}|${time}` })}
            className="admin-select h-10 w-full px-3"
          >
            {WEEKDAY_OPTIONS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
          <input
            type="time"
            value={time}
            onChange={(event) => setDraftValue({ schedule_value: `${weekday}|${event.target.value}` })}
            className="admin-input h-10 w-full px-3"
          />
        </>
      );
    }

    if (draft.schedule_type === 'once') {
      return (
        <input
          type="datetime-local"
          value={getOnceInputValue(draft.schedule_value)}
          onChange={(event) => setDraftValue({ schedule_value: buildOnceValue(event.target.value, draft.timezone) })}
          className="admin-input h-10 w-full px-3"
        />
      );
    }

    return (
      <input
        type="text"
        value={draft.schedule_value}
        onChange={(event) => setDraftValue({ schedule_value: event.target.value })}
        placeholder="例如：0 9 * * 1-5"
        className="admin-input h-10 w-full px-3"
      />
    );
  };

  const canPersist = Boolean(
    draft &&
      draft.id &&
      draft.name.trim() &&
      draft.prompt.trim() &&
      draft.conversation_id &&
      draft.schedule_value.trim(),
  );

  if (loading) {
    return (
      <MainLayout headerTitle="自动化" headerSubtitle="定时任务、真实运行记录与目标会话绑定">
        <div className="admin-page">
          <div className="admin-frame">
            <div className="admin-card p-6 text-sm" style={{ color: 'var(--text-secondary)' }}>
              正在加载自动化配置...
            </div>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout
      headerTitle="自动化"
      headerSubtitle="基于真实会话的定时任务系统，运行记录直接来自后端执行数据。"
      headerActions={
        <div className="admin-toolbar">
          <button
            type="button"
            onClick={() => void refreshPage(selectedAutomationId)}
            className="btn-secondary inline-flex items-center gap-2"
            disabled={busy}
          >
            <RefreshCw size={16} />
            刷新
          </button>
          <button
            type="button"
            onClick={() => void handleCreate()}
            className="btn-primary inline-flex items-center gap-2"
            disabled={busy || conversations.length === 0}
          >
            <Plus size={16} />
            新建任务
          </button>
        </div>
      }
    >
      <div className="admin-page">
        <div className="admin-frame max-w-[1400px]">
          <section className="admin-summary">
            {summaryCards(stats).map((card) => (
              <div key={card.label} className="admin-summary-card">
                <div className="admin-summary-label">{card.label}</div>
                <div className="admin-summary-value">{card.value}</div>
                <div className="mt-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                  {card.hint}
                </div>
              </div>
            ))}
          </section>

          {error ? (
            <div className="warning-banner px-4 py-3 text-sm" style={{ color: 'var(--text-secondary)' }}>
              {error}
            </div>
          ) : null}

          <section className="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)] 2xl:grid-cols-[300px_minmax(0,1fr)]">
            <aside className="admin-card flex min-h-[720px] flex-col overflow-hidden">
              <div className="border-b px-4 py-4" style={{ borderColor: 'var(--panel-border)' }}>
                <div className="admin-toolbar">
                  <input
                    type="search"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="搜索任务、提示词或目标会话"
                    className="admin-input h-10 flex-1 px-3"
                  />
                  <select
                    value={statusFilter}
                    onChange={(event) => setStatusFilter(event.target.value as 'all' | 'enabled' | 'disabled')}
                    className="admin-select h-10 w-full px-3 sm:w-[110px]"
                  >
                    <option value="all">全部</option>
                    <option value="enabled">启用</option>
                    <option value="disabled">停用</option>
                  </select>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-3">
                <div className="grid gap-2">
                  {visibleAutomations.map((automation) => {
                    const conversation = conversations.find((item) => item.id === automation.conversation_id) || null;
                    const isActive = automation.id === selectedAutomationId;
                    return (
                      <button
                        type="button"
                        key={automation.id}
                        onClick={() => setSelectedAutomationId(automation.id)}
                        className={`rounded-2xl border p-3 text-left transition ${isActive ? 'shadow-sm' : ''}`}
                        style={{
                          borderColor: isActive
                            ? 'color-mix(in srgb, var(--accent) 35%, var(--panel-border))'
                            : 'var(--panel-border)',
                          background: isActive
                            ? 'color-mix(in srgb, var(--accent) 10%, var(--surface-elevated))'
                            : 'var(--surface-elevated)',
                        }}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <div className="truncate text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                              {automation.name}
                            </div>
                            <div className="mt-1 truncate text-xs" style={{ color: 'var(--text-muted)' }}>
                              {normalizeConversationTitle(conversation?.title || '')}
                            </div>
                          </div>
                          <StatusBadge tone={automation.enabled ? 'success' : 'neutral'}>
                            {automation.enabled ? '启用' : '停用'}
                          </StatusBadge>
                        </div>
                        <div className="mt-3 grid gap-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
                          <div>{formatSchedule(automation)}</div>
                          <div>下次运行：{formatRelative(automation.next_run_at)}</div>
                        </div>
                      </button>
                    );
                  })}

                  {visibleAutomations.length === 0 ? (
                    <div
                      className="rounded-2xl border border-dashed p-4 text-sm"
                      style={{ borderColor: 'var(--panel-border)', color: 'var(--text-muted)' }}
                    >
                      没有匹配的自动化任务。
                    </div>
                  ) : null}
                </div>
              </div>
            </aside>

            <section className="grid gap-4 lg:grid-cols-[minmax(0,760px)_300px] 2xl:grid-cols-[minmax(0,820px)_320px] 2xl:justify-center">
              <div className="admin-card flex min-h-[720px] flex-col overflow-hidden">
                <div
                  className="flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3"
                  style={{ borderColor: 'var(--panel-border)' }}
                >
                  <div>
                    <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {draft?.name || '选择一个自动化任务'}
                    </div>
                    <div className="mt-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                      这里的“目标会话”就是会话页中的真实会话，不再是旧系统的残留工作会话定义。
                    </div>
                  </div>

                  <div className="admin-toolbar">
                    <button
                      type="button"
                      onClick={() => void handleClone()}
                      className="btn-secondary inline-flex items-center gap-2"
                      disabled={busy || !draft?.id}
                    >
                      <Copy size={16} />
                      复制
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleRunNow()}
                      className="btn-secondary inline-flex items-center gap-2"
                      disabled={busy || !draft?.id}
                    >
                      <Play size={16} />
                      立即执行
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleSave()}
                      className="btn-primary inline-flex items-center gap-2"
                      disabled={busy || !canPersist}
                    >
                      <Save size={16} />
                      保存
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleDelete()}
                      className="btn-secondary inline-flex items-center gap-2"
                      disabled={busy || !draft?.id}
                    >
                      <Trash2 size={16} />
                      删除
                    </button>
                  </div>
                </div>

                {draft ? (
                  <div className="flex-1 overflow-y-auto p-4">
                    <div className="mx-auto grid max-w-[760px] gap-4">
                      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_180px]">
                        <label className="grid gap-2">
                          <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
                            任务名称
                          </span>
                          <input
                            type="text"
                            value={draft.name}
                            onChange={(event) => setDraftValue({ name: event.target.value })}
                            className="admin-input h-11 px-3"
                            placeholder="例如：每日工作总结"
                          />
                        </label>

                        <div className="grid gap-2">
                          <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
                            启用状态
                          </span>
                          <div
                            className="flex h-11 items-center justify-between rounded-xl border px-3"
                            style={{ borderColor: 'var(--panel-border)', background: 'var(--input-bg)' }}
                          >
                            <span className="text-sm" style={{ color: 'var(--text-primary)' }}>
                              {draft.enabled ? '已启用' : '已停用'}
                            </span>
                            <Switch
                              checked={draft.enabled}
                              onChange={() => void handleToggleEnabled()}
                              ariaLabel="切换自动化启用状态"
                            />
                          </div>
                        </div>
                      </div>

                      <label className="grid gap-2">
                        <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
                          目标会话
                        </span>
                        <select
                          value={draft.conversation_id ?? ''}
                          onChange={(event) => setDraftValue({ conversation_id: Number(event.target.value) })}
                          className="admin-select h-11 px-3"
                        >
                          <option value="" disabled>
                            请选择目标会话
                          </option>
                          {conversations.map((conversation) => (
                            <option key={conversation.id} value={conversation.id}>
                              {normalizeConversationTitle(conversation.title)}
                            </option>
                          ))}
                        </select>
                      </label>

                      <div className="grid gap-3 rounded-2xl border p-4" style={{ borderColor: 'var(--panel-border)' }}>
                        <div className="flex items-center gap-2 text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                          <Clock3 size={16} />
                          调度设置
                        </div>
                        <div className="grid gap-3 lg:grid-cols-[160px_minmax(0,1fr)_220px]">
                          <select
                            value={draft.schedule_type}
                            onChange={(event) => {
                              const nextType = event.target.value;
                              const defaults: Record<string, string> = {
                                interval: '60',
                                daily: '09:00',
                                weekly: '0|09:00',
                                once: '',
                                cron: '0 9 * * 1-5',
                              };
                              setDraftValue({
                                schedule_type: nextType,
                                schedule_value: defaults[nextType] ?? draft.schedule_value,
                              });
                            }}
                            className="admin-select h-10 px-3"
                          >
                            <option value="interval">间隔</option>
                            <option value="daily">每日</option>
                            <option value="weekly">每周</option>
                            <option value="once">单次</option>
                            <option value="cron">Cron</option>
                          </select>

                          <div
                            className={`grid gap-3 ${
                              draft.schedule_type === 'interval' || draft.schedule_type === 'weekly'
                                ? 'md:grid-cols-2'
                                : ''
                            }`}
                          >
                            {renderScheduleEditor()}
                          </div>

                          <input
                            type="text"
                            list="automation-timezones"
                            value={draft.timezone}
                            onChange={(event) => setDraftValue({ timezone: event.target.value })}
                            className="admin-input h-10 px-3"
                            placeholder="时区"
                          />
                        </div>
                        <datalist id="automation-timezones">
                          {TIMEZONE_SUGGESTIONS.map((timezone) => (
                            <option key={timezone} value={timezone} />
                          ))}
                        </datalist>
                      </div>

                      <label className="grid gap-2">
                        <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
                          执行提示词
                        </span>
                        <textarea
                          value={draft.prompt}
                          onChange={(event) => setDraftValue({ prompt: event.target.value })}
                          rows={12}
                          className="admin-input min-h-[260px] resize-y px-3 py-3"
                          placeholder="描述自动化执行时要让 AI 完成的任务。"
                        />
                      </label>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-1 items-center justify-center p-8 text-sm" style={{ color: 'var(--text-muted)' }}>
                    先从左侧选择一个自动化任务，或新建一个任务开始配置。
                  </div>
                )}
              </div>

              <aside className="grid gap-4">
                <div className="admin-card p-4">
                  <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                    运行概览
                  </div>
                  <div className="mt-3 grid gap-3 text-sm">
                    <div className="rounded-xl border p-3" style={{ borderColor: 'var(--panel-border)' }}>
                      <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                        目标会话
                      </div>
                      <div className="mt-1 font-medium" style={{ color: 'var(--text-primary)' }}>
                        {activeConversation ? normalizeConversationTitle(activeConversation.title) : '未选择'}
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="rounded-xl border p-3" style={{ borderColor: 'var(--panel-border)' }}>
                        <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                          最近运行
                        </div>
                        <div className="mt-1 text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                          {formatRelative(draft?.last_run_at)}
                        </div>
                        <div className="mt-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                          {formatDateTime(draft?.last_run_at)}
                        </div>
                      </div>
                      <div className="rounded-xl border p-3" style={{ borderColor: 'var(--panel-border)' }}>
                        <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                          下次运行
                        </div>
                        <div className="mt-1 text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                          {formatRelative(draft?.next_run_at)}
                        </div>
                        <div className="mt-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                          {formatDateTime(draft?.next_run_at)}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="admin-card flex min-h-[360px] flex-col p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                        最新运行记录
                      </div>
                      <div className="mt-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                        这里展示的是后端 automation_runs 的真实执行记录，不是前端模拟数据。
                      </div>
                    </div>
                    {draft?.id ? <StatusBadge tone="info">{runs.length} 条</StatusBadge> : null}
                  </div>

                  <div className="mt-2 flex justify-end">
                    <button
                      type="button"
                      onClick={() => void handleClearRuns()}
                      className="btn-secondary px-3 py-2 text-xs"
                      disabled={busy || !draft?.id || runs.length === 0}
                    >
                      清空历史记录
                    </button>
                  </div>

                  <div className="mt-4 flex-1 space-y-3 overflow-y-auto">
                    {runs.map((run) => (
                      <div
                        key={run.id}
                        className="rounded-2xl border p-3"
                        style={{ borderColor: 'var(--panel-border)', background: 'var(--surface-elevated)' }}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                              {run.trigger_mode === 'manual' ? '手动触发' : '定时触发'}
                            </div>
                            <div className="mt-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                              {formatDateTime(run.triggered_at)}
                            </div>
                          </div>
                          <StatusBadge tone={getRunTone(run.status)}>{formatRunStatus(run.status)}</StatusBadge>
                        </div>
                        <div className="mt-3 grid gap-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
                          <div>运行 ID：{run.run_id || '未返回'}</div>
                          <div>完成时间：{formatDateTime(run.completed_at)}</div>
                          {run.error ? <div style={{ color: '#dc2626' }}>错误：{run.error}</div> : null}
                        </div>
                      </div>
                    ))}

                    {draft?.id && runs.length === 0 ? (
                      <div
                        className="rounded-2xl border border-dashed p-4 text-sm"
                        style={{ borderColor: 'var(--panel-border)', color: 'var(--text-muted)' }}
                      >
                        这个任务还没有运行记录。
                      </div>
                    ) : null}

                    {!draft?.id ? (
                      <div
                        className="rounded-2xl border border-dashed p-4 text-sm"
                        style={{ borderColor: 'var(--panel-border)', color: 'var(--text-muted)' }}
                      >
                        选择一个任务后可查看它的最近执行记录。
                      </div>
                    ) : null}
                  </div>
                </div>
              </aside>
            </section>
          </section>
        </div>
      </div>
    </MainLayout>
  );
};

export default AutomationsPage;
