import { useCallback, useEffect, useState } from "react";
import MainLayout from "../layout/MainLayout";
import PageSection from "../admin/PageSection";
import SegmentedTabs from "../admin/SegmentedTabs";
import TaskListTab from "./TaskListTab";
import HistoryTab from "./HistoryTab";
import AutomationFormModal from "./AutomationFormModal";
import {
  createAutomation,
  deleteAutomation,
  getAllAutomationRuns,
  getAutomations,
  getAutomationStats,
  getConversations,
  runAutomationNow,
  updateAutomation,
} from "../../services/api";
import type {
  Automation,
  AutomationPayload,
  AutomationRun,
  AutomationStats,
  Conversation,
} from "../../types";

const TABS = [
  { key: "tasks", label: "任务列表" },
  { key: "history", label: "历史任务" },
];

const EMPTY_STATS: AutomationStats = {
  total: 0,
  enabled: 0,
  disabled: 0,
  due_now: 0,
  running: 0,
  failed_recently: 0,
  next_run_at: null,
  last_run_at: null,
};

const AutomationsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState("tasks");
  const [automations, setAutomations] = useState<Automation[]>([]);
  const [stats, setStats] = useState<AutomationStats>(EMPTY_STATS);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [historyRuns, setHistoryRuns] = useState<AutomationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editingAutomation, setEditingAutomation] = useState<Automation | null>(null);

  const refreshTaskList = useCallback(async () => {
    const [automationData, statsData, conversationData] = await Promise.all([
      getAutomations(),
      getAutomationStats(),
      getConversations(),
    ]);
    setAutomations(automationData);
    setStats(statsData);
    setConversations(conversationData);
  }, []);

  const refreshHistory = useCallback(async () => {
    const runs = await getAllAutomationRuns();
    setHistoryRuns(runs);
  }, []);

  // Build latest run map for task cards
  const latestRuns = new Map<number, AutomationRun>();
  for (const run of historyRuns) {
    if (!latestRuns.has(run.automation_id)) {
      latestRuns.set(run.automation_id, run);
    }
  }

  // Initial load
  useEffect(() => {
    void (async () => {
      try {
        await refreshTaskList();
      } catch (err) {
        console.error("Failed to load automations", err);
        setError(err instanceof Error ? err.message : "加载自动化失败");
      } finally {
        setLoading(false);
      }
    })();
  }, [refreshTaskList]);

  // Load history when switching to history tab
  useEffect(() => {
    if (activeTab === "history") {
      void refreshHistory().catch((err) => {
        console.error("Failed to load history", err);
        setError(err instanceof Error ? err.message : "加载执行记录失败");
      });
    }
  }, [activeTab, refreshHistory]);

  const handleCreate = () => {
    if (conversations.length === 0) {
      setError("请先创建至少一个会话，再创建自动化任务。");
      return;
    }
    setEditingAutomation(null);
    setModalOpen(true);
  };

  const handleEdit = (id: number) => {
    const automation = automations.find((a) => a.id === id);
    if (!automation) return;
    setEditingAutomation(automation);
    setModalOpen(true);
  };

  const handleSave = async (payload: AutomationPayload, id?: number) => {
    try {
      setBusy(true);
      setError(null);
      if (id) {
        await updateAutomation(id, payload);
      } else {
        await createAutomation(payload);
      }
      await refreshTaskList();
    } finally {
      setBusy(false);
    }
  };

  const handleToggle = async (id: number) => {
    const automation = automations.find((a) => a.id === id);
    if (!automation) return;
    try {
      setBusy(true);
      setError(null);
      await updateAutomation(id, { enabled: !automation.enabled });
      await refreshTaskList();
    } catch (err) {
      console.error("Failed to toggle automation", err);
      setError(err instanceof Error ? err.message : "切换启用状态失败");
    } finally {
      setBusy(false);
    }
  };

  const handleRun = async (id: number) => {
    try {
      setBusy(true);
      setError(null);
      await runAutomationNow(id);
      await refreshTaskList();
    } catch (err) {
      console.error("Failed to run automation", err);
      setError(err instanceof Error ? err.message : "立即执行失败");
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async (id: number) => {
    const automation = automations.find((a) => a.id === id);
    if (!automation) return;
    const confirmed = window.confirm(`确认删除自动化任务"${automation.name}"吗？`);
    if (!confirmed) return;
    try {
      setBusy(true);
      setError(null);
      await deleteAutomation(id);
      await refreshTaskList();
    } catch (err) {
      console.error("Failed to delete automation", err);
      setError(err instanceof Error ? err.message : "删除自动化失败");
    } finally {
      setBusy(false);
    }
  };

  const handleRefresh = () => {
    if (activeTab === "history") {
      void refreshHistory();
    } else {
      void refreshTaskList();
    }
  };

  if (loading) {
    return (
      <MainLayout headerTitle="自动化">
        <div className="admin-page">
          <div className="admin-frame">
            <div className="admin-card p-6 text-sm" style={{ color: "var(--text-secondary)" }}>
              正在加载自动化配置...
            </div>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout headerTitle="自动化">
      <div className="admin-page">
        <div className="admin-frame">
          <PageSection title="自动化">
            <SegmentedTabs tabs={TABS} activeKey={activeTab} onChange={setActiveTab} />
          </PageSection>

          {error ? (
            <div className="warning-banner px-4 py-3 text-sm" style={{ color: "var(--text-secondary)" }}>
              {error}
            </div>
          ) : null}

          {activeTab === "tasks" ? (
            <TaskListTab
              automations={automations}
              stats={stats}
              conversations={conversations}
              latestRuns={latestRuns}
              busy={busy}
              onCreate={handleCreate}
              onRefresh={handleRefresh}
              onToggle={handleToggle}
              onEdit={handleEdit}
              onRun={handleRun}
              onDelete={handleDelete}
            />
          ) : (
            <HistoryTab
              runs={historyRuns}
              loading={false}
              busy={busy}
              onRefresh={handleRefresh}
            />
          )}

          <AutomationFormModal
            open={modalOpen}
            automation={editingAutomation}
            conversations={conversations}
            onClose={() => setModalOpen(false)}
            onSave={handleSave}
          />
        </div>
      </div>
    </MainLayout>
  );
};

export default AutomationsPage;
