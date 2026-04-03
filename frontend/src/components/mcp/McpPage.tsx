import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BellRing,
  Blocks,
  CheckCircle2,
  Database,
  FolderKanban,
  Globe,
  Loader2,
  Plus,
  PlugZap,
  RefreshCw,
  Save,
  Search,
  Server,
  ShieldAlert,
  TerminalSquare,
  Trash2,
  Wrench,
} from "lucide-react";

import MainLayout from "../layout/MainLayout";
import { PageSection, SectionCard, SegmentedTabs, StatusBadge } from "../admin";
import {
  createMcpServer,
  deleteMcpServer,
  getMcpServers,
  getMcpStats,
  probeAllMcpServers,
  probeMcpServer,
  updateMcpServer,
} from "../../services/api";
import type { McpServer, McpServerPayload, McpStats } from "../../types";

type FilterKey = "all" | "connected" | "attention" | "disabled";

type DraftServer = McpServerPayload & {
  id?: string;
  status?: McpServer["status"];
  resources?: number;
  tools?: number;
  prompts?: number;
  alerts?: number;
  capabilities?: string[];
  tool_names?: string[];
  resource_names?: string[];
  prompt_names?: string[];
  status_reason?: string | null;
  last_probe_at?: string | null;
  updated_at?: string | null;
  events?: McpServer["events"];
};

const FILTER_TABS: Array<{ key: FilterKey; label: string }> = [
  { key: "all", label: "全部" },
  { key: "connected", label: "已连接" },
  { key: "attention", label: "需关注" },
  { key: "disabled", label: "未启用" },
];

const STATUS_META: Record<
  McpServer["status"],
  { label: string; tone: "success" | "warning" | "neutral" }
> = {
  connected: { label: "已连接", tone: "success" },
  degraded: { label: "需关注", tone: "warning" },
  disabled: { label: "未启用", tone: "neutral" },
};

const TRANSPORT_LABEL: Record<McpServer["transport"], string> = {
  stdio: "STDIO",
  http: "HTTP",
  sse: "SSE",
};

const EMPTY_DRAFT: DraftServer = {
  name: "新 MCP 服务",
  description: "",
  transport: "stdio",
  command: "",
  args: [],
  endpoint: "",
  enabled: true,
  tags: [],
  workspaces: [],
  env: {},
  headers: {},
  timeout_seconds: 8,
  status: "disabled",
  resources: 0,
  tools: 0,
  prompts: 0,
  alerts: 0,
  capabilities: [],
  tool_names: [],
  resource_names: [],
  prompt_names: [],
  status_reason: "未保存",
  last_probe_at: null,
  updated_at: null,
  events: [],
};

