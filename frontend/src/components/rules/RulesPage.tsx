import { useEffect, useMemo, useState } from "react";
import { Loader2, Save } from "lucide-react";

import MainLayout from "../layout/MainLayout";
import { SectionCard } from "../admin";
import { useApp } from "../../contexts/AppContext";
import {
  getConversationRule,
  getGlobalRule,
  updateConversationRule,
  updateGlobalRule,
} from "../../services/api";

const RulesPage: React.FC = () => {
  const { conversations, currentConversationId, loadConversations } = useApp();
  const [selectedConversationId, setSelectedConversationId] = useState<
    number | null
  >(null);
  const [globalRule, setGlobalRule] = useState("");
  const [conversationRule, setConversationRule] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingGlobal, setIsSavingGlobal] = useState(false);
  const [isSavingConversation, setIsSavingConversation] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    if (currentConversationId) {
      setSelectedConversationId(currentConversationId);
      return;
    }
    if (!selectedConversationId && conversations.length > 0) {
      setSelectedConversationId(conversations[0].id);
    }
  }, [conversations, currentConversationId]);

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        const global = await getGlobalRule();
        setGlobalRule(global.rule || "");
      } catch (error) {
        console.error("Failed to load global rule:", error);
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, []);

  useEffect(() => {
    if (!selectedConversationId) {
      setConversationRule("");
      return;
    }

    const load = async () => {
      try {
        const response = await getConversationRule(selectedConversationId);
        setConversationRule(response.rule || "");
      } catch (error) {
        console.error("Failed to load conversation rule:", error);
        setConversationRule("");
      }
    };

    void load();
  }, [selectedConversationId]);

  const selectedConversation = useMemo(
    () =>
      conversations.find((item) => item.id === selectedConversationId) || null,
    [conversations, selectedConversationId],
  );

  const showNotice = (message: string) => {
    setNotice(message);
    window.setTimeout(() => {
      setNotice((current) => (current === message ? null : current));
    }, 2400);
  };

  const handleSaveGlobalRule = async () => {
    try {
      setIsSavingGlobal(true);
      const response = await updateGlobalRule(globalRule);
      setGlobalRule(response.rule);
      showNotice("全局规则已保存");
    } catch (error) {
      console.error("Failed to save global rule:", error);
      showNotice("全局规则保存失败");
    } finally {
      setIsSavingGlobal(false);
    }
  };

  const handleSaveConversationRule = async () => {
    if (!selectedConversationId) {
      return;
    }

    try {
      setIsSavingConversation(true);
      const response = await updateConversationRule(
        selectedConversationId,
        conversationRule,
      );
      setConversationRule(response.rule);
      showNotice("会话规则已保存");
      await loadConversations();
    } catch (error) {
      console.error("Failed to save conversation rule:", error);
      showNotice("会话规则保存失败");
    } finally {
      setIsSavingConversation(false);
    }
  };

  if (isLoading) {
    return (
      <MainLayout
        headerTitle="规则"
        headerSubtitle="用强约束规则统一限制模型输出和行为"
      >
        <div className="flex h-full items-center justify-center py-16">
          <Loader2 size={40} className="animate-spin text-primary" />
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout
      headerTitle="规则"
      headerSubtitle="规则会在myclaw生成回复前以系统提示词注入，属于强制生效的行为约束。"
    >
      <div className="admin-page">
        <div className="admin-frame rules-page">
          {notice ? <div className="callout mb-4">{notice}</div> : null}

          <div className="rules-grid">
            <SectionCard className="rules-card">
              <div className="rules-card__header">
                <div>
                  <h2 className="rules-card__title">全局规则</h2>
                  <p className="rules-card__desc">
                    适合放长期稳定的约束，比如回复语言、事实严谨度、代码修改方式、风险提示要求。
                  </p>
                </div>
              </div>

              <textarea
                className="admin-input rules-editor"
                value={globalRule}
                onChange={(event) => setGlobalRule(event.target.value)}
                placeholder={
                  "例如：\n1. 始终使用中文回答。\n2. 不确定的事实必须明确说明不确定。\n3. 涉及代码改动时优先直接落地实现，不给空泛建议。"
                }
              />

              <div className="rules-card__footer">
                <div className="rules-hint">
                  建议用分条短句描述，便于长期维护。
                </div>
                <button
                  type="button"
                  className="btn rules-save-btn"
                  onClick={() => void handleSaveGlobalRule()}
                  disabled={isSavingGlobal}
                >
                  {isSavingGlobal ? (
                    <Loader2 size={20} className="animate-spin" />
                  ) : (
                    <Save size={20} />
                  )}
                  <span>保存全局规则</span>
                </button>
              </div>
            </SectionCard>

            <SectionCard className="rules-card">
              <div className="rules-card__header">
                <div>
                  <h2 className="rules-card__title">会话规则</h2>
                  <p className="rules-card__desc">
                    适合放当前这次协作的临时约束。
                  </p>
                </div>
                <select
                  className="admin-select px-3 py-2 min-w-[180px]"
                  value={selectedConversationId ?? ""}
                  onChange={(event) =>
                    setSelectedConversationId(Number(event.target.value))
                  }
                >
                  {conversations.map((conversation) => (
                    <option key={conversation.id} value={conversation.id}>
                      {conversation.title || `会话 ${conversation.id}`}
                    </option>
                  ))}
                </select>
              </div>

              <textarea
                className="admin-input rules-editor"
                value={conversationRule}
                onChange={(event) => setConversationRule(event.target.value)}
                disabled={!selectedConversation}
                placeholder={
                  "例如：\n1. 本轮对话中你扮演严格的前端架构师。\n2. 回复先给结论，再给最小可执行改动。\n3. 未经确认不要主动修改数据库结构。"
                }
              />

              <div className="rules-card__footer">
                <div className="rules-hint">
                  {selectedConversation
                    ? `当前规则将强制作用于「${selectedConversation.title || `会话 ${selectedConversation.id}`}」`
                    : "暂无可配置的会话"}
                </div>
                <button
                  type="button"
                  className="btn rules-save-btn"
                  onClick={() => void handleSaveConversationRule()}
                  disabled={!selectedConversation || isSavingConversation}
                >
                  {isSavingConversation ? (
                    <Loader2 size={20} className="animate-spin" />
                  ) : (
                    <Save size={20} />
                  )}
                  <span>保存会话规则</span>
                </button>
              </div>
            </SectionCard>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default RulesPage;
