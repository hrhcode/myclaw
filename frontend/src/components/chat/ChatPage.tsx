import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle } from "lucide-react";
import MainLayout from "../layout/MainLayout";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import ThemeToggle from "../common/ThemeToggle";
import ConversationSelect from "../common/ConversationSelect";
import { useApp } from "../../contexts/AppContext";
import { sendMessageStream, getConfig } from "../../services/api";
import type { Message, ToolCallInfo, ToolResultInfo } from "../../types";

/**
 * 聊天页面组件 - 主聊天界面
 */
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
  const [initialLoaded, setInitialLoaded] = useState(false);

  useEffect(() => {
    checkConfiguration();
    loadConversations();
  }, []);

  useEffect(() => {
    if (!initialLoaded || conversations.length === 0) {
      setInitialLoaded(true);
      return;
    }

    if (conversationId) {
      const id = parseInt(conversationId, 10);
      if (!isNaN(id) && id !== currentConversationId) {
        selectConversation(id);
      }
    } else if (currentConversationId === null) {
      const sortedConversations = [...conversations].sort(
        (a, b) =>
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
      );
      if (sortedConversations.length > 0) {
        const mostRecent = sortedConversations[0];
        selectConversation(mostRecent.id);
        navigate(`/chat/${mostRecent.id}`, { replace: true });
      }
    }
  }, [
    conversationId,
    selectConversation,
    conversations,
    navigate,
    initialLoaded,
    currentConversationId,
  ]);

  /**
   * 检查配置状态
   */
  const checkConfiguration = async () => {
    try {
      await getConfig("zhipu_api_key");
      setIsConfigured(true);
    } catch {
      setIsConfigured(false);
    }
  };

  /**
   * 创建新会话
   */
  const handleCreateNewChat = async () => {
    const newConversation = await createNewConversation("新对话");
    if (newConversation) {
      selectConversation(newConversation.id);
      navigate(`/chat/${newConversation.id}`, { replace: true });
    }
  };

  /**
   * 处理发送消息或命令
   */
  const handleSendMessage = async (content: string) => {
    const trimmedContent = content.trim();

    if (trimmedContent === "/new") {
      await handleCreateNewChat();
      return;
    }

    if (isConfigured === false) {
      alert("请先在配置页面配置API Key");
      navigate("/settings");
      return;
    }

    setIsSending(true);

    let conversationIdToUse = currentConversationId;

    if (!conversationIdToUse) {
      const newConversation = await createNewConversation(
        trimmedContent.substring(0, 20) + "...",
      );
      if (newConversation) {
        conversationIdToUse = newConversation.id;
        selectConversation(newConversation.id);
        navigate(`/chat/${newConversation.id}`, { replace: true });
      } else {
        setIsSending(false);
        return;
      }
    }

    const userMessage: Message = {
      id: Date.now(),
      conversation_id: conversationIdToUse,
      role: "user",
      content: trimmedContent,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    const tempAiMessage: Message = {
      id: Date.now() + 1,
      conversation_id: conversationIdToUse,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
      toolCalls: [],
      toolResults: new Map(),
    };
    setMessages((prev) => [...prev, tempAiMessage]);

    try {
      await sendMessageStream(
        {
          conversation_id: conversationIdToUse,
          message: trimmedContent,
        },
        (chunk) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === tempAiMessage.id
                ? { ...msg, content: msg.content + chunk }
                : msg,
            ),
          );
        },
        () => {
          loadConversations();
        },
        (error) => {
          console.error("Chat error:", error);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === tempAiMessage.id
                ? { ...msg, content: "发送失败，请检查是否已配置API Key" }
                : msg,
            ),
          );
        },
        (toolName, toolCallId, argumentsStr) => {
          setMessages((prev) =>
            prev.map((msg) => {
              if (msg.id === tempAiMessage.id) {
                const newToolCall: ToolCallInfo = {
                  toolName,
                  toolCallId,
                  arguments: argumentsStr,
                };
                return {
                  ...msg,
                  toolCalls: [...(msg.toolCalls || []), newToolCall],
                };
              }
              return msg;
            }),
          );
        },
        (toolCallId, content) => {
          setMessages((prev) =>
            prev.map((msg) => {
              if (msg.id === tempAiMessage.id) {
                const newResults = new Map(msg.toolResults || new Map());
                newResults.set(toolCallId, { toolCallId, content });
                return {
                  ...msg,
                  toolResults: newResults,
                };
              }
              return msg;
            }),
          );
        },
      );
    } catch (error) {
      console.error("Failed to send message:", error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === tempAiMessage.id
            ? { ...msg, content: "发送失败，请检查是否已配置API Key" }
            : msg,
        ),
      );
    } finally {
      setIsSending(false);
    }
  };

  return (
    <MainLayout showHeader={false}>
      <div className="h-full flex flex-col">
        <header className="navbar h-16 flex items-center justify-between px-6 relative z-50">
          <div className="flex items-center gap-3">
            <ConversationSelect />
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />
          </div>
        </header>

        <AnimatePresence>
          {isConfigured === false && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="px-6 py-4"
            >
              <div className="warning-banner p-4 flex items-center gap-3">
                <AlertTriangle
                  size={20}
                  className="text-yellow-500 flex-shrink-0"
                />
                <p className="text-yellow-700 dark:text-yellow-200/90 text-sm">
                  请先配置API Key才能使用聊天功能。{" "}
                  <Link to="/settings" className="underline font-semibold">
                    去配置
                  </Link>
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <MessageList messages={messages} />
        <MessageInput
          onSendMessage={handleSendMessage}
          disabled={isSending}
          onCreateNewChat={handleCreateNewChat}
        />
      </div>
    </MainLayout>
  );
};

export default ChatPage;
