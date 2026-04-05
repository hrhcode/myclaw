import { useCallback, useEffect, useRef, useState } from "react";
import MainLayout from "../layout/MainLayout";
import Switch from "../admin/Switch";
import { Save } from "lucide-react";
import {
  createChannel,
  getChannels,
  getConversations,
  updateChannel,
} from "../../services/api";
import type { Channel, ChannelCreatePayload, Conversation } from "../../types";

// ── 预置通道定义 ──────────────────────────────────────────

interface PresetChannel {
  type: string;
  name: string;
  description: string;
  defaultConfig: Record<string, unknown>;
}

const PRESET_CHANNELS: PresetChannel[] = [
  {
    type: "qq",
    name: "QQ",
    description:
      "通过 QQ 官方机器人 API 接入，需在 QQ 开放平台创建机器人获取 AppId 和 AppSecret",
    defaultConfig: {
      app_id: "",
      app_secret: "",
      trigger_mode: "at_or_mention",
      private_enabled: true,
    },
  },
];

// ── 状态展示映射 ──────────────────────────────────────────

const statusLabel: Record<string, string> = {
  running: "运行中",
  stopped: "已停止",
  error: "错误",
};

const statusColor: Record<string, string> = {
  running: "#22c55e",
  stopped: "#94a3b8",
  error: "#ef4444",
};

// ── Toast ─────────────────────────────────────────────────

interface ToastState {
  type: "success" | "error";
  text: string;
}

function Toast({ message }: { message: ToastState | null }) {
  if (!message) return null;
  return (
    <div
      className="fixed top-4 left-1/2 -translate-x-1/2 z-[60] px-4 py-2 rounded-lg text-sm shadow-lg"
      style={{
        background:
          message.type === "success"
            ? "rgba(34,197,94,0.15)"
            : "rgba(239,68,68,0.15)",
        color: message.type === "success" ? "#22c55e" : "var(--accent-danger)",
        border: `1px solid ${message.type === "success" ? "rgba(34,197,94,0.3)" : "rgba(239,68,68,0.3)"}`,
      }}
    >
      {message.text}
    </div>
  );
}

// ── 主组件 ────────────────────────────────────────────────

