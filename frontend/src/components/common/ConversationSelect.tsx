import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ChevronDown, MessageCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { useApp } from '../../contexts/AppContext';

interface ConversationSelectProps {
  className?: string;
}

const normalizeConversationTitle = (title?: string | null) => {
  if (!title) return '选择聊天记录';
  if (title === 'New Chat') return '新聊天';
  return title;
};

const ConversationSelect: React.FC<ConversationSelectProps> = ({ className = '' }) => {
  const { conversations, currentConversationId, selectConversation } = useApp();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentConversation = conversations.find((conversation) => conversation.id === currentConversationId);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (id: number) => {
    selectConversation(id);
    navigate(`/chat/${id}`, { replace: true });
    setIsOpen(false);
  };

  const sortedConversations = [...conversations].sort(
    (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
  );

  return (
    <div ref={dropdownRef} className={`relative z-[100] ${className}`}>
      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        onClick={() => setIsOpen((value) => !value)}
        className="conversation-select-trigger"
        aria-label="选择聊天记录"
        title="选择聊天记录"
      >
        <MessageCircle size={16} style={{ color: 'var(--accent)' }} />
        <span className="conversation-select-label">{normalizeConversationTitle(currentConversation?.title)}</span>
        <motion.div animate={{ rotate: isOpen ? 180 : 0 }} transition={{ duration: 0.18 }}>
          <ChevronDown size={16} style={{ color: 'var(--text-muted)' }} />
        </motion.div>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.15 }}
            className="conversation-select-menu"
          >
            {sortedConversations.length === 0 ? (
              <div className="conversation-select-empty">暂无聊天记录</div>
            ) : (
              sortedConversations.map((conversation) => (
                <button
                  key={conversation.id}
                  onClick={() => handleSelect(conversation.id)}
                  className={`conversation-select-item ${conversation.id === currentConversationId ? 'is-active' : ''}`}
                >
                  <MessageCircle size={14} />
                  <span>{normalizeConversationTitle(conversation.title)}</span>
                </button>
              ))
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ConversationSelect;
