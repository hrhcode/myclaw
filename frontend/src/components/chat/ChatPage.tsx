import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { AlertTriangle } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { createPortal } from "react-dom";

import type {
  AgentTraceEvent,
  AgentTraceEventPayload,
  AgentTraceEventType,
  Message,
} from "../../types";
import { useApp } from "../../contexts/AppContext";
import { getAgentRunByRunId, getConfig, saveMessageToKnowledge, sendMessageStream } from "../../services/api";
import MainLayout from "../layout/MainLayout";
import MessageInput from "./MessageInput";
import type { MessageInputHandle } from "./MessageInput";
import MessageList from "./MessageList";

const buildTraceEvent = (
  type: AgentTraceEventType,
  payload: AgentTraceEventPayload,
): AgentTraceEvent => ({
  id: `${type}-${payload.tool_call_id || payload.iteration || Date.now()}-${Math.random()
    .toString(36)
    .slice(2, 8)}`,
  type,
  createdAt: new Date().toISOString(),
  payload,
});

const appendTraceEvent = (
  previousEvents: AgentTraceEvent[] = [],
  type: AgentTraceEventType,
  payload: AgentTraceEventPayload,
): AgentTraceEvent[] => {
  if (type === "reasoning" && previousEvents.length > 0) {
    const lastEvent = previousEvents[previousEvents.length - 1];
    if (lastEvent.type === "reasoning") {
      return [
        ...previousEvents.slice(0, -1),
        {
          ...lastEvent,
          payload: {
            ...lastEvent.payload,
            ...payload,
            content: `${lastEvent.payload.content || ""}${payload.content || ""}`,
          },
        },
      ];
    }
  }

  return [...previousEvents, buildTraceEvent(type, payload)];
};

