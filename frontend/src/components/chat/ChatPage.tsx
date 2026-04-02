import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AlertTriangle, History, Plus, RefreshCw } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

import type {
  AgentTraceEvent,
  AgentTraceEventPayload,
  AgentTraceEventType,
  Message,
} from "../../types";
import { useApp } from "../../contexts/AppContext";
import { getConfig, sendMessageStream } from "../../services/api";
import MainLayout from "../layout/MainLayout";
import MessageInput from "./MessageInput";
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
  const [notice, setNotice] = useState<string | null>(null);
  const chunkBufferRef = useRef("");
  const flushTimerRef = useRef<number | null>(null);

  useEffect(() => {
    void checkConfiguration();
    void loadConversations();
  }, [loadConversations]);

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

  const showNotice = (message: string) => {
    setNotice(message);
    window.setTimeout(() => {
      setNotice((previous) => (previous === message ? null : previous));
    }, 3000);
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
      showNotice("请先完成接口密钥配置。");
      navigate("/settings");
      return;
    }

    if (!currentConversationId) {
      showNotice("会话仍在加载中。");
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
            showNotice("消息发送失败。");
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
      showNotice("消息发送失败。");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <MainLayout
      headerTitle="对话"
      headerSubtitle="围绕当前会话持续推进任务，并实时查看执行轨迹。"
      contentClassName="content--chat"
      headerActions={
        <div className="chat-controls">
          <button
            className="btn btn--icon"
            onClick={() => void loadConversations()}
            title="刷新会话列表"
            aria-label="刷新会话列表"
          >
            <RefreshCw size={16} />
          </button>
          <Link
            className="btn btn--icon"
            to="/conversations"
            title="查看会话列表"
            aria-label="查看会话列表"
          >
            <History size={16} />
          </Link>
          <button
            className="btn btn--icon"
            onClick={() => void handleCreateNewChat()}
            title="新建会话"
            aria-label="新建会话"
          >
            <Plus size={16} />
          </button>
        </div>
      }
    >
      <section className="card chat">
        <AnimatePresence>
          {notice ? (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="callout danger"
            >
              {notice}
            </motion.div>
          ) : null}
        </AnimatePresence>

        {isConfigured === false ? (
          <div className="callout danger">
            <div className="row">
              <AlertTriangle size={16} />
              <span>
                尚未配置接口密钥。<Link to="/settings">前往设置</Link>
              </span>
            </div>
          </div>
        ) : null}

        <MessageList messages={messages} />
        <MessageInput
          onSendMessage={handleSendMessage}
          disabled={isSending}
          onCreateNewChat={handleCreateNewChat}
        />
      </section>
    </MainLayout>
  );
};

export default ChatPage;
