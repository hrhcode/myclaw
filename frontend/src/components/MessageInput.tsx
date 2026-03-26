import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Send, Loader2 } from 'lucide-react';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

/**
 * 消息输入组件 - 用于输入和发送消息
 * 采用玻璃拟态设计，支持自动调整高度和主题切换
 */
const MessageInput: React.FC<MessageInputProps> = ({ onSendMessage, disabled = false }) => {
  const [message, setMessage] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  /**
   * 自动调整文本框高度
   */
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
    }
  }, [message]);

  /**
   * 处理表单提交
   */
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  /**
   * 处理键盘事件
   */
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  /**
   * 判断是否可以发送
   */
  const canSend = message.trim() && !disabled;

  return (
    <div className="p-4" style={{ borderTop: '1px solid var(--glass-border)' }}>
      <form onSubmit={handleSubmit} className="relative">
        <motion.div
          animate={{
            boxShadow: isFocused
              ? '0 0 0 2px rgba(102, 126, 234, 0.3), 0 0 20px rgba(102, 126, 234, 0.2)'
              : '0 0 0 0 transparent',
          }}
          transition={{ duration: 0.2 }}
          className="relative flex items-end gap-3 p-3 rounded-2xl glass"
        >
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="输入消息... (Shift+Enter 换行)"
              disabled={disabled}
              rows={1}
              className="w-full px-4 py-3 bg-transparent resize-none focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ 
                maxHeight: '150px',
                color: 'var(--text-primary)',
              }}
            />
          </div>

          <motion.button
            type="submit"
            disabled={!canSend}
            whileHover={canSend ? { scale: 1.05 } : {}}
            whileTap={canSend ? { scale: 0.95 } : {}}
            className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-300 ${
              canSend
                ? 'bg-gradient-to-r from-primary to-primary-dark text-white shadow-glow hover:shadow-glow-lg'
                : 'bg-white/5 text-white/30 cursor-not-allowed'
            }`}
          >
            {disabled ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              >
                <Loader2 size={20} />
              </motion.div>
            ) : (
              <Send size={20} className={canSend ? 'translate-x-0.5' : ''} />
            )}
          </motion.button>
        </motion.div>

        <div className="flex items-center justify-between mt-2 px-2">
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
            按 Enter 发送，Shift+Enter 换行
          </span>
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
            {message.length} 字符
          </span>
        </div>
      </form>
    </div>
  );
};

export default MessageInput;
