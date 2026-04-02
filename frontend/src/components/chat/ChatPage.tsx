import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle } from 'lucide-react';

import MainLayout from '../layout/MainLayout';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import ThemeToggle from '../common/ThemeToggle';
import ConversationSelect from '../common/ConversationSelect';
import SessionSelect from '../common/SessionSelect';
import { useApp } from '../../contexts/AppContext';
import { sendMessageStream, getConfig } from '../../services/api';
import type { AgentTraceEvent, AgentTraceEventPayload, AgentTraceEventType, Message } from '../../types';

const buildTraceEvent = (
  type: AgentTraceEventType,
  payload: AgentTraceEventPayload,
): AgentTraceEvent => ({
  id: `${type}-${payload.tool_call_id || payload.iteration || Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
  type,
  createdAt: new Date().toISOString(),
  payload,
});

const appendTraceEvent = (
  previousEvents: AgentTraceEvent[] = [],
  type: AgentTraceEventType,
  payload: AgentTraceEventPayload,
): AgentTraceEvent[] => {
  if (type === 'reasoning' && previousEvents.length > 0) {
    const lastEvent = previousEvents[previousEvents.length - 1];
    if (lastEvent.type === 'reasoning') {
      const mergedContent = `${lastEvent.payload.content || ''}${payload.content || ''}`;
      return [
        ...previousEvents.slice(0, -1),
        {
          ...lastEvent,
          payload: {
            ...lastEvent.payload,
            ...payload,
            content: mergedContent,
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
    currentSessionId,
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
  const chunkBufferRef = useRef('');
  const flushTimerRef = useRef<number | null>(null);

  useEffect(() => {
    checkConfiguration();
    loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    if (conversationId) {
      const id = parseInt(conversationId, 10);
      if (!Number.isNaN(id) && id !== currentConversationId) {
        selectConversation(id);
      }
    }
  }, [conversationId, selectConversation, currentConversationId]);

  useEffect(() => {
    if (!currentConversationId && conversations.length > 0) {
      const sortedConversations = [...conversations].sort(
        (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
      );
      const mostRecent = sortedConversations[0];
      selectConversation(mostRecent.id);
      navigate(`/chat/${mostRecent.id}`, { replace: true });
    }
  }, [conversations, currentConversationId, selectConversation, navigate]);

  useEffect(() => {
    return () => {
      if (flushTimerRef.current !== null) {
        window.clearTimeout(flushTimerRef.current);
      }
    };
  }, []);

  const checkConfiguration = async () => {
    try {
      await getConfig('zhipu_api_key');
      setIsConfigured(true);
    } catch {
      setIsConfigured(false);
    }
  };

  const handleCreateNewChat = async () => {
    const newConversation = await createNewConversation('新聊天');
    if (newConversation) {
      selectConversation(newConversation.id);
      navigate(`/chat/${newConversation.id}`, { replace: true });
    }
  };

  const updateStreamingMessage = (tempMessageId: number, updater: (message: Message) => Message) => {
    setMessages((prev) => prev.map((message) => (message.id === tempMessageId ? updater(message) : message)));
  };

  const showNotice = (message: string) => {
    setNotice(message);
    window.setTimeout(() => {
      setNotice((prev) => (prev === message ? null : prev));
    }, 3000);
  };

  const flushBufferedChunk = (tempMessageId: number) => {
    if (!chunkBufferRef.current) {
      return;
    }
    const content = chunkBufferRef.current;
    chunkBufferRef.current = '';
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
    const isChatCommand = trimmedContent.startsWith('/');

    if (trimmedContent === '/new') {
      await handleCreateNewChat();
      return;
    }

    if (isConfigured === false && !isChatCommand) {
      showNotice('请先在设置中配置 API Key。');
      navigate('/settings');
      return;
    }

    if (!currentConversationId) {
      showNotice('聊天记录仍在加载中，请稍后重试。');
      return;
    }
    if (!currentSessionId) {
      showNotice('工作会话仍在加载中，请稍后重试。');
      return;
    }

    setIsSending(true);

    const conversationIdToUse = currentConversationId;
    const now = new Date().toISOString();

    const userMessage: Message = {
      id: Date.now(),
      conversation_id: conversationIdToUse,
      role: 'user',
      content: trimmedContent,
      created_at: now,
    };

    const tempAiMessage: Message = {
      id: Date.now() + 1,
      conversation_id: conversationIdToUse,
      role: 'assistant',
      content: '',
      created_at: now,
      traceEvents: [],
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, tempAiMessage]);

    try {
      await sendMessageStream(
        {
          session_id: currentSessionId,
          conversation_id: conversationIdToUse,
          message: trimmedContent,
        },
        {
          onChunk: (chunk) => {
            chunkBufferRef.current += chunk;
            scheduleChunkFlush(tempAiMessage.id);
          },
          onConversation: (nextConversationId, runId) => {
            updateStreamingMessage(tempAiMessage.id, (message) => ({
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
            updateStreamingMessage(tempAiMessage.id, (message) => ({
              ...message,
              runId: payload.run_id || message.runId,
              traceEvents: appendTraceEvent(message.traceEvents, type, payload),
            }));
          },
          onComplete: (_message, conversationIdFromStream) => {
            if (flushTimerRef.current !== null) {
              window.clearTimeout(flushTimerRef.current);
              flushTimerRef.current = null;
            }
            flushBufferedChunk(tempAiMessage.id);
            updateStreamingMessage(tempAiMessage.id, (message) => ({
              ...message,
              conversation_id: conversationIdFromStream,
              isStreaming: false,
            }));
            loadConversations();
          },
          onError: (error) => {
            if (flushTimerRef.current !== null) {
              window.clearTimeout(flushTimerRef.current);
              flushTimerRef.current = null;
            }
            flushBufferedChunk(tempAiMessage.id);
            console.error('Chat error:', error);
            updateStreamingMessage(tempAiMessage.id, (message) => ({
              ...message,
              content: message.content || '消息发送失败，请检查 API Key 和工具配置后重试。',
              traceEvents: appendTraceEvent(message.traceEvents, 'loop_warning', {
                message: error.message,
                severity: 'error',
              }),
              isStreaming: false,
            }));
            showNotice('消息发送失败，请检查配置后重试。');
          },
        },
      );
    } catch (error) {
      if (flushTimerRef.current !== null) {
        window.clearTimeout(flushTimerRef.current);
        flushTimerRef.current = null;
      }
      flushBufferedChunk(tempAiMessage.id);
      console.error('Failed to send message:', error);
      updateStreamingMessage(tempAiMessage.id, (message) => ({
        ...message,
        content: '消息发送失败，请检查 API Key 和工具配置后重试。',
        isStreaming: false,
      }));
      showNotice('消息发送失败，请检查配置后重试。');
    } finally {
      setIsSending(false);
    }
  };

  return (
    <MainLayout showHeader={false}>
      <div className="chat-page">
        <header className="chat-header">
          <div className="flex items-center gap-3 min-w-0 flex-wrap">
            <div className="flex flex-col gap-1 min-w-[200px]">
              <span className="text-xs font-medium px-1" style={{ color: 'var(--text-muted)' }}>
                工作会话
              </span>
              <SessionSelect />
            </div>
            <div className="flex flex-col gap-1 min-w-[220px]">
              <span className="text-xs font-medium px-1" style={{ color: 'var(--text-muted)' }}>
                聊天记录
              </span>
              <ConversationSelect />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />
          </div>
        </header>

        <AnimatePresence>
          {notice && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="px-6 pt-3"
            >
              <div className="warning-banner p-3 text-sm">{notice}</div>
            </motion.div>
          )}
          {isConfigured === false && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="px-6 pt-4"
            >
              <div className="warning-banner p-4 flex items-center gap-3">
                <AlertTriangle size={20} className="text-yellow-500 flex-shrink-0" />
                <p className="text-yellow-700 dark:text-yellow-200/90 text-sm">
                  使用聊天前请先配置 API Key。{' '}
                  <Link to="/settings" className="underline font-semibold">
                    打开设置
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
