import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createPortal } from 'react-dom';
import { AnimatePresence, motion } from 'framer-motion';
import {
  AlertTriangle,
  ArrowRight,
  Check,
  Clock,
  Edit3,
  Loader2,
  MessageSquare,
  Search,
  Trash2,
  X,
} from 'lucide-react';

import MainLayout from '../layout/MainLayout';
import { useApp } from '../../contexts/AppContext';
import { getConversationStats } from '../../services/api';
import type { Conversation, Message } from '../../types';

interface ConversationWithStats extends Conversation {
  messageCount: number;
  lastMessage?: Message;
}

interface ConfirmDialogProps {
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}

interface RenameDialogProps {
  currentTitle: string;
  onConfirm: (newTitle: string) => void;
  onCancel: () => void;
}

const normalizeConversationTitle = (title: string) => {
  if (!title || title === 'New Chat' || title === '新对话') return '新会话';
  return title;
};

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({ title, message, onConfirm, onCancel }) => {
  return createPortal(
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.15, ease: 'easeOut' }}
      className="fixed inset-0 z-50 flex items-center justify-center"
      onClick={onCancel}
    >
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
        onClick={(event) => event.stopPropagation()}
        className="relative mx-4 w-full max-w-sm rounded-2xl glass-card p-6 shadow-2xl"
        style={{ border: '1px solid var(--glass-border)' }}
      >
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-500/20">
            <AlertTriangle size={20} className="text-red-500" />
          </div>
          <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
            {title}
          </h3>
        </div>
        <p className="mb-6 text-sm" style={{ color: 'var(--text-secondary)' }}>
          {message}
        </p>
        <div className="flex gap-3">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onCancel}
            className="glass flex-1 rounded-xl px-4 py-2.5 text-sm font-medium"
            style={{ color: 'var(--text-secondary)' }}
          >
            取消
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onConfirm}
            className="flex-1 rounded-xl bg-red-500 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-red-600"
          >
            确认删除
          </motion.button>
        </div>
      </motion.div>
    </motion.div>,
    document.body,
  );
};

const RenameDialog: React.FC<RenameDialogProps> = ({ currentTitle, onConfirm, onCancel }) => {
  const [title, setTitle] = useState(currentTitle);

  useEffect(() => {
    setTitle(currentTitle);
  }, [currentTitle]);

  return createPortal(
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.15, ease: 'easeOut' }}
      className="fixed inset-0 z-50 flex items-center justify-center"
      onClick={onCancel}
    >
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
        onClick={(event) => event.stopPropagation()}
        className="relative mx-4 w-full max-w-sm rounded-2xl glass-card p-6 shadow-2xl"
        style={{ border: '1px solid var(--glass-border)' }}
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
            重命名会话
          </h3>
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={onCancel}
            className="rounded-lg p-1.5 transition-colors"
            style={{ color: 'var(--text-muted)' }}
          >
            <X size={18} />
          </motion.button>
        </div>
        <input
          type="text"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="请输入会话标题"
          className="glass-input mb-4 w-full rounded-xl px-4 py-3"
          style={{ color: 'var(--text-primary)' }}
          autoFocus
          onKeyDown={(event) => {
            if (event.key === 'Enter' && title.trim()) {
              onConfirm(title.trim());
            }
            if (event.key === 'Escape') {
              onCancel();
            }
          }}
        />
        <div className="flex gap-3">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onCancel}
            className="glass flex-1 rounded-xl px-4 py-2.5 text-sm font-medium"
            style={{ color: 'var(--text-secondary)' }}
          >
            取消
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onConfirm(title.trim())}
            disabled={!title.trim()}
            className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Check size={16} />
            确认
          </motion.button>
        </div>
      </motion.div>
    </motion.div>,
    document.body,
  );
};

