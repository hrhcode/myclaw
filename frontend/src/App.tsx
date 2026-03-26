import { useState, useEffect, useRef } from 'react';
import { BrowserRouter, Routes, Route, Link, useNavigate } from 'react-router-dom';
import ConversationList from './components/ConversationList';
import MessageList from './components/MessageList';
import MessageInput from './components/MessageInput';
import Settings from './components/Settings';
import type { Conversation, Message } from './types';
import { sendMessageStream, getConversations, createConversation, deleteConversation, getMessages, getConfig } from './services/api';

const ChatPage: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isConfigured, setIsConfigured] = useState<boolean | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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

  const checkConfiguration = async () => {
    try {
      await getConfig('zhipu_api_key');
      setIsConfigured(true);
    } catch {
      setIsConfigured(false);
    }
  };

  const loadConversations = async () => {
    try {
      const data = await getConversations();
      setConversations(data);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadMessages = async (conversationId: number) => {
    try {
      const data = await getMessages(conversationId);
      setMessages(data);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const handleCreateConversation = async () => {
    try {
      const newConversation = await createConversation('新对话');
      setConversations([newConversation, ...conversations]);
      setCurrentConversationId(newConversation.id);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const handleDeleteConversation = async (id: number) => {
    try {
      await deleteConversation(id);
      setConversations(conversations.filter((c) => c.id !== id));
      if (currentConversationId === id) {
        setCurrentConversationId(null);
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (isConfigured === false) {
      alert('请先在设置页面配置API Key');
      navigate('/settings');
      return;
    }

    setIsLoading(true);

    let conversationId = currentConversationId;
    if (!conversationId) {
      try {
        const newConversation = await createConversation(content.substring(0, 20) + '...');
        setConversations([newConversation, ...conversations]);
        conversationId = newConversation.id;
        setCurrentConversationId(conversationId);
      } catch (error) {
        console.error('Failed to create conversation:', error);
        setIsLoading(false);
        return;
      }
    }

    const userMessage: Message = {
      id: Date.now(),
      conversation_id: conversationId,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    const tempAiMessage: Message = {
      id: Date.now() + 1,
      conversation_id: conversationId,
      role: 'assistant',
      content: '',
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
                : msg
            )
          );
        },
        () => {
          loadConversations();
        },
        (error) => {
          console.error('Chat error:', error);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === tempAiMessage.id
                ? { ...msg, content: '发送失败，请检查是否已配置API Key' }
                : msg
            )
          );
        }
      );
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === tempAiMessage.id
            ? { ...msg, content: '发送失败，请检查是否已配置API Key' }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900">
      <ConversationList
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={setCurrentConversationId}
        onCreateConversation={handleCreateConversation}
        onDeleteConversation={handleDeleteConversation}
      />
      <div className="flex-1 flex flex-col">
        <div className="h-14 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-4">
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
            AI对话助手
          </h1>
          <Link
            to="/settings"
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            设置
          </Link>
        </div>
        {isConfigured === false && (
          <div className="bg-yellow-100 border-l-4 border-yellow-500 p-4 m-4">
            <p className="text-yellow-700">
              请先配置API Key才能使用聊天功能。{' '}
              <Link to="/settings" className="underline font-semibold">
                去设置
              </Link>
            </p>
          </div>
        )}
        <MessageList messages={messages} />
        <div ref={messagesEndRef} />
        <MessageInput onSendMessage={handleSendMessage} disabled={isLoading} />
      </div>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;