import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import type { ReactNode } from "react";
import type { Conversation, Message } from "../types";
import {
  getConversations,
  getMessages,
  createConversation,
  deleteConversation,
  renameConversation,
} from "../services/api";

interface AppContextType {
  conversations: Conversation[];
  currentConversationId: number | null;
  messages: Message[];
  isConfigured: boolean | null;
  sidebarCollapsed: boolean;
  loadConversations: () => Promise<void>;
  selectConversation: (id: number | null) => void;
  createNewConversation: (title?: string) => Promise<Conversation | null>;
  removeConversation: (id: number) => Promise<void>;
  renameConversationById: (id: number, title: string) => Promise<void>;
  loadMessages: (conversationId: number) => Promise<void>;
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  setIsConfigured: (value: boolean | null) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

const SIDEBAR_COLLAPSED_KEY = "sidebar-collapsed";

interface AppProviderProps {
  children: ReactNode;
}

/**
 * 全局应用状态Provider - 管理会话数据、消息和UI状态
 */
export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<
    number | null
  >(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConfigured, setIsConfigured] = useState<boolean | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
      return stored === "true";
    }
    return false;
  });

  /**
   * 加载会话列表
   */
  const loadConversations = useCallback(async () => {
    try {
      const data = await getConversations();
      setConversations(data);
    } catch (error) {
      console.error("Failed to load conversations:", error);
    }
  }, []);

  /**
   * 选择会话
   */
  const selectConversation = useCallback((id: number | null) => {
    setCurrentConversationId(id);
  }, []);

  /**
   * 加载消息列表
   */
  const loadMessages = useCallback(async (conversationId: number) => {
    try {
      const data = await getMessages(conversationId);
      setMessages(data);
    } catch (error) {
      console.error("Failed to load messages:", error);
    }
  }, []);

  /**
   * 创建新会话
   */
  const createNewConversation = useCallback(
    async (title: string = "新对话"): Promise<Conversation | null> => {
      try {
        const newConversation = await createConversation(title);
        setConversations((prev) => [newConversation, ...prev]);
        return newConversation;
      } catch (error) {
        console.error("Failed to create conversation:", error);
        return null;
      }
    },
    [],
  );

  /**
   * 删除会话
   */
  const removeConversation = useCallback(
    async (id: number): Promise<void> => {
      try {
        await deleteConversation(id);
        setConversations((prev) => prev.filter((c) => c.id !== id));
        if (currentConversationId === id) {
          setCurrentConversationId(null);
          setMessages([]);
        }
      } catch (error) {
        console.error("Failed to delete conversation:", error);
        throw error;
      }
    },
    [currentConversationId],
  );

  /**
   * 重命名会话
   */
  const renameConversationById = useCallback(
    async (id: number, title: string): Promise<void> => {
      try {
        const updated = await renameConversation(id, title);
        setConversations((prev) =>
          prev.map((c) =>
            c.id === id
              ? { ...c, title: updated.title, updated_at: updated.updated_at }
              : c,
          ),
        );
      } catch (error) {
        console.error("Failed to rename conversation:", error);
        throw error;
      }
    },
    [],
  );

  /**
   * 切换侧边栏折叠状态
   */
  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed((prev) => {
      const newValue = !prev;
      localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(newValue));
      return newValue;
    });
  }, []);

  /**
   * 设置侧边栏折叠状态
   */
  const setSidebarCollapsedWithStorage = useCallback((collapsed: boolean) => {
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(collapsed));
    setSidebarCollapsed(collapsed);
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    if (currentConversationId) {
      loadMessages(currentConversationId);
    } else {
      setMessages([]);
    }
  }, [currentConversationId, loadMessages]);

  return (
    <AppContext.Provider
      value={{
        conversations,
        currentConversationId,
        messages,
        isConfigured,
        sidebarCollapsed,
        loadConversations,
        selectConversation,
        createNewConversation,
        removeConversation,
        renameConversationById,
        loadMessages,
        setMessages,
        setIsConfigured,
        toggleSidebar,
        setSidebarCollapsed: setSidebarCollapsedWithStorage,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

/**
 * 使用应用上下文的Hook
 */
export const useApp = (): AppContextType => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
};
