import { useEffect, useState } from 'react';

import MainLayout from '../layout/MainLayout';
import {
  createAutomation,
  deleteAutomation,
  getAutomationRuns,
  getAutomations,
  updateAutomation,
} from '../../services/api';
import type { Automation, AutomationPayload, AutomationRun } from '../../types';

const EMPTY_AUTOMATION: Partial<Automation> = {
  name: '',
  prompt: '',
  schedule_type: 'interval',
  schedule_value: '60',
  enabled: true,
};

const formatScheduleType = (scheduleType: string) => {
  if (scheduleType === 'interval') return '固定间隔';
  if (scheduleType === 'daily') return '每天固定时间';
  if (scheduleType === 'weekly') return '每周固定时间';
  return scheduleType;
};

const formatRunStatus = (status: string) => {
  if (status === 'success') return '成功';
  if (status === 'failed') return '失败';
  if (status === 'running') return '执行中';
  return status;
};

const AutomationsPage: React.FC = () => {
  const [automations, setAutomations] = useState<Automation[]>([]);
  const [selectedAutomation, setSelectedAutomation] = useState<Automation | null>(null);
  const [runs, setRuns] = useState<AutomationRun[]>([]);

  const loadAutomations = async () => {
    const data = await getAutomations();
    setAutomations(data);
    setSelectedAutomation((prev) => data.find((item) => item.id === prev?.id) || prev || data[0] || null);
  };

  useEffect(() => {
    void loadAutomations().catch((error) => console.error('Failed to load automations', error));
  }, []);

  useEffect(() => {
    if (!selectedAutomation) {
      setRuns([]);
      return;
    }
    void getAutomationRuns(selectedAutomation.id)
      .then(setRuns)
      .catch((error) => console.error('Failed to load automation runs', error));
  }, [selectedAutomation]);

  const saveAutomation = async () => {
    if (!selectedAutomation) {
      return;
    }
    const updated = await updateAutomation(selectedAutomation.id, {
      name: selectedAutomation.name,
      prompt: selectedAutomation.prompt,
      schedule_type: selectedAutomation.schedule_type,
      schedule_value: selectedAutomation.schedule_value,
      enabled: selectedAutomation.enabled,
    });
    setSelectedAutomation(updated);
    await loadAutomations();
  };

  return (
    <MainLayout headerTitle="自动化任务">
      <div className="admin-page">
        <div className="admin-frame h-full space-y-4 overflow-y-auto p-4">
          <button
            type="button"
            className="btn-secondary"
            onClick={async () => {
              const created = await createAutomation({
                ...(EMPTY_AUTOMATION as AutomationPayload),
                name: `自动化任务 ${Date.now()}`,
                prompt: '总结最近进展，并给出当前最值得执行的下一步建议。',
              });
              await loadAutomations();
              setSelectedAutomation(created);
            }}
          >
            新建自动化
          </button>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-[320px,1fr]">
            <div className="space-y-2">
              {automations.map((automation) => (
                <button
                  key={automation.id}
                  type="button"
                  className="w-full rounded-xl border p-3 text-left"
                  style={{
                    borderColor:
                      selectedAutomation?.id === automation.id ? 'var(--accent)' : 'var(--panel-border)',
                  }}
                  onClick={() => setSelectedAutomation(automation)}
                >
                  <div className="font-semibold">{automation.name}</div>
                  <div className="mt-1 text-xs opacity-70">
                    {formatScheduleType(automation.schedule_type)}：{automation.schedule_value}
                  </div>
                  <div className="mt-1 text-[11px] opacity-60">
                    {automation.enabled ? '已启用' : '已停用'} · 下次执行 {automation.next_run_at || '未排程'}
                  </div>
                </button>
              ))}
            </div>

            <div className="glass-card rounded-2xl p-4">
              {selectedAutomation ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div>
                      <label className="mb-1 block text-sm">名称</label>
                      <input
                        className="admin-input w-full px-3 py-2"
                        value={selectedAutomation.name}
                        onChange={(event) =>
                          setSelectedAutomation((prev) => (prev ? { ...prev, name: event.target.value } : prev))
                        }
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm">调度方式</label>
                      <select
                        className="admin-select w-full px-3 py-2"
                        value={selectedAutomation.schedule_type}
                        onChange={(event) =>
                          setSelectedAutomation((prev) =>
                            prev
                              ? {
                                  ...prev,
                                  schedule_type: event.target.value,
                                  schedule_value:
                                    event.target.value === 'interval'
                                      ? '60'
                                      : event.target.value === 'daily'
                                        ? '09:00'
                                        : '0|09:00',
                                }
                              : prev,
                          )
                        }
                      >
                        <option value="interval">固定间隔（分钟）</option>
                        <option value="daily">每天固定时间</option>
                        <option value="weekly">每周固定时间</option>
                      </select>
                    </div>
                    <div>
                      <label className="mb-1 block text-sm">调度参数</label>
                      <input
                        className="admin-input w-full px-3 py-2"
                        value={selectedAutomation.schedule_value}
                        onChange={(event) =>
                          setSelectedAutomation((prev) => (prev ? { ...prev, schedule_value: event.target.value } : prev))
                        }
                        placeholder={
                          selectedAutomation.schedule_type === 'interval'
                            ? '60'
                            : selectedAutomation.schedule_type === 'daily'
                              ? '09:00'
                              : '0|09:00'
                        }
                      />
                    </div>
                  </div>

                  <div>
                    <label className="mb-1 block text-sm">任务提示词</label>
                    <textarea
                      className="admin-input min-h-[160px] w-full px-3 py-2"
                      value={selectedAutomation.prompt}
                      onChange={(event) =>
                        setSelectedAutomation((prev) => (prev ? { ...prev, prompt: event.target.value } : prev))
                      }
                    />
                  </div>

                  <div className="space-y-1 text-sm opacity-80">
                    <div>最近执行：{selectedAutomation.last_run_at || '尚未执行'}</div>
                    <div>下次执行：{selectedAutomation.next_run_at || '尚未排程'}</div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <button type="button" className="btn-secondary" onClick={() => void saveAutomation()}>
                      保存
                    </button>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={async () => {
                        if (!selectedAutomation) {
                          return;
                        }
                        const updated = await updateAutomation(selectedAutomation.id, {
                          enabled: !selectedAutomation.enabled,
                        });
                        setSelectedAutomation(updated);
                        await loadAutomations();
                      }}
                    >
                      {selectedAutomation.enabled ? '停用' : '启用'}
                    </button>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={async () => {
                        if (!selectedAutomation) {
                          return;
                        }
                        await deleteAutomation(selectedAutomation.id);
                        setSelectedAutomation(null);
                        await loadAutomations();
                      }}
                    >
                      删除
                    </button>
                  </div>

                  <div>
                    <div className="mb-2 font-semibold">最近执行记录</div>
                    <div className="space-y-2">
                      {runs.map((run) => (
                        <div
                          key={run.id}
                          className="rounded-xl border p-3"
                          style={{ borderColor: 'var(--panel-border)' }}
                        >
                          <div className="text-sm font-medium">{formatRunStatus(run.status)}</div>
                          <div className="text-xs opacity-70">
                            触发于 {run.triggered_at}
                            {run.completed_at ? ` · 完成于 ${run.completed_at}` : ''}
                          </div>
                          {run.run_id ? <div className="mt-1 text-xs opacity-70">运行编号 {run.run_id}</div> : null}
                          {run.error ? <div className="mt-1 text-xs text-red-500">{run.error}</div> : null}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-sm opacity-70">选择一个自动化任务后，可在这里查看配置和最近执行记录。</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default AutomationsPage;