const ChannelsPage: React.FC = () => {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [togglingType, setTogglingType] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastState | null>(null);

  const [localValues, setLocalValues] = useState<
    Record<string, Record<string, string>>
  >({});
  const channelsRef = useRef<Channel[]>([]);

  const showToast = useCallback((type: "success" | "error", text: string) => {
    setToast({ type, text });
    window.setTimeout(() => setToast(null), 2400);
  }, []);

  const loadChannels = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getChannels();
      setChannels(data);
      channelsRef.current = data;
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadChannels();
    getConversations()
      .then(setConversations)
      .catch(() => {});
  }, [loadChannels]);

  const getChannelByType = (type: string): Channel | undefined =>
    channels.find((ch) => ch.channel_type === type);

  const getLocal = (type: string, key: string, fallback: unknown): string => {
    if (localValues[type] && key in localValues[type]) {
      return localValues[type][key];
    }
    const ch = getChannelByType(type);
    if (key === "_name" && ch) return ch.name;
    if (key === "conversation_id" && ch)
      return ch.conversation_id != null ? String(ch.conversation_id) : "";
    const val = ch ? ch.config[key] : undefined;
    if (val !== undefined && val !== null) return String(val);
    return fallback !== undefined && fallback !== null ? String(fallback) : "";
  };

  const setLocal = (type: string, key: string, value: string) => {
    setLocalValues((prev) => ({
      ...prev,
      [type]: { ...(prev[type] || {}), [key]: value },
    }));
  };

  const saveChannelConfig = useCallback(
    async (type: string) => {
      const ch = channelsRef.current.find((c) => c.channel_type === type);
      if (!ch) return;

      const localData = localValues[type];
      if (!localData || Object.keys(localData).length === 0) {
        showToast("success", "配置无变化");
        return;
      }

      const payload: {
        name?: string;
        config?: Record<string, unknown>;
        conversation_id?: number | null;
      } = {};
      const newConfig: Record<string, unknown> = { ...ch.config };

      for (const [key, value] of Object.entries(localData)) {
        if (key === "_name") {
          payload.name = value;
        } else if (key === "conversation_id") {
          payload.conversation_id =
            value === "" || value === "0" ? null : Number(value);
        } else {
          newConfig[key] = value;
        }
      }

      if (Object.keys(newConfig).length > 0) {
        payload.config = newConfig;
      }

      try {
        const updated = await updateChannel(ch.id, payload);
        channelsRef.current = channelsRef.current.map((c) =>
          c.id === ch.id ? { ...c, ...updated } : c,
        );
        setChannels((prev) =>
          prev.map((c) => (c.id === ch.id ? { ...c, ...updated } : c)),
        );
        setLocalValues((prev) => {
          const next = { ...prev };
          delete next[type];
          return next;
        });
        showToast("success", "配置已保存");
      } catch (err) {
        showToast("error", err instanceof Error ? err.message : "保存失败");
      }
    },
    [localValues, showToast],
  );

  const hasLocalChanges = (type: string): boolean => {
    const localData = localValues[type];
    if (!localData || Object.keys(localData).length === 0) return false;
    const ch = getChannelByType(type);
    if (!ch) return Object.keys(localData).length > 0;
    for (const [key, value] of Object.entries(localData)) {
      let serverVal: unknown;
      if (key === "_name") {
        serverVal = ch.name;
      } else if (key === "conversation_id") {
        serverVal = ch.conversation_id ?? "";
      } else {
        serverVal = ch.config[key];
      }
      if (String(serverVal ?? "") !== value) return true;
    }
    return false;
  };

  const handleToggle = async (preset: PresetChannel) => {
    const existing = getChannelByType(preset.type);
    setTogglingType(preset.type);
    try {
      if (existing) {
        await updateChannel(existing.id, { enabled: !existing.enabled });
      } else {
        const payload: ChannelCreatePayload = {
          name: preset.name,
          channel_type: preset.type,
          enabled: true,
          config: preset.defaultConfig,
        };
        await createChannel(payload);
      }
      await loadChannels();
    } catch (err) {
      showToast("error", err instanceof Error ? err.message : "操作失败");
    } finally {
      setTogglingType(null);
    }
  };

  if (loading) {
    return (
      <MainLayout headerTitle="通道">
        <div className="admin-page">
          <div className="admin-frame">
            <div
              className="admin-card p-6 text-sm"
              style={{ color: "var(--text-secondary)" }}
            >
              正在加载通道配置...
            </div>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout headerTitle="通道">
      <Toast message={toast} />
      <div className="admin-page">
        <div className="admin-frame settings-page-shell settings-page-shell--minimal">
          {error && (
            <div
              className="warning-banner px-4 py-3 text-sm"
              style={{ color: "var(--text-secondary)" }}
            >
              {error}
            </div>
          )}

          <div className="channels-grid">
            {PRESET_CHANNELS.map((preset) => {
              const ch = getChannelByType(preset.type);
              const isEnabled = ch?.enabled ?? false;
              const busy = togglingType === preset.type;

              return (
                <div key={preset.type} className="channel-card">
                  <div className="channel-card__header">
                    <div className="channel-card__title-row">
                      <h3 className="channel-card__title">{preset.name}</h3>
                      <div className="flex items-center gap-2">
                        {ch && (
                          <span className="channel-card__status">
                            <span
                              className="channel-card__status-dot"
                              style={{
                                background: statusColor[ch.status] || "#94a3b8",
                              }}
                            />
                            {statusLabel[ch.status] || ch.status}
                          </span>
                        )}
                        <Switch
                          checked={isEnabled}
                          onChange={() => handleToggle(preset)}
                          ariaLabel={`切换${preset.name}启用状态`}
                        />
                        {busy && (
                          <span className="channel-card__busy">处理中…</span>
                        )}
                      </div>
                    </div>
                    <p className="channel-card__desc">{preset.description}</p>
                  </div>

                  {preset.type === "qq" && (
                    <div className="channel-card__body">
                      <div className="channel-card__row">
                        <div className="channel-card__field">
                          <label>名称</label>
                          <input
                            type="text"
                            className="admin-input"
                            value={getLocal(preset.type, "_name", preset.name)}
                            onChange={(e) =>
                              setLocal(preset.type, "_name", e.target.value)
                            }
                            placeholder="输入名称"
                          />
                        </div>
                        <div className="channel-card__field">
                          <label>AppId</label>
                          <input
                            type="text"
                            className="admin-input"
                            value={getLocal(preset.type, "app_id", "")}
                            onChange={(e) =>
                              setLocal(preset.type, "app_id", e.target.value)
                            }
                            placeholder="机器人 AppId"
                          />
                        </div>
                      </div>
                      <div className="channel-card__row">
                        <div className="channel-card__field">
                          <label>AppSecret</label>
                          <input
                            type="password"
                            className="admin-input"
                            value={getLocal(preset.type, "app_secret", "")}
                            onChange={(e) =>
                              setLocal(
                                preset.type,
                                "app_secret",
                                e.target.value,
                              )
                            }
                            placeholder="机器人 AppSecret"
                          />
                        </div>
                        <div className="channel-card__field">
                          <label>触发模式</label>
                          <select
                            className="admin-select"
                            value={getLocal(
                              preset.type,
                              "trigger_mode",
                              "at_or_mention",
                            )}
                            onChange={(e) =>
                              setLocal(
                                preset.type,
                                "trigger_mode",
                                e.target.value,
                              )
                            }
                          >
                            <option value="at_or_mention">@ 或提及</option>
                            <option value="all_messages">所有消息</option>
                          </select>
                        </div>
                      </div>
                      <div className="channel-card__row">
                        <div className="channel-card__field channel-card__field--toggle">
                          <label>启用私聊</label>
                          <Switch
                            checked={
                              getLocal(
                                preset.type,
                                "private_enabled",
                                "true",
                              ) === "true"
                            }
                            onChange={(v) =>
                              setLocal(
                                preset.type,
                                "private_enabled",
                                String(v),
                              )
                            }
                            ariaLabel="切换私聊"
                          />
                        </div>
                        <div className="channel-card__field">
                          <label>绑定会话</label>
                          <select
                            className="admin-select"
                            value={getLocal(preset.type, "conversation_id", "")}
                            onChange={(e) =>
                              setLocal(
                                preset.type,
                                "conversation_id",
                                e.target.value,
                              )
                            }
                          >
                            <option value="">不绑定</option>
                            {conversations.map((c) => (
                              <option key={c.id} value={c.id}>
                                {c.title}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>
                      <div className="channel-card__footer">
                        <button
                          type="button"
                          className="btn channel-save-btn"
                          onClick={() => saveChannelConfig(preset.type)}
                          disabled={!ch || !hasLocalChanges(preset.type)}
                        >
                          <Save size={16} />
                          <span>保存配置</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default ChannelsPage;
