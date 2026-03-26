import { useState, useEffect, useRef } from 'react';
import ConversationList from './components/ConversationList';
import MessageList from './components/MessageList';
import MessageInput from './components/MessageInput';
import Settings from './components/Settings';
import { Conversation, Message } from './types';
import { sendMessageStream, getConversations, createConversation, deleteConversation, getMessages } from './services/api';

/**
 * 主应用组件 - AI对话应用
 */
const App: React.FC = () => {
  const [apiKey, setApiKey] = useState(() => {
    return localStorage.getItem('api_key') || '';
  });
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 滚动到消息底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 加载会话列表
  useEffect(() => {
    loadConversations();
  }, []);

  // 加载当前会话的消息
  useEffect(() => {
    if (currentConversationId) {
      loadMessages(currentConversationId);
    } else {
      setMessages([]);
    }
  }, [currentConversationId]);

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
    if (!apiKey) {
      alert('请先在设置中配置API Key');
      return;
    }

    setIsLoading(true);

    // 如果没有当前会话，创建一个新会话
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

    // 添加用户消息
    const userMessage: Message = {
      id: Date.now(),
      conversation_id: conversationId,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // 创建临时AI消息用于流式显示
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
          api_key: apiKey,
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
        (finalMessage, finalConversationId) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === tempAiMessage.id ? finalMessage : msg
            )
          );
          loadConversations();
        },
        (error) => {
          console.error('Chat error:', error);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === tempAiMessage.id
                ? { ...msg, content: '发送失败，请重试' }
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
            ? { ...msg, content: '发送失败，请重试' }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleApiKeyChange = (newApiKey: string) => {
    setApiKey(newApiKey);
    localStorage.setItem('api_key', newApiKey);
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
          <Settings apiKey={apiKey} onApiKeyChange={handleApiKeyChange} />
        </div>
        <MessageList messages={messages} />
        <div ref={messagesEndRef} />
        <MessageInput onSendMessage={handleSendMessage} disabled={isLoading} />
      </div>
    </div>
  );
};

export default App;
