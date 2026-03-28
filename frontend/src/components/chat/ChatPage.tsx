import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Plus } from "lucide-react";
import MainLayout from "../layout/MainLayout";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import ThemeToggle from "../common/ThemeToggle";
import { useApp } from "../../contexts/AppContext";
import { sendMessageStream, getConfig } from "../../services/api";
import type { Message } from "../../types";

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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  /**
   * 滚动到底部
   */
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
   * 发送消息
   */
  const handleSendMessage = async (content: string) => {
    if (isConfigured === false) {
      alert("请先在配置页面配置API Key");
      navigate("/settings");
      return;
    }

    setIsSending(true);

    let conversationIdToUse = currentConversationId;

    if (!conversationIdToUse) {
      const newConversation = await createNewConversation(
        content.substring(0, 20) + "...",
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
      content,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    const tempAiMessage: Message = {
      id: Date.now() + 1,
      conversation_id: conversationIdToUse,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempAiMessage]);

    try {
      await sendMessageStream(
        {
          conversation_id: conversationIdToUse,
          message: content,
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

  return (
    <MainLayout showHeader={false}>
      <div className="h-full flex flex-col">
        <header className="navbar h-16 flex items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleCreateNewChat}
              className="btn-primary flex items-center gap-2"
            >
              <Plus size={16} />
              <span>新对话</span>
            </motion.button>
            {currentConversationId && (
              <h2
                className="text-lg font-semibold truncate max-w-[300px]"
                style={{ color: "var(--text-primary)" }}
              >
                {conversations.find((c) => c.id === currentConversationId)
                  ?.title || "新对话"}
              </h2>
            )}
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
        <div ref={messagesEndRef} />
        <MessageInput onSendMessage={handleSendMessage} disabled={isSending} />
      </div>
    </MainLayout>
  );
};

export default ChatPage;
