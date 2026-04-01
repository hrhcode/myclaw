import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from 'react';
import type { ReactNode } from 'react';
import type {
  AgentEventFromDB,
  AgentTraceEvent,
  AgentTraceEventPayload,
  AgentTraceEventType,
  Conversation,
  Message,
} from '../types';
import {
  getConversations,
  getMessages,
  createConversation,
  deleteConversation,
  renameConversation,
} from '../services/api';

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

interface AppProviderProps {
  children: ReactNode;
}

const parseAgentPayload = (payload: string): AgentTraceEventPayload => {
  try {
    return JSON.parse(payload) as AgentTraceEventPayload;
  } catch {
    return { content: payload };
  }
};

const mapAgentEvents = (events?: AgentEventFromDB[]): AgentTraceEvent[] => {
  if (!events || events.length === 0) {
    return [];
  }

  return events.map((event) => ({
    id: `db-${event.id}`,
    type: event.event_type as AgentTraceEventType,
    createdAt: event.created_at,
    payload: parseAgentPayload(event.payload),
  }));
};

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConfigured, setIsConfigured] = useState<boolean | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    const saved = localStorage.getItem('sidebar_collapsed');
    return saved === 'true';
  });

  const loadConversations = useCallback(async () => {
    try {
      const data = await getConversations();
      setConversations(data);

      setCurrentConversationId((prevId) => {
        if (data.length > 0 && prevId === null) {
          const sortedConversations = [...data].sort(
            (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
          );
          return sortedConversations[0].id;
        }
        return prevId;
      });
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  }, []);

  const selectConversation = useCallback((id: number | null) => {
    setCurrentConversationId(id);
  }, []);

  const loadMessages = useCallback(async (conversationId: number) => {
    try {
      const data = await getMessages(conversationId);
      const processedMessages: Message[] = data.map((message) => ({
        ...message,
        traceEvents: mapAgentEvents(message.agent_events),
        runId: message.agent_events?.[0]?.run_id,
      }));
      setMessages(processedMessages);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  }, []);

  const createNewConversation = useCallback(
    async (title: string = 'New Chat'): Promise<Conversation | null> => {
      try {
        const newConversation = await createConversation(title);
        setConversations((prev) => [newConversation, ...prev]);
        return newConversation;
      } catch (error) {
        console.error('Failed to create conversation:', error);
        return null;
      }
    },
    [],
  );

  const removeConversation = useCallback(
    async (id: number): Promise<void> => {
      try {
        await deleteConversation(id);
        setConversations((prev) => prev.filter((conversation) => conversation.id !== id));
        if (currentConversationId === id) {
          setCurrentConversationId(null);
          setMessages([]);
        }
      } catch (error) {
        console.error('Failed to delete conversation:', error);
        throw error;
      }
    },
    [currentConversationId],
  );

  const renameConversationById = useCallback(async (id: number, title: string): Promise<void> => {
    try {
      const updated = await renameConversation(id, title);
      setConversations((prev) =>
        prev.map((conversation) =>
          conversation.id === id
            ? { ...conversation, title: updated.title, updated_at: updated.updated_at }
            : conversation,
        ),
      );
    } catch (error) {
      console.error('Failed to rename conversation:', error);
      throw error;
    }
  }, []);

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed((prev) => {
      const nextValue = !prev;
      localStorage.setItem('sidebar_collapsed', String(nextValue));
      return nextValue;
    });
  }, []);

  const setSidebarCollapsedWithStorage = useCallback((collapsed: boolean) => {
    localStorage.setItem('sidebar_collapsed', String(collapsed));
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

export const useApp = (): AppContextType => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
