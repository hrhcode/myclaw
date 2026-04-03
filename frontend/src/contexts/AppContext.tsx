import {
  createContext,
  useContext,
  useEffect,
  useCallback,
  useState,
} from "react";
import type { ReactNode } from "react";

import type {
  AgentEventFromDB,
  AgentTraceEvent,
  AgentTraceEventPayload,
  AgentTraceEventType,
  Conversation,
  Message,
} from "../types";
import {
  createConversation,
  deleteConversation,
  getConversations,
  getMessages,
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

const parseAgentPayload = (payload: string): AgentTraceEventPayload => {
  try {
    return JSON.parse(payload) as AgentTraceEventPayload;
  } catch {
    return { content: payload };
  }
};

const mapAgentEvents = (events?: AgentEventFromDB[]): AgentTraceEvent[] =>
  (events || []).map((event) => ({
    id: `db-${event.id}`,
    type: event.event_type as AgentTraceEventType,
    createdAt: event.created_at,
    payload: parseAgentPayload(event.payload),
  }));

export const AppProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<
    number | null
  >(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConfigured, setIsConfigured] = useState<boolean | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(
    () => localStorage.getItem("sidebar_collapsed") === "true",
  );

  const loadConversations = useCallback(async () => {
    try {
      const data = await getConversations();
      setConversations(data);
      setCurrentConversationId((prev) => {
        if (prev && data.some((item) => item.id === prev)) {
          return prev;
        }
        return data[0]?.id ?? null;
      });
    } catch (error) {
      console.error("Failed to load conversations:", error);
    }
  }, []);

  const loadMessages = useCallback(async (conversationId: number) => {
    try {
      const data = await getMessages(conversationId);
      setMessages(
        data.map((message) => ({
          ...message,
          traceEvents: mapAgentEvents(message.agent_events),
          runId: message.agent_events?.[0]?.run_id,
        })),
      );
    } catch (error) {
      console.error("Failed to load messages:", error);
    }
  }, []);

  const selectConversation = useCallback((id: number | null) => {
    setCurrentConversationId(id);
  }, []);

  const createNewConversation = useCallback(
    async (title = "新会话"): Promise<Conversation | null> => {
      try {
        const conversation = await createConversation(title);
        setConversations((prev) => [conversation, ...prev]);
        setCurrentConversationId(conversation.id);
        return conversation;
      } catch (error) {
        console.error("Failed to create conversation:", error);
        return null;
      }
    },
    [],
  );

  const removeConversation = useCallback(
    async (id: number) => {
      await deleteConversation(id);
      setConversations((prev) =>
        prev.filter((conversation) => conversation.id !== id),
      );
      if (currentConversationId === id) {
        setCurrentConversationId(null);
        setMessages([]);
      }
    },
    [currentConversationId],
  );

  const renameConversationById = useCallback(
    async (id: number, title: string) => {
      const updated = await renameConversation(id, title);
      setConversations((prev) =>
        prev.map((conversation) =>
          conversation.id === id
            ? {
                ...conversation,
                title: updated.title,
                updated_at: updated.updated_at,
              }
            : conversation,
        ),
      );
    },
    [],
  );

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem("sidebar_collapsed", String(next));
      return next;
    });
  }, []);

  const setSidebarCollapsedWithStorage = useCallback((collapsed: boolean) => {
    localStorage.setItem("sidebar_collapsed", String(collapsed));
    setSidebarCollapsed(collapsed);
  }, []);

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    if (currentConversationId) {
      void loadMessages(currentConversationId);
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

export const useApp = (): AppContextType => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
};
