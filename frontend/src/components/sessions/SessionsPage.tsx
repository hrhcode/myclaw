import { useEffect, useState } from 'react';

import MainLayout from '../layout/MainLayout';
import { useApp } from '../../contexts/AppContext';
import {
  dispatchSessionMessage,
  getSessionHistorySummary,
  getSessionSkills,
  getSessionStatus,
  getSkills,
  updateSessionSkills,
} from '../../services/api';
import type { SessionSkill, SessionStatus, Skill } from '../../types';

const formatStopReason = (reason?: string | null) => {
  if (!reason) return '运行中';
  if (reason === 'final_answer') return '已完成';
  if (reason === 'command') return '命令执行完成';
  if (reason === 'max_iterations') return '达到最大迭代次数';
  return reason;
};

const SessionsPage: React.FC = () => {
  const {
    sessions,
    currentSessionId,
    selectSession,
    createNewSession,
    updateSessionById,
    removeSession,
    loadSessions,
  } = useApp();
  const [status, setStatus] = useState<SessionStatus | null>(null);
  const [newName, setNewName] = useState('');
  const [availableSkills, setAvailableSkills] = useState<Skill[]>([]);
  const [sessionSkills, setSessionSkills] = useState<SessionSkill[]>([]);
  const [historySummary, setHistorySummary] = useState<string>('');
  const [dispatchTargetId, setDispatchTargetId] = useState<number | null>(null);
  const [dispatchMessage, setDispatchMessage] = useState('');
  const [isDispatching, setIsDispatching] = useState(false);

  useEffect(() => {
    loadSessions();
    getSkills()
      .then(setAvailableSkills)
      .catch((error) => console.error('Failed to load skills', error));
  }, [loadSessions]);

  useEffect(() => {
    if (!currentSessionId) {
      setStatus(null);
      setSessionSkills([]);
      setHistorySummary('');
      setDispatchTargetId(null);
      return;
    }

    getSessionStatus(currentSessionId)
      .then((nextStatus) => {
        setStatus(nextStatus);
        setDispatchTargetId((prev) => prev ?? nextStatus.id);
      })
      .catch((error) => console.error('Failed to load session status', error));
    getSessionSkills(currentSessionId)
      .then(setSessionSkills)
      .catch((error) => console.error('Failed to load session skills', error));
    getSessionHistorySummary(currentSessionId)
      .then((response) => setHistorySummary(response.summary))
      .catch((error) => console.error('Failed to load session history summary', error));
  }, [currentSessionId]);

  const refreshStatus = async (sessionId: number) => {
    setStatus(await getSessionStatus(sessionId));
    const summary = await getSessionHistorySummary(sessionId);
    setHistorySummary(summary.summary);
  };

  return (
    <MainLayout headerTitle="工作会话">
      <div className="admin-page">
        <div className="admin-frame p-4 h-full overflow-y-auto space-y-4">
          <div className="flex gap-2">
            <input
              className="admin-input flex-1 px-3 py-2"
              value={newName}
              onChange={(event) => setNewName(event.target.value)}
              placeholder="输入新的工作会话名称"
            />
            <button
              type="button"
              className="btn-secondary"
              onClick={async () => {
                const created = await createNewSession(newName || undefined);
                if (created) {
                  setNewName('');
                }
              }}
            >
              新建
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[300px,1fr] gap-4">
            <div className="space-y-2">
              {sessions.map((session) => (
                <button
                  key={session.id}
                  type="button"
                  className="w-full rounded-xl border p-3 text-left"
                  style={{
                    borderColor: currentSessionId === session.id ? 'var(--accent)' : 'var(--panel-border)',
                  }}
                  onClick={() => selectSession(session.id)}
                >
                  <div className="font-semibold">{session.name}</div>
                  <div className="text-xs opacity-70">{session.workspace_path || '未配置工作区目录'}</div>
                  <div className="text-[11px] opacity-60 mt-1">
                    {session.model || '默认模型'} · {session.tool_profile}
                    {session.is_default ? ' · 默认会话' : ''}
                  </div>
                </button>
              ))}
            </div>

            <div className="glass-card rounded-2xl p-4">
              {status ? (
                <div className="space-y-5">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm mb-1">名称</label>
                      <input
                        className="admin-input w-full px-3 py-2"
                        value={status.name}
                        onChange={(event) => setStatus((prev) => (prev ? { ...prev, name: event.target.value } : prev))}
                      />
                    </div>
                    <div>
                      <label className="block text-sm mb-1">模式</label>
                      <input className="admin-input w-full px-3 py-2" value={status.mode} readOnly />
                    </div>
                    <div>
                      <label className="block text-sm mb-1">工作区目录</label>
                      <input
                        className="admin-input w-full px-3 py-2"
                        value={status.workspace_path || ''}
                        onChange={(event) =>
                          setStatus((prev) => (prev ? { ...prev, workspace_path: event.target.value } : prev))
                        }
                      />
                    </div>
                    <div>
                      <label className="block text-sm mb-1">模型覆盖</label>
                      <input
                        className="admin-input w-full px-3 py-2"
                        value={status.model || ''}
                        onChange={(event) =>
                          setStatus((prev) => (prev ? { ...prev, model: event.target.value || null } : prev))
                        }
                        placeholder="留空时使用全局默认模型"
                      />
                    </div>
                    <div>
                      <label className="block text-sm mb-1">模型提供方覆盖</label>
                      <input
                        className="admin-input w-full px-3 py-2"
                        value={status.provider || ''}
                        onChange={(event) =>
                          setStatus((prev) => (prev ? { ...prev, provider: event.target.value || null } : prev))
                        }
                        placeholder="可选，填写 provider 标识"
                      />
                    </div>
                    <div>
                      <label className="block text-sm mb-1">工具配置档</label>
                      <input
                        className="admin-input w-full px-3 py-2"
                        value={status.tool_profile}
                        onChange={(event) =>
                          setStatus((prev) => (prev ? { ...prev, tool_profile: event.target.value } : prev))
                        }
                      />
                    </div>
                    <div>
                      <label className="block text-sm mb-1">允许工具</label>
                      <input
                        className="admin-input w-full px-3 py-2"
                        value={status.tool_allow.join(', ')}
                        onChange={(event) =>
                          setStatus((prev) =>
                            prev
                              ? {
                                  ...prev,
                                  tool_allow: event.target.value
                                    .split(',')
                                    .map((item) => item.trim())
                                    .filter(Boolean),
                                }
                              : prev,
                          )
                        }
                        placeholder="例如：time_tool, sessions_list"
                      />
                    </div>
                    <div>
                      <label className="block text-sm mb-1">禁用工具</label>
                      <input
                        className="admin-input w-full px-3 py-2"
                        value={status.tool_deny.join(', ')}
                        onChange={(event) =>
                          setStatus((prev) =>
                            prev
                              ? {
                                  ...prev,
                                  tool_deny: event.target.value
                                    .split(',')
                                    .map((item) => item.trim())
                                    .filter(Boolean),
                                }
                              : prev,
                          )
                        }
                        placeholder="例如：shell, browser"
                      />
                    </div>
                    <div>
                      <label className="block text-sm mb-1">最大迭代次数</label>
                      <input
                        className="admin-input w-full px-3 py-2"
                        type="number"
                        min={1}
                        value={status.max_iterations}
                        onChange={(event) =>
                          setStatus((prev) =>
                            prev ? { ...prev, max_iterations: Number.parseInt(event.target.value || '1', 10) } : prev,
                          )
                        }
                      />
                    </div>
                    <div className="flex items-center gap-3 pt-7">
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={status.memory_auto_extract}
                          onChange={(event) =>
                            setStatus((prev) =>
                              prev ? { ...prev, memory_auto_extract: event.target.checked } : prev,
                            )
                          }
                        />
                        自动提炼记忆
                      </label>
                      <input
                        className="admin-input w-24 px-3 py-2"
                        type="number"
                        min={1}
                        value={status.memory_threshold}
                        onChange={(event) =>
                          setStatus((prev) =>
                            prev ? { ...prev, memory_threshold: Number.parseInt(event.target.value || '1', 10) } : prev,
                          )
                        }
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm mb-1">上下文摘要</label>
                    <textarea
                      className="admin-input w-full px-3 py-2 min-h-[140px]"
                      value={status.context_summary || ''}
                      onChange={(event) =>
                        setStatus((prev) => (prev ? { ...prev, context_summary: event.target.value } : prev))
                      }
                    />
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={async () => {
                        await updateSessionById(status.id, status);
                        await refreshStatus(status.id);
                      }}
                    >
                      保存
                    </button>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={async () => {
                        await updateSessionById(status.id, { is_default: true });
                        await refreshStatus(status.id);
                      }}
                    >
                      设为默认
                    </button>
                    {!status.is_default ? (
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={async () => {
                          await removeSession(status.id);
                          setStatus(null);
                        }}
                      >
                        删除
                      </button>
                    ) : null}
                  </div>

                  <div>
                    <div className="font-semibold mb-2">提示词来源</div>
                    <div className="text-sm opacity-80 space-y-1">
                      <div>工作区提示注入：{status.workspace_path ? '已启用' : '未启用'}</div>
                      <div>会话摘要注入：{status.context_summary ? '已启用' : '未启用'}</div>
                      <div>已启用技能数：{sessionSkills.filter((item) => item.enabled).length}</div>
                    </div>
                  </div>

                  <div>
                    <div className="font-semibold mb-2">技能</div>
                    <div className="space-y-2">
                      {availableSkills.map((skill) => {
                        const enabled = sessionSkills.some((item) => item.skill_name === skill.name && item.enabled);
                        return (
                          <label
                            key={skill.name}
                            className="flex items-start justify-between rounded-xl border p-3 gap-3"
                            style={{ borderColor: 'var(--panel-border)' }}
                          >
                            <div>
                              <div className="font-medium text-sm">{skill.name}</div>
                              <div className="text-xs opacity-70">{skill.description}</div>
                              <div className="text-[11px] opacity-60 mt-1">{skill.path}</div>
                            </div>
                            <input
                              type="checkbox"
                              checked={enabled}
                              onChange={async (event) => {
                                const nextSkills = event.target.checked
                                  ? [
                                      ...sessionSkills.filter((item) => item.skill_name !== skill.name),
                                      {
                                        skill_name: skill.name,
                                        skill_path: skill.path,
                                        enabled: true,
                                      },
                                    ]
                                  : sessionSkills.filter((item) => item.skill_name !== skill.name);
                                setSessionSkills(nextSkills);
                                await updateSessionSkills(status.id, nextSkills);
                              }}
                            />
                          </label>
                        );
                      })}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                    <div>
                      <div className="font-semibold mb-2">最近会话摘要</div>
                      <div
                        className="rounded-xl border p-3 text-sm whitespace-pre-wrap min-h-[180px]"
                        style={{ borderColor: 'var(--panel-border)' }}
                      >
                        {historySummary || '当前还没有最近会话摘要。'}
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="font-semibold">派发任务到其他工作会话</div>
                      <select
                        className="admin-select w-full px-3 py-2"
                        value={dispatchTargetId ?? ''}
                        onChange={(event) => setDispatchTargetId(Number.parseInt(event.target.value, 10))}
                      >
                        {sessions.map((session) => (
                          <option key={session.id} value={session.id}>
                            {session.name}
                          </option>
                        ))}
                      </select>
                      <textarea
                        className="admin-input w-full px-3 py-2 min-h-[140px]"
                        value={dispatchMessage}
                        onChange={(event) => setDispatchMessage(event.target.value)}
                        placeholder="输入要派发给其他工作会话的任务内容，并触发一次 Agent 运行。"
                      />
                      <button
                        type="button"
                        className="btn-secondary"
                        disabled={!dispatchTargetId || !dispatchMessage.trim() || isDispatching}
                        onClick={async () => {
                          if (!dispatchTargetId || !dispatchMessage.trim()) {
                            return;
                          }
                          setIsDispatching(true);
                          try {
                            await dispatchSessionMessage(dispatchTargetId, dispatchMessage.trim());
                            setDispatchMessage('');
                            await refreshStatus(status.id);
                          } finally {
                            setIsDispatching(false);
                          }
                        }}
                      >
                        {isDispatching ? '派发中...' : '派发任务'}
                      </button>
                    </div>
                  </div>

                  <div>
                    <div className="font-semibold mb-2">最近运行</div>
                    <div className="space-y-2">
                      {status.recent_runs.map((run) => (
                        <div
                          key={run.run_id}
                          className="rounded-xl border p-3"
                          style={{ borderColor: 'var(--panel-border)' }}
                        >
                          <div className="text-sm font-medium">{run.user_message}</div>
                          <div className="text-xs opacity-70">
                            {formatStopReason(run.stop_reason)} · {run.started_at || '暂无开始时间'}
                          </div>
                          {run.compacted_summary ? (
                            <div className="text-xs opacity-70 whitespace-pre-wrap mt-2">{run.compacted_summary}</div>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-sm opacity-70">选择一个工作会话后，可在这里查看它的运行状态、技能和最近任务。</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default SessionsPage;