const ChatPage: React.FC = () => {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const {
    conversations,
    currentConversationId,
    messages,
    isConfigured,
    selectConversation,
    createNewConversation,
    setMessages,
    setIsConfigured,
    loadConversations,
  } = useApp();

  const [isSending, setIsSending] = useState(false);
  const [savingKnowledgeMessageId, setSavingKnowledgeMessageId] = useState<number | null>(null);
  const [notice, setNotice] = useState<{ message: string; type: "success" | "error" } | null>(null);
  const [rollbackConfirmMessage, setRollbackConfirmMessage] = useState<Message | null>(null);
  const [highlightMessageId, setHighlightMessageId] = useState<number | null>(null);
  const chunkBufferRef = useRef("");
  const flushTimerRef = useRef<number | null>(null);
  const messageInputRef = useRef<MessageInputHandle>(null);

  useEffect(() => {
    void checkConfiguration();
    void loadConversations();
  }, [loadConversations]);

  // 处理 ?highlight=run_id 参数：通过 API 查找 message_id
  useEffect(() => {
    const runId = searchParams.get("highlight");
    if (!runId) return;
    // 清除 URL 参数避免刷新时重复触发
    navigate(window.location.pathname, { replace: true });
    let cancelled = false;
    getAgentRunByRunId(runId)
      .then((info) => {
        if (!cancelled && info.message_id) {
          setHighlightMessageId(info.message_id);
        }
      })
      .catch(() => {
        // 静默失败
      });
    return () => { cancelled = true; };
  }, [searchParams, navigate]);

  useEffect(() => {
    if (!conversationId) {
      return;
    }
    const id = Number.parseInt(conversationId, 10);
    if (!Number.isNaN(id) && id !== currentConversationId) {
      selectConversation(id);
    }
  }, [conversationId, currentConversationId, selectConversation]);

  useEffect(() => {
    if (currentConversationId || conversations.length === 0) {
      return;
    }
    const mostRecent = [...conversations].sort(
      (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
    )[0];
    if (!mostRecent) {
      return;
    }
    selectConversation(mostRecent.id);
    navigate(`/chat/${mostRecent.id}`, { replace: true });
  }, [conversations, currentConversationId, navigate, selectConversation]);

  useEffect(() => {
    return () => {
      if (flushTimerRef.current !== null) {
        window.clearTimeout(flushTimerRef.current);
      }
    };
  }, []);

  const checkConfiguration = async () => {
    try {
      await getConfig("zhipu_api_key");
      setIsConfigured(true);
    } catch {
      setIsConfigured(false);
    }
  };

  const handleCreateNewChat = async () => {
    const newConversation = await createNewConversation("新会话");
    if (!newConversation) {
      return;
    }
    selectConversation(newConversation.id);
    navigate(`/chat/${newConversation.id}`, { replace: true });
  };

  const updateStreamingMessage = (
    tempMessageId: number,
    updater: (message: Message) => Message,
  ) => {
    setMessages((previous) =>
      previous.map((message) => (message.id === tempMessageId ? updater(message) : message)),
    );
  };

  const showNotice = (message: string, type: "success" | "error" = "success") => {
    const noticeObj = { message, type };
    setNotice(noticeObj);
    window.setTimeout(() => {
      setNotice((previous) => (previous === noticeObj ? null : previous));
    }, 2500);
  };

  const flushBufferedChunk = (tempMessageId: number) => {
    if (!chunkBufferRef.current) {
      return;
    }
    const content = chunkBufferRef.current;
    chunkBufferRef.current = "";
    updateStreamingMessage(tempMessageId, (message) => ({
      ...message,
      content: message.content + content,
    }));
  };

  const scheduleChunkFlush = (tempMessageId: number) => {
    if (flushTimerRef.current !== null) {
      return;
    }
    flushTimerRef.current = window.setTimeout(() => {
      flushTimerRef.current = null;
      flushBufferedChunk(tempMessageId);
    }, 50);
  };

  const handleSendMessage = async (content: string) => {
    const trimmedContent = content.trim();
    const isChatCommand = trimmedContent.startsWith("/");

    if (trimmedContent === "/new") {
      await handleCreateNewChat();
      return;
    }

    if (isConfigured === false && !isChatCommand) {
      showNotice("请先完成接口密钥配置。", "error");
      navigate("/settings");
      return;
    }

    if (!currentConversationId) {
      showNotice("会话仍在加载中。", "error");
      return;
    }

    setIsSending(true);

    const now = new Date().toISOString();
    const tempAssistantMessage: Message = {
      id: Date.now() + 1,
      conversation_id: currentConversationId,
      role: "assistant",
      content: "",
      created_at: now,
      traceEvents: [],
      isStreaming: true,
    };

    setMessages((previous) => [
      ...previous,
      {
        id: Date.now(),
        conversation_id: currentConversationId,
        role: "user",
        content: trimmedContent,
        created_at: now,
      },
      tempAssistantMessage,
    ]);

    try {
      await sendMessageStream(
        {
          conversation_id: currentConversationId,
          message: trimmedContent,
        },
        {
          onChunk: (chunk) => {
            chunkBufferRef.current += chunk;
            scheduleChunkFlush(tempAssistantMessage.id);
          },
          onConversation: (nextConversationId, runId) => {
            updateStreamingMessage(tempAssistantMessage.id, (message) => ({
              ...message,
              conversation_id: nextConversationId,
              runId,
            }));

            if (nextConversationId !== currentConversationId) {
              selectConversation(nextConversationId);
              navigate(`/chat/${nextConversationId}`, { replace: true });
            }
          },
          onTraceEvent: (type, payload) => {
            updateStreamingMessage(tempAssistantMessage.id, (message) => ({
              ...message,
              runId: payload.run_id || message.runId,
              traceEvents: appendTraceEvent(message.traceEvents, type, payload),
            }));
          },
          onComplete: (_message, streamedConversationId) => {
            if (flushTimerRef.current !== null) {
              window.clearTimeout(flushTimerRef.current);
              flushTimerRef.current = null;
            }
            flushBufferedChunk(tempAssistantMessage.id);
            updateStreamingMessage(tempAssistantMessage.id, (message) => ({
              ...message,
              conversation_id: streamedConversationId,
              isStreaming: false,
            }));
            void loadConversations();
          },
          onError: (error) => {
            if (flushTimerRef.current !== null) {
              window.clearTimeout(flushTimerRef.current);
              flushTimerRef.current = null;
            }
            flushBufferedChunk(tempAssistantMessage.id);
            updateStreamingMessage(tempAssistantMessage.id, (message) => ({
              ...message,
              content: message.content || "消息发送失败，请检查接口密钥和工具配置。",
              traceEvents: appendTraceEvent(message.traceEvents, "loop_warning", {
                message: error.message,
                severity: "error",
              }),
              isStreaming: false,
            }));
            showNotice("消息发送失败。", "error");
          },
        },
      );
    } catch (error) {
      if (flushTimerRef.current !== null) {
        window.clearTimeout(flushTimerRef.current);
        flushTimerRef.current = null;
      }
      flushBufferedChunk(tempAssistantMessage.id);
      console.error("Failed to send message:", error);
      updateStreamingMessage(tempAssistantMessage.id, (message) => ({
        ...message,
        content: "消息发送失败，请检查接口密钥和工具配置。",
        isStreaming: false,
      }));
      showNotice("消息发送失败。", "error");
    } finally {
      setIsSending(false);
    }
  };

  const handleSaveAssistantMessage = async (message: Message) => {
    try {
      setSavingKnowledgeMessageId(message.id);
      await saveMessageToKnowledge(message.id);
      showNotice("已保存到知识库");
    } catch (error) {
      console.error("Failed to save assistant message to knowledge base:", error);
      showNotice("保存到知识库失败", "error");
    } finally {
      setSavingKnowledgeMessageId(null);
    }
  };

  const handleCopyMessage = async (message: Message) => {
    await navigator.clipboard.writeText(message.content);
    showNotice("已复制到剪贴板");
  };

  const handleRollbackClick = (message: Message) => {
    setRollbackConfirmMessage(message);
  };

  const handleRollbackConfirm = () => {
    const msg = rollbackConfirmMessage;
    if (!msg) return;
    const index = messages.findIndex((m) => m.id === msg.id);
    if (index === -1) {
      setRollbackConfirmMessage(null);
      return;
    }
    const rolledBackContent = msg.content;
    setMessages((previous) => previous.slice(0, index));
    if (messageInputRef.current?.isEmpty()) {
      messageInputRef.current.setMessage(rolledBackContent);
    }
    setRollbackConfirmMessage(null);
  };

  const handleRollbackCancel = () => {
    setRollbackConfirmMessage(null);
  };

  const handleRegenerate = (message: Message) => {
    if (isSending) return;

    const messageIndex = messages.findIndex((m) => m.id === message.id);
    if (messageIndex <= 0) return;

    const userMessage = messages[messageIndex - 1];
    if (userMessage.role !== "user") return;

    const userContent = userMessage.content;

    setMessages((previous) =>
      previous.filter((m) => m.id !== message.id && m.id !== userMessage.id),
    );

    void handleSendMessage(userContent);
  };

  return (
    <MainLayout
      contentClassName="content--chat"
    >
      <AnimatePresence>
        {notice ? (
          <motion.div
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.2 }}
            className={`toast-notice ${notice.type === "error" ? "toast-notice--error" : "toast-notice--success"}`}
          >
            {notice.message}
          </motion.div>
        ) : null}
      </AnimatePresence>

      <section className="card chat">
        {isConfigured === false ? (
          <div className="callout danger">
            <div className="row">
              <AlertTriangle size={20} />
              <span>
                尚未配置接口密钥。<Link to="/settings">前往设置</Link>
              </span>
            </div>
          </div>
        ) : null}

        <MessageList
          messages={messages}
          onCopyMessage={handleCopyMessage}
          onRegenerateMessage={handleRegenerate}
          onSaveAssistantMessage={handleSaveAssistantMessage}
          savingMessageId={savingKnowledgeMessageId}
          onRollbackMessage={handleRollbackClick}
          highlightMessageId={highlightMessageId}
        />
        <MessageInput
          ref={messageInputRef}
          onSendMessage={handleSendMessage}
          disabled={isSending}
          onCreateNewChat={handleCreateNewChat}
        />
      </section>

      {rollbackConfirmMessage
        ? createPortal(
            <div className="rollback-overlay" onClick={handleRollbackCancel}>
              <div className="rollback-dialog" onClick={(e) => e.stopPropagation()}>
                <p>当前操作不可逆，是否确认回滚？</p>
                <div className="rollback-dialog-actions">
                  <button type="button" onClick={handleRollbackCancel}>取消</button>
                  <button type="button" className="is-confirm" onClick={handleRollbackConfirm}>确认</button>
                </div>
              </div>
            </div>,
            document.body,
          )
        : null}
    </MainLayout>
  );
};

export default ChatPage;
