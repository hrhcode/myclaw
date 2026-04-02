import { createContext, useContext, useEffect, useCallback, useState } from 'react';
import type { ReactNode } from 'react';

import type {
  AgentEventFromDB,
  AgentTraceEvent,
  AgentTraceEventPayload,
  AgentTraceEventType,
  Conversation,
  Message,
  Session,
} from '../types';
import {
  createConversationForSession,
  createSession,
  deleteConversation,
  deleteSession,
  getConversationsBySession,
  getMessages,
  getSessions,
  renameConversation,
  updateSession,
} from '../services/api';

interface AppContextType {
  sessions: Session[];
  currentSessionId: number | null;
  conversations: Conversation[];
  currentConversationId: number | null;
  messages: Message[];
  isConfigured: boolean | null;
  sidebarCollapsed: boolean;
  loadSessions: () => Promise<void>;
  selectSession: (id: number | null) => void;
  createNewSession: (name?: string) => Promise<Session | null>;
  updateSessionById: (id: number, payload: Partial<Session>) => Promise<void>;
  removeSession: (id: number) => Promise<void>;
  loadConversations: (sessionId?: number | null) => Promise<void>;
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

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConfigured, setIsConfigured] = useState<boolean | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => localStorage.getItem('sidebar_collapsed') === 'true');

  const loadSessions = useCallback(async () => {
    try {
      const data = await getSessions();
      setSessions(data);
      setCurrentSessionId((prev) => prev ?? data.find((item) => item.is_default)?.id ?? data[0]?.id ?? null);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  }, []);

  const loadConversations = useCallback(async (sessionId?: number | null) => {
    const effectiveSessionId = sessionId ?? currentSessionId;
    if (!effectiveSessionId) {
      setConversations([]);
      setCurrentConversationId(null);
      return;
    }
    try {
      const data = await getConversationsBySession(effectiveSessionId);
      setConversations(data);
      setCurrentConversationId((prev) => {
        if (prev && data.some((item) => item.id === prev)) {
          return prev;
        }
        return data[0]?.id ?? null;
      });
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  }, [currentSessionId]);

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
      console.error('Failed to load messages:', error);
    }
  }, []);

  const selectSession = useCallback((id: number | null) => {
    setCurrentSessionId(id);
    setCurrentConversationId(null);
  }, []);

  const selectConversation = useCallback((id: number | null) => {
    setCurrentConversationId(id);
  }, []);

  const createNewSession = useCallback(async (name = `session-${Date.now()}`): Promise<Session | null> => {
    try {
      const session = await createSession({ name, tool_profile: 'full', max_iterations: 5 });
      await loadSessions();
      setCurrentSessionId(session.id);
      return session;
    } catch (error) {
      console.error('Failed to create session:', error);
      return null;
    }
  }, [loadSessions]);

  const updateSessionById = useCallback(async (id: number, payload: Partial<Session>) => {
    const updated = await updateSession(id, payload);
    setSessions((prev) => prev.map((session) => (session.id === id ? updated : session)));
    if (payload.is_default) {
      await loadSessions();
    }
  }, [loadSessions]);

  const removeSession = useCallback(async (id: number) => {
    await deleteSession(id);
    await loadSessions();
  }, [loadSessions]);

  const createNewConversation = useCallback(async (title = 'New Chat'): Promise<Conversation | null> => {
    if (!currentSessionId) {
      return null;
    }
    try {
      const conversation = await createConversationForSession(title, currentSessionId);
      setConversations((prev) => [conversation, ...prev]);
      setCurrentConversationId(conversation.id);
      return conversation;
    } catch (error) {
      console.error('Failed to create conversation:', error);
      return null;
    }
  }, [currentSessionId]);

  const removeConversation = useCallback(async (id: number) => {
    await deleteConversation(id);
    setConversations((prev) => prev.filter((conversation) => conversation.id !== id));
    if (currentConversationId === id) {
      setCurrentConversationId(null);
      setMessages([]);
    }
  }, [currentConversationId]);

  const renameConversationById = useCallback(async (id: number, title: string) => {
    const updated = await renameConversation(id, title);
    setConversations((prev) =>
      prev.map((conversation) =>
        conversation.id === id ? { ...conversation, title: updated.title, updated_at: updated.updated_at } : conversation,
      ),
    );
  }, []);

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem('sidebar_collapsed', String(next));
      return next;
    });
  }, []);

  const setSidebarCollapsedWithStorage = useCallback((collapsed: boolean) => {
    localStorage.setItem('sidebar_collapsed', String(collapsed));
    setSidebarCollapsed(collapsed);
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    if (currentSessionId) {
      loadConversations(currentSessionId);
    }
  }, [currentSessionId, loadConversations]);

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
        sessions,
        currentSessionId,
        conversations,
        currentConversationId,
        messages,
        isConfigured,
        sidebarCollapsed,
        loadSessions,
        selectSession,
        createNewSession,
        updateSessionById,
        removeSession,
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