const McpPage: React.FC = () => {
  const [servers, setServers] = useState<McpServer[]>([]);
  const [stats, setStats] = useState<McpStats>({ total: 0, enabled: 0, resources: 0, alerts: 0 });
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<FilterKey>("all");
  const [selectedId, setSelectedId] = useState<string>("");
  const [draft, setDraft] = useState<DraftServer | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const visibleServers = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return servers.filter((server) => {
      const matchesQuery =
        normalizedQuery.length === 0 ||
        [
          server.name,
          server.description,
          server.transport,
          ...server.tags,
          ...server.capabilities,
          ...server.tool_names,
          ...server.resource_names,
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalizedQuery);

      const matchesFilter =
        filter === "all" ||
        (filter === "connected" && server.status === "connected") ||
        (filter === "attention" && (server.status === "degraded" || server.alerts > 0)) ||
        (filter === "disabled" && !server.enabled);

      return matchesQuery && matchesFilter;
    });
  }, [filter, query, servers]);

  const loadPage = async (preferredId?: string) => {
    const [serverData, statsData] = await Promise.all([getMcpServers(), getMcpStats()]);
    setServers(serverData);
    setStats(statsData);

    const nextId = preferredId ?? selectedId ?? serverData[0]?.id ?? "";
    setSelectedId(nextId);
    if (nextId && nextId !== "__new__") {
      const selected = serverData.find((item) => item.id === nextId) ?? serverData[0] ?? null;
      setDraft(selected ? { ...selected } : null);
    } else if (!draft || preferredId !== "__new__") {
      setDraft(serverData[0] ? { ...serverData[0] } : null);
    }
  };

  useEffect(() => {
    void (async () => {
      try {
        setLoading(true);
        await loadPage();
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "加载 MCP 服务失败");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (selectedId === "__new__") return;
    const selected = servers.find((item) => item.id === selectedId) ?? null;
    setDraft(selected ? { ...selected } : null);
  }, [selectedId, servers]);

  const setDraftValue = <K extends keyof DraftServer>(key: K, value: DraftServer[K]) => {
    setDraft((current) => (current ? { ...current, [key]: value } : current));
  };

  const handleCreateDraft = () => {
    setSelectedId("__new__");
    setDraft({ ...EMPTY_DRAFT });
    setError(null);
  };

  const handleSave = async () => {
    if (!draft) return;
    try {
      setBusy(true);
      setError(null);
      const payload = toPayload(draft);
      const saved = draft.id
        ? await updateMcpServer(draft.id, payload)
        : await createMcpServer(payload);
      await loadPage(saved.id);
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "保存 MCP 服务失败");
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    if (!draft?.id) return;
    const confirmed = window.confirm(`确认删除 MCP 服务“${draft.name}”吗？`);
    if (!confirmed) return;
    try {
      setBusy(true);
      setError(null);
      await deleteMcpServer(draft.id);
      const nextId = servers.find((item) => item.id !== draft.id)?.id;
      await loadPage(nextId);
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "删除 MCP 服务失败");
    } finally {
      setBusy(false);
    }
  };

  const handleToggleEnabled = async () => {
    if (!draft?.id) return;
    try {
      setBusy(true);
      setError(null);
      const updated = await updateMcpServer(draft.id, { enabled: !draft.enabled });
      await loadPage(updated.id);
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "切换 MCP 服务状态失败");
    } finally {
      setBusy(false);
    }
  };

  const handleProbe = async () => {
    if (!draft?.id) return;
    try {
      setBusy(true);
      setError(null);
      const probed = await probeMcpServer(draft.id);
      await loadPage(probed.id);
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "探测 MCP 服务失败");
    } finally {
      setBusy(false);
    }
  };

  const handleProbeAll = async () => {
    try {
      setBusy(true);
      setError(null);
      const result = await probeAllMcpServers();
      setServers(result);
      setSelectedId((current) => current || result[0]?.id || "");
      setDraft((current) => {
        if (current?.id) {
          const matched = result.find((item) => item.id === current.id);
          return matched ? { ...matched } : result[0] ? { ...result[0] } : null;
        }
        return current?.id === "__new__" ? current : result[0] ? { ...result[0] } : null;
      });
      setStats(await getMcpStats());
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "批量探测 MCP 服务失败");
    } finally {
      setBusy(false);
    }
  };

  const canSave = Boolean(
    draft &&
      draft.name.trim() &&
      ((draft.transport === "stdio" && draft.command?.trim()) ||
        (draft.transport !== "stdio" && draft.endpoint?.trim())),
  );

  if (loading) {
    return (
      <MainLayout headerTitle="MCP" headerSubtitle="正在加载 MCP 配置与最近状态">
        <div className="admin-page">
          <div className="admin-frame">
            <SectionCard className="p-6">
              <div className="text-sm" style={{ color: "var(--text-secondary)" }}>
                正在加载 MCP 服务...
              </div>
            </SectionCard>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout
      headerTitle="MCP"
      headerSubtitle="只保留 MCP 管理最关键的动作：查看、新增、启停、删除、探测。探测成功后会自动接入运行时工具。"
      headerActions={
        <div className="admin-toolbar">
          <button
            type="button"
            onClick={() => void loadPage(selectedId === "__new__" ? undefined : selectedId)}
            className="btn-secondary inline-flex items-center gap-2"
            disabled={busy}
          >
            <RefreshCw size={16} />
            刷新
          </button>
          <button
            type="button"
            onClick={() => void handleProbeAll()}
            className="btn-secondary inline-flex items-center gap-2"
            disabled={busy || servers.length === 0}
          >
            {busy ? <Loader2 size={16} className="animate-spin" /> : <Activity size={16} />}
            全量探测
          </button>
          <button
            type="button"
            onClick={handleCreateDraft}
            className="btn-primary inline-flex items-center gap-2"
            disabled={busy}
          >
            <Plus size={16} />
            新建服务
          </button>
        </div>
      }
    >
      <div className="admin-page">
        <div className="admin-frame max-w-[1460px]">
          <section className="admin-summary">
            <SummaryCard label="MCP 服务" value={stats.total} hint="统一纳入左侧控制台管理" />
            <SummaryCard label="已启用" value={stats.enabled} hint="启用后可执行探测与资源发现" />
            <SummaryCard label="可用资源" value={stats.resources} hint="资源总量来自最近一次探测结果" />
            <SummaryCard label="待处理告警" value={stats.alerts} hint="探测失败或状态异常会累积到这里" />
          </section>

          {error ? (
            <div className="warning-banner px-4 py-3 text-sm" style={{ color: "#b45309" }}>
              {error}
            </div>
          ) : null}

          <div className="grid gap-4 xl:grid-cols-[340px_minmax(0,1fr)]">
            <aside className="admin-card flex min-h-[780px] flex-col overflow-hidden">
              <div className="border-b p-4" style={{ borderColor: "var(--panel-border)" }}>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>服务器列表</div>
                    <div className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                      点击左侧服务可编辑配置并执行单点探测。
                    </div>
                  </div>
                  <StatusBadge tone="info">{visibleServers.length} 个</StatusBadge>
                </div>

                <div className="relative mt-4">
                  <Search
                    size={16}
                    className="absolute left-3 top-1/2 -translate-y-1/2"
                    style={{ color: "var(--text-muted)" }}
                  />
                  <input
                    type="text"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="搜索服务、能力或标签"
                    className="admin-input h-10 w-full pl-9 pr-3"
                  />
                </div>

                <div className="mt-4">
                  <SegmentedTabs tabs={FILTER_TABS} activeKey={filter} onChange={(key) => setFilter(key as FilterKey)} compact equalWidth />
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-3">
                <div className="grid gap-2">
                  {visibleServers.map((server) => {
                    const isActive = server.id === selectedId;
                    const statusMeta = STATUS_META[server.status];

                    return (
                      <button
                        key={server.id}
                        type="button"
                        onClick={() => setSelectedId(server.id)}
                        className="rounded-2xl border p-4 text-left transition"
                        style={{
                          borderColor: isActive
                            ? "color-mix(in srgb, var(--accent) 35%, var(--panel-border))"
                            : "var(--panel-border)",
                          background: isActive
                            ? "color-mix(in srgb, var(--accent) 10%, var(--surface-elevated))"
                            : "var(--surface-elevated)",
                        }}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <div className="truncate text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                              {server.name}
                            </div>
                            <div className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                              {server.transport.toUpperCase()} · {server.tools} tools · {server.resources} resources
                            </div>
                          </div>
                          <StatusBadge tone={statusMeta.tone}>{statusMeta.label}</StatusBadge>
                        </div>

                        <p className="mt-3 text-xs leading-6" style={{ color: "var(--text-secondary)" }}>
                          {server.description || "暂无描述"}
                        </p>

                        <div className="mt-3 flex flex-wrap gap-2">
                          {server.tags.map((tag) => (
                            <span
                              key={tag}
                              className="rounded-full px-2.5 py-1 text-[11px]"
                              style={{ background: "var(--surface-subtle)", color: "var(--text-secondary)" }}
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </aside>

            {draft ? (
              <div className="grid gap-4">
                <PageSection
                  title={draft.name || "新 MCP 服务"}
                  description={draft.description || "这里可以编辑 MCP 服务配置，并直接发起真实探测。"}
                  actions={
                    <StatusBadge tone={STATUS_META[draft.status || "disabled"].tone}>
                      {STATUS_META[draft.status || "disabled"].label}
                    </StatusBadge>
                  }
                >
                  <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
                    <SectionCard className="p-5">
                      <div className="grid gap-4 md:grid-cols-2">
                        <InfoTile icon={<Server size={16} />} label="传输方式" value={TRANSPORT_LABEL[draft.transport]} />
                        <InfoTile icon={<Activity size={16} />} label="最近探测" value={formatTime(draft.last_probe_at)} />
                        <InfoTile icon={<Database size={16} />} label="资源总量" value={`${draft.resources || 0} resources`} />
                        <InfoTile icon={<Wrench size={16} />} label="工具总量" value={`${draft.tools || 0} tools`} />
                      </div>

                      <div className="mt-5 grid gap-4">
                        <Field label="服务名称">
                          <input
                            type="text"
                            value={draft.name}
                            onChange={(event) => setDraftValue("name", event.target.value)}
                            className="admin-input h-11 px-3"
                          />
                        </Field>

                        <Field label="描述">
                          <textarea
                            value={draft.description}
                            onChange={(event) => setDraftValue("description", event.target.value)}
                            rows={3}
                            className="admin-input resize-y px-3 py-3"
                          />
                        </Field>

                        <div className="grid gap-4 md:grid-cols-3">
                          <Field label="传输方式">
                            <select
                              value={draft.transport}
                              onChange={(event) => setDraftValue("transport", event.target.value as DraftServer["transport"])}
                              className="admin-select h-11 px-3"
                            >
                              <option value="stdio">STDIO</option>
                              <option value="http">HTTP</option>
                              <option value="sse">SSE</option>
                            </select>
                          </Field>

                          <Field label="启用状态">
                            <select
                              value={draft.enabled ? "enabled" : "disabled"}
                              onChange={(event) => setDraftValue("enabled", event.target.value === "enabled")}
                              className="admin-select h-11 px-3"
                            >
                              <option value="enabled">启用</option>
                              <option value="disabled">停用</option>
                            </select>
                          </Field>

                          <Field label="超时秒数">
                            <input
                              type="number"
                              min="1"
                              value={draft.timeout_seconds}
                              onChange={(event) => setDraftValue("timeout_seconds", Number(event.target.value) || 8)}
                              className="admin-input h-11 px-3"
                            />
                          </Field>
                        </div>

                        {draft.transport === "stdio" ? (
                          <>
                            <Field label="启动命令">
                              <input
                                type="text"
                                value={draft.command || ""}
                                onChange={(event) => setDraftValue("command", event.target.value)}
                                className="admin-input h-11 px-3"
                                placeholder="例如：npx"
                              />
                            </Field>
                            <Field label="参数（JSON 数组）">
                              <textarea
                                value={JSON.stringify(draft.args, null, 2)}
                                onChange={(event) => setDraftValue("args", parseJsonArray(event.target.value))}
                                rows={4}
                                className="admin-input font-mono resize-y px-3 py-3"
                              />
                            </Field>
                          </>
                        ) : (
                          <Field label={draft.transport === "http" ? "MCP Endpoint" : "SSE Endpoint"}>
                            <input
                              type="text"
                              value={draft.endpoint || ""}
                              onChange={(event) => setDraftValue("endpoint", event.target.value)}
                              className="admin-input h-11 px-3"
                              placeholder="http://localhost:8811/mcp"
                            />
                          </Field>
                        )}

                        <div className="grid gap-4 lg:grid-cols-2">
                          <Field label="标签（逗号分隔）">
                            <input
                              type="text"
                              value={draft.tags.join(", ")}
                              onChange={(event) => setDraftValue("tags", splitCsv(event.target.value))}
                              className="admin-input h-11 px-3"
                            />
                          </Field>

                          <Field label="工作区（换行分隔）">
                            <textarea
                              value={draft.workspaces.join("\n")}
                              onChange={(event) => setDraftValue("workspaces", splitLines(event.target.value))}
                              rows={3}
                              className="admin-input resize-y px-3 py-3"
                            />
                          </Field>
                        </div>

                        <div className="grid gap-4 lg:grid-cols-2">
                          <Field label="环境变量（JSON 对象）">
                            <textarea
                              value={JSON.stringify(draft.env, null, 2)}
                              onChange={(event) => setDraftValue("env", parseJsonObject(event.target.value))}
                              rows={6}
                              className="admin-input font-mono resize-y px-3 py-3"
                            />
                          </Field>

                          <Field label="请求头（JSON 对象）">
                            <textarea
                              value={JSON.stringify(draft.headers, null, 2)}
                              onChange={(event) => setDraftValue("headers", parseJsonObject(event.target.value))}
                              rows={6}
                              className="admin-input font-mono resize-y px-3 py-3"
                            />
                          </Field>
                        </div>
                      </div>
                    </SectionCard>

                    <SectionCard className="p-5">
                      <div className="flex items-center gap-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                        <BellRing size={16} />
                        健康概览
                      </div>
                      <div className="mt-4 grid gap-3">
                        <HealthRow
                          icon={<PlugZap size={16} />}
                          label="运行时接入"
                          value={draft.status === "connected" && (draft.tool_names?.length || 0) > 0 ? `已注册 ${draft.tool_names?.length || 0} 个工具` : "需先探测成功"}
                        />
                        <HealthRow
                          icon={<CheckCircle2 size={16} />}
                          label="状态说明"
                          value={draft.status_reason || "暂无说明"}
                        />
                        <HealthRow
                          icon={<ShieldAlert size={16} />}
                          label="告警数量"
                          value={draft.alerts ? `${draft.alerts} 项待处理` : "暂无告警"}
                        />
                        <HealthRow
                          icon={<Blocks size={16} />}
                          label="Prompts"
                          value={`${draft.prompts || 0} 个`}
                        />
                      </div>

                      <div className="mt-4 grid gap-2">
                        <button
                          type="button"
                          onClick={() => void handleProbe()}
                          className="btn-secondary inline-flex items-center justify-center gap-2"
                          disabled={busy || !draft.id}
                        >
                          {busy ? <Loader2 size={16} className="animate-spin" /> : <PlugZap size={16} />}
                          探测当前服务
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleSave()}
                          className="btn-primary inline-flex items-center justify-center gap-2"
                          disabled={busy || !canSave}
                        >
                          <Save size={16} />
                          保存配置
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleToggleEnabled()}
                          className="btn-secondary inline-flex items-center justify-center gap-2"
                          disabled={busy || !draft.id}
                        >
                          <PlugZap size={16} />
                          {draft.enabled ? "暂停服务" : "启用服务"}
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleDelete()}
                          className="btn-secondary inline-flex items-center justify-center gap-2"
                          disabled={busy || !draft.id}
                        >
                          <Trash2 size={16} />
                          删除服务
                        </button>
                      </div>
                    </SectionCard>
                  </div>
                </PageSection>

                <div className="grid gap-4 2xl:grid-cols-[minmax(0,1fr)_360px]">
                  <PageSection
                    title="资源与能力"
                    description="探测成功后会在这里展示真实的 tools、resources、prompts 能力列表。"
                  >
                    <div className="grid gap-4 lg:grid-cols-3">
                      <CapabilityCard
                        icon={<FolderKanban size={16} />}
                        title="Resources"
                        items={draft.resource_names || []}
                        emptyText="当前未发现 resources"
                      />
                      <CapabilityCard
                        icon={<TerminalSquare size={16} />}
                        title="Tools"
                        items={draft.tool_names || []}
                        emptyText="当前未发现 tools"
                      />
                      <CapabilityCard
                        icon={<Globe size={16} />}
                        title="Prompts"
                        items={draft.prompt_names || []}
                        emptyText="当前未发现 prompts"
                      />
                    </div>
                  </PageSection>

                  <PageSection
                    title="最近事件"
                    description="这里展示本服务最近的探测与状态变化。"
                  >
                    <div className="grid gap-3">
                      {(draft.events || []).length > 0 ? (
                        (draft.events || []).map((event) => (
                          <SectionCard key={event.id} className="p-4">
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <div className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                                  {event.message}
                                </div>
                                <div className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
                                  {event.time}
                                </div>
                              </div>
                              <StatusBadge tone={event.level === "success" ? "success" : event.level === "warning" ? "warning" : "info"}>
                                {event.level === "success" ? "成功" : event.level === "warning" ? "提示" : "信息"}
                              </StatusBadge>
                            </div>
                          </SectionCard>
                        ))
                      ) : (
                        <SectionCard className="p-4">
                          <div className="text-sm" style={{ color: "var(--text-muted)" }}>
                            暂无事件记录。
                          </div>
                        </SectionCard>
                      )}
                    </div>
                  </PageSection>
                </div>
              </div>
            ) : (
              <SectionCard className="p-6">
                <div className="text-sm" style={{ color: "var(--text-muted)" }}>
                  当前还没有 MCP 服务。可以点击右上角“新建服务”开始配置。
                </div>
              </SectionCard>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

const SummaryCard: React.FC<{ label: string; value: number; hint: string }> = ({ label, value, hint }) => (
  <SectionCard className="p-5">
    <div className="text-xs" style={{ color: "var(--text-muted)" }}>{label}</div>
    <div className="mt-2 text-2xl font-semibold" style={{ color: "var(--text-primary)" }}>{value}</div>
    <div className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>{hint}</div>
  </SectionCard>
);

const Field: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <label className="grid gap-2">
    <span className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>{label}</span>
    {children}
  </label>
);

const InfoTile: React.FC<{ icon: React.ReactNode; label: string; value: string }> = ({ icon, label, value }) => (
  <div className="rounded-2xl border p-4" style={{ borderColor: "var(--panel-border)" }}>
    <div className="flex items-center gap-2 text-xs" style={{ color: "var(--text-muted)" }}>
      {icon}
      {label}
    </div>
    <div className="mt-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{value}</div>
  </div>
);

const HealthRow: React.FC<{ icon: React.ReactNode; label: string; value: string }> = ({ icon, label, value }) => (
  <div className="flex items-center justify-between gap-3 rounded-2xl border px-4 py-3" style={{ borderColor: "var(--panel-border)" }}>
    <div className="flex items-center gap-2 text-sm" style={{ color: "var(--text-secondary)" }}>
      {icon}
      {label}
    </div>
    <div className="max-w-[160px] text-right text-sm font-medium" style={{ color: "var(--text-primary)" }}>
      {value}
    </div>
  </div>
);

const CapabilityCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  items: string[];
  emptyText: string;
}> = ({ icon, title, items, emptyText }) => (
  <SectionCard className="p-5">
    <div className="flex items-center gap-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
      {icon}
      {title}
    </div>
    <div className="mt-4 grid gap-2">
      {items.length > 0 ? (
        items.map((item) => (
          <div key={item} className="rounded-xl border px-3 py-2 text-sm" style={{ borderColor: "var(--panel-border)", color: "var(--text-secondary)" }}>
            {item}
          </div>
        ))
      ) : (
        <div className="rounded-xl border border-dashed px-3 py-4 text-sm" style={{ borderColor: "var(--panel-border)", color: "var(--text-muted)" }}>
          {emptyText}
        </div>
      )}
    </div>
  </SectionCard>
);

const toPayload = (draft: DraftServer): McpServerPayload => ({
  name: draft.name.trim(),
  description: draft.description.trim(),
  transport: draft.transport,
  command: draft.command?.trim() || null,
  args: draft.args,
  endpoint: draft.endpoint?.trim() || null,
  enabled: draft.enabled,
  tags: draft.tags,
  workspaces: draft.workspaces,
  env: draft.env,
  headers: draft.headers,
  timeout_seconds: draft.timeout_seconds,
});

const splitCsv = (value: string) =>
  value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

const splitLines = (value: string) =>
  value
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);

const parseJsonArray = (value: string) => {
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed.map(String) : [];
  } catch {
    return [];
  }
};

const parseJsonObject = (value: string) => {
  try {
    const parsed = JSON.parse(value);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return {};
    }
    return Object.fromEntries(
      Object.entries(parsed).map(([key, item]) => [key, String(item)]),
    );
  } catch {
    return {};
  }
};

const formatTime = (value?: string | null) => {
  if (!value) return "未探测";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
};

export default McpPage;