const ConversationsPage: React.FC = () => {
  const navigate = useNavigate();
  const { conversations, loadConversations, removeConversation, renameConversationById } = useApp();
  const [conversationsWithStats, setConversationsWithStats] = useState<ConversationWithStats[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<number | null>(null);
  const [renameTarget, setRenameTarget] = useState<{ id: number; title: string } | null>(null);

  const loadConversationStats = async () => {
    setIsLoading(true);
    try {
      const statsResponse = await getConversationStats();
      const statsMap = new Map(statsResponse.map((item) => [item.conversation_id, item]));
      const stats = conversations.map((conversation) => {
        const item = statsMap.get(conversation.id);
        const lastMessage =
          item?.last_message_content && item.last_message_created_at
            ? {
                id: item.last_message_id || Date.now(),
                conversation_id: conversation.id,
                role: 'assistant' as const,
                content: item.last_message_content,
                created_at: item.last_message_created_at,
              }
            : undefined;
        return {
          ...conversation,
          title: normalizeConversationTitle(conversation.title),
          messageCount: item?.message_count || 0,
          lastMessage,
        };
      });
      setConversationsWithStats(
        stats.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()),
      );
    } catch (error) {
      console.error('Failed to load conversation stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    if (conversations.length > 0) {
      void loadConversationStats();
    } else {
      setConversationsWithStats([]);
      setIsLoading(false);
    }
  }, [conversations]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins} 分钟前`;
    if (diffHours < 24) return `${diffHours} 小时前`;
    if (diffDays < 7) return `${diffDays} 天前`;
    return date.toLocaleDateString('zh-CN');
  };

  const truncateMessage = (content: string, maxLength: number = 50) => {
    if (content.length <= maxLength) return content;
    return `${content.substring(0, maxLength)}...`;
  };

  const filteredConversations = conversationsWithStats.filter((conversation) =>
    normalizeConversationTitle(conversation.title).toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const handleDelete = async () => {
    if (deleteTarget === null) return;

    if (conversations.length <= 1) {
      alert('无法删除最后一个会话，系统至少需要保留一个。');
      setDeleteTarget(null);
      return;
    }

    try {
      await removeConversation(deleteTarget);
      setDeleteTarget(null);
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      alert('删除会话失败，请稍后重试。');
    }
  };

  const handleRename = async (newTitle: string) => {
    if (renameTarget === null || !newTitle) return;
    try {
      await renameConversationById(renameTarget.id, newTitle);
      setRenameTarget(null);
    } catch (error) {
      console.error('Failed to rename conversation:', error);
    }
  };

  const goToChat = (conversationId: number) => {
    navigate(`/chat/${conversationId}`);
  };

  return (
    <MainLayout
      headerTitle="会话"
      headerSubtitle="查看和管理你的历史会话，继续未完成的上下文。"
    >
      <div className="flex h-full flex-col p-6">
        <div className="mb-6">
          <div className="relative">
            <Search
              size={18}
              className="absolute left-4 top-1/2 -translate-y-1/2"
              style={{ color: 'var(--text-muted)' }}
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="搜索会话..."
              className="glass-input w-full rounded-xl py-3 pl-12 pr-4"
              style={{ color: 'var(--text-primary)' }}
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="flex h-64 items-center justify-center">
              <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
                <Loader2 size={32} className="text-primary" />
              </motion.div>
            </div>
          ) : filteredConversations.length === 0 ? (
            <div className="flex h-64 flex-col items-center justify-center">
              <MessageSquare
                size={48}
                strokeWidth={1}
                className="mb-4 opacity-50"
                style={{ color: 'var(--text-muted)' }}
              />
              <p style={{ color: 'var(--text-muted)' }}>{searchQuery ? '没有找到匹配的会话' : '暂无会话'}</p>
              <p className="mt-1 text-sm opacity-60" style={{ color: 'var(--text-muted)' }}>
                {searchQuery ? '试试别的关键词' : '先开始一个新会话吧'}
              </p>
            </div>
          ) : (
            <div
              className="hidden overflow-hidden rounded-2xl glass-card lg:block"
              style={{ border: '1px solid var(--glass-border)' }}
            >
              <div className="conversations-table">
                <div className="px-5 py-3.5 text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--glass-border)' }}>
                  会话标题
                </div>
                <div className="px-4 py-3.5 text-center text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--glass-border)' }}>
                  消息数
                </div>
                <div className="px-4 py-3.5 text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--glass-border)' }}>
                  最近更新
                </div>
                <div className="px-4 py-3.5 text-center text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--glass-border)' }}>
                  操作
                </div>
              </div>

              <AnimatePresence mode="popLayout">
                {filteredConversations.map((conversation, index) => (
                  <motion.div
                    key={conversation.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ delay: index * 0.03 }}
                    className="group conversations-table cursor-pointer transition-colors hover:bg-[var(--glass-bg)]"
                    style={{
                      borderBottom: index < filteredConversations.length - 1 ? '1px solid var(--glass-border)' : 'none',
                    }}
                    onClick={() => goToChat(conversation.id)}
                  >
                    <div className="flex items-center gap-3 px-5 py-4">
                      <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl" style={{ backgroundColor: 'var(--primary-alpha)' }}>
                        <MessageSquare size={18} className="text-primary" />
                      </div>
                      <div className="min-w-0">
                        <h3 className="truncate text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                          {normalizeConversationTitle(conversation.title)}
                        </h3>
                        {conversation.lastMessage ? (
                          <p className="mt-0.5 truncate text-xs" style={{ color: 'var(--text-muted)' }}>
                            {truncateMessage(conversation.lastMessage.content, 40)}
                          </p>
                        ) : null}
                      </div>
                    </div>

                    <div className="flex items-center justify-center px-4 py-4">
                      <span className="rounded-lg px-2.5 py-1 text-sm font-medium" style={{ backgroundColor: 'var(--glass-bg)', color: 'var(--text-secondary)' }}>
                        {conversation.messageCount}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 px-4 py-4">
                      <Clock size={14} style={{ color: 'var(--text-muted)' }} />
                      <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
                        {formatDate(conversation.updated_at)}
                      </span>
                    </div>

                    <div className="flex items-center justify-center gap-1 px-4 py-4">
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={(event) => {
                          event.stopPropagation();
                          setRenameTarget({ id: conversation.id, title: normalizeConversationTitle(conversation.title) });
                        }}
                        className="rounded-lg p-2 opacity-0 transition-colors group-hover:opacity-100"
                        style={{ color: 'var(--text-muted)' }}
                        title="重命名"
                      >
                        <Edit3 size={16} />
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={(event) => {
                          event.stopPropagation();
                          setDeleteTarget(conversation.id);
                        }}
                        className="rounded-lg p-2 opacity-0 transition-colors group-hover:opacity-100"
                        style={{ color: 'var(--text-muted)' }}
                        title="删除"
                      >
                        <Trash2 size={16} />
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="rounded-lg p-2 opacity-0 transition-colors group-hover:opacity-100"
                        style={{ color: 'var(--text-muted)' }}
                        title="进入会话"
                      >
                        <ArrowRight size={16} />
                      </motion.button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}

          {filteredConversations.length > 0 ? (
            <div className="grid grid-cols-1 gap-3 lg:hidden">
              <AnimatePresence mode="popLayout">
                {filteredConversations.map((conversation, index) => (
                  <motion.div
                    key={conversation.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ delay: index * 0.03 }}
                    className="cursor-pointer rounded-xl glass-card p-4"
                    style={{ border: '1px solid var(--glass-border)' }}
                    onClick={() => goToChat(conversation.id)}
                  >
                    <div className="mb-2 flex items-center gap-3">
                      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg" style={{ backgroundColor: 'var(--primary-alpha)' }}>
                        <MessageSquare size={16} className="text-primary" />
                      </div>
                      <h3 className="flex-1 truncate text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                        {normalizeConversationTitle(conversation.title)}
                      </h3>
                      <span className="rounded-md px-2 py-0.5 text-xs" style={{ backgroundColor: 'var(--glass-bg)', color: 'var(--text-muted)' }}>
                        {conversation.messageCount} 条消息
                      </span>
                    </div>
                    {conversation.lastMessage ? (
                      <p className="mb-2 line-clamp-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                        {truncateMessage(conversation.lastMessage.content, 60)}
                      </p>
                    ) : null}
                    <div className="flex items-center justify-between">
                      <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                        {formatDate(conversation.updated_at)}
                      </span>
                      <div className="flex items-center gap-1">
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={(event) => {
                            event.stopPropagation();
                            setRenameTarget({ id: conversation.id, title: normalizeConversationTitle(conversation.title) });
                          }}
                          className="rounded-lg p-1.5"
                          style={{ color: 'var(--text-muted)' }}
                          title="重命名"
                        >
                          <Edit3 size={14} />
                        </motion.button>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={(event) => {
                            event.stopPropagation();
                            setDeleteTarget(conversation.id);
                          }}
                          className="rounded-lg p-1.5"
                          style={{ color: 'var(--text-muted)' }}
                          title="删除"
                        >
                          <Trash2 size={14} />
                        </motion.button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          ) : null}
        </div>

        <div className="mt-4 pt-4 text-center text-xs" style={{ color: 'var(--text-muted)', borderTop: '1px solid var(--glass-border)' }}>
          共 {filteredConversations.length} 个会话
        </div>

        <AnimatePresence>
          {deleteTarget !== null ? (
            <ConfirmDialog
              title="删除会话"
              message="确认要删除这个会话吗？删除后无法恢复，相关消息也会一并移除。"
              onConfirm={handleDelete}
              onCancel={() => setDeleteTarget(null)}
            />
          ) : null}
        </AnimatePresence>

        <AnimatePresence>
          {renameTarget !== null ? (
            <RenameDialog
              currentTitle={renameTarget.title}
              onConfirm={handleRename}
              onCancel={() => setRenameTarget(null)}
            />
          ) : null}
        </AnimatePresence>
      </div>
    </MainLayout>
  );
};

export default ConversationsPage;
