import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Trash2, MessageSquare, Clock } from 'lucide-react';
import type { Conversation } from '../types';

interface ConversationListProps {
  conversations: Conversation[];
  currentConversationId: number | null;
  onSelectConversation: (id: number) => void;
  onCreateConversation: () => void;
  onDeleteConversation: (id: number) => void;
}

/**
 * 会话列表组件 - 显示和管理所有对话会话
 * 采用玻璃拟态设计，支持动画效果和主题切换
 */
const ConversationList: React.FC<ConversationListProps> = ({
  conversations,
  currentConversationId,
  onSelectConversation,
  onCreateConversation,
  onDeleteConversation,
}) => {
  /**
   * 格式化日期显示
   */
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  /**
   * 处理删除会话
   */
  const handleDelete = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (confirm('确定要删除这个对话吗？')) {
      onDeleteConversation(id);
    }
  };

  return (
    <motion.div
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="w-72 h-full flex flex-col glass-card"
      style={{ borderRight: '1px solid var(--glass-border)' }}
    >
      <div className="p-4" style={{ borderBottom: '1px solid var(--glass-border)' }}>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onCreateConversation}
          className="w-full btn-primary flex items-center justify-center gap-2 py-3"
        >
          <Plus size={20} />
          <span>新建对话</span>
        </motion.button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        <AnimatePresence mode="popLayout">
          {conversations.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center py-12"
              style={{ color: 'var(--text-muted)' }}
            >
              <MessageSquare size={48} strokeWidth={1} className="mb-4 opacity-50" />
              <p className="text-sm">暂无对话</p>
              <p className="text-xs mt-1 opacity-60">点击上方按钮开始新对话</p>
            </motion.div>
          ) : (
            conversations.map((conversation, index) => (
              <motion.div
                key={conversation.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => onSelectConversation(conversation.id)}
                className={`group relative p-4 rounded-xl cursor-pointer transition-all duration-300 ${
                  currentConversationId === conversation.id
                    ? 'bg-gradient-to-r from-primary/20 to-primary-dark/20 border border-primary/30 shadow-glow'
                    : 'glass hover:bg-white/5 hover:border-white/10'
                }`}
              >
                {currentConversationId === conversation.id && (
                  <motion.div
                    layoutId="activeIndicator"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-gradient-to-b from-primary to-primary-dark rounded-r-full"
                  />
                )}

                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <h3
                      className="text-sm font-medium truncate mb-1"
                      style={{ color: 'var(--text-primary)' }}
                    >
                      {conversation.title}
                    </h3>
                    <div
                      className="flex items-center gap-1.5 text-xs"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      <Clock size={12} />
                      <span>{formatDate(conversation.updated_at)}</span>
                    </div>
                  </div>

                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={(e) => handleDelete(e, conversation.id)}
                    className="opacity-0 group-hover:opacity-100 p-2 rounded-lg transition-all"
                    style={{ color: 'var(--text-muted)' }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.color = '#ef4444';
                      e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.color = 'var(--text-muted)';
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    <Trash2 size={16} />
                  </motion.button>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

      <div className="p-4" style={{ borderTop: '1px solid var(--glass-border)' }}>
        <div className="flex items-center justify-between text-xs" style={{ color: 'var(--text-muted)' }}>
          <span>共 {conversations.length} 个对话</span>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <span>在线</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default ConversationList;
