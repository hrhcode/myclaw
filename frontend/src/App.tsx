import { useState, useEffect, useRef } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  useNavigate,
} from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Settings, Sparkles, AlertTriangle, Sun, Moon } from "lucide-react";
import { ThemeProvider, useTheme } from "./contexts/ThemeContext";
import ConversationList from "./components/ConversationList";
import MessageList from "./components/MessageList";
import MessageInput from "./components/MessageInput";
import SettingsPage from "./components/Settings";
import type { Conversation, Message } from "./types";
import {
  sendMessageStream,
  getConversations,
  createConversation,
  deleteConversation,
  getMessages,
  getConfig,
} from "./services/api";
import "./App.css";

/**
 * 主题切换按钮组件
 */
const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <motion.button
      onClick={toggleTheme}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className="flex items-center gap-2 px-4 py-2.5 rounded-xl glass transition-colors"
      style={{ color: "var(--text-secondary)" }}
      onMouseEnter={(e) =>
        (e.currentTarget.style.color = "var(--text-primary)")
      }
      onMouseLeave={(e) =>
        (e.currentTarget.style.color = "var(--text-secondary)")
      }
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
    >
      <AnimatePresence mode="wait">
        {theme === "dark" ? (
          <motion.div
            key="moon"
            initial={{ rotate: -90, opacity: 0 }}
            animate={{ rotate: 0, opacity: 1 }}
            exit={{ rotate: 90, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <Moon size={18} />
          </motion.div>
        ) : (
          <motion.div
            key="sun"
            initial={{ rotate: 90, opacity: 0 }}
            animate={{ rotate: 0, opacity: 1 }}
            exit={{ rotate: -90, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <Sun size={18} />
          </motion.div>
        )}
      </AnimatePresence>
      <span className="text-sm font-medium">
        {theme === "dark" ? "深色" : "浅色"}
      </span>
    </motion.button>
  );
};

/**
 * 聊天页面组件 - 主聊天界面
 */
const ChatPage: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<
    number | null
  >(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isConfigured, setIsConfigured] = useState<boolean | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

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
    if (currentConversationId) {
      loadMessages(currentConversationId);
    } else {
      setMessages([]);
    }
  }, [currentConversationId]);

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
   * 加载会话列表
   */
  const loadConversations = async () => {
    try {
      const data = await getConversations();
      setConversations(data);
    } catch (error) {
      console.error("Failed to load conversations:", error);
    }
  };

  /**
   * 加载消息列表
   */
  const loadMessages = async (conversationId: number) => {
    try {
      const data = await getMessages(conversationId);
      setMessages(data);
    } catch (error) {
      console.error("Failed to load messages:", error);
    }
  };

  /**
   * 创建新会话
   */
  const handleCreateConversation = async () => {
    try {
      const newConversation = await createConversation("新对话");
      setConversations([newConversation, ...conversations]);
      setCurrentConversationId(newConversation.id);
    } catch (error) {
      console.error("Failed to create conversation:", error);
    }
  };

  /**
   * 删除会话
   */
  const handleDeleteConversation = async (id: number) => {
    try {
      await deleteConversation(id);
      setConversations(conversations.filter((c) => c.id !== id));
      if (currentConversationId === id) {
        setCurrentConversationId(null);
        setMessages([]);
      }
    } catch (error) {
      console.error("Failed to delete conversation:", error);
    }
  };

  /**
   * 发送消息
   */
  const handleSendMessage = async (content: string) => {
    if (isConfigured === false) {
      alert("请先在设置页面配置API Key");
      navigate("/settings");
      return;
    }

    setIsLoading(true);

    let conversationId = currentConversationId;
    if (!conversationId) {
      try {
        const newConversation = await createConversation(
          content.substring(0, 20) + "...",
        );
        setConversations([newConversation, ...conversations]);
        conversationId = newConversation.id;
        setCurrentConversationId(conversationId);
      } catch (error) {
        console.error("Failed to create conversation:", error);
        setIsLoading(false);
        return;
      }
    }

    const userMessage: Message = {
      id: Date.now(),
      conversation_id: conversationId,
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    const tempAiMessage: Message = {
      id: Date.now() + 1,
      conversation_id: conversationId,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempAiMessage]);

    try {
      await sendMessageStream(
        {
          conversation_id: conversationId,
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
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container flex h-screen">
      <div className="app-bg-glow" />

      <ConversationList
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={setCurrentConversationId}
        onCreateConversation={handleCreateConversation}
        onDeleteConversation={handleDeleteConversation}
      />

      <div className="main-content flex-1 flex flex-col">
        <motion.header
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="navbar h-16 flex items-center justify-between px-6"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-primary-dark flex items-center justify-center">
              <Sparkles size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-[var(--text-primary)]">
                AI对话助手
              </h1>
              <p className="text-xs text-[var(--text-muted)]">
                智能对话，无限可能
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link
                to="/settings"
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl glass transition-colors"
                style={{ color: "var(--text-secondary)" }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.color = "var(--text-primary)")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.color = "var(--text-secondary)")
                }
              >
                <Settings size={18} />
                <span className="text-sm font-medium">设置</span>
              </Link>
            </motion.div>
          </div>
        </motion.header>

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
                    去设置
                  </Link>
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <MessageList messages={messages} />
        <div ref={messagesEndRef} />
        <MessageInput onSendMessage={handleSendMessage} disabled={isLoading} />
      </div>
    </div>
  );
};

/**
 * 主应用组件
 */
const App: React.FC = () => {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;
