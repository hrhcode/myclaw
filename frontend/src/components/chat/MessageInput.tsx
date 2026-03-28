import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, PlusCircle, Command } from "lucide-react";

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  onCreateNewChat?: () => void;
}

interface CommandItem {
  command: string;
  description: string;
  icon: React.ReactNode;
  action?: () => void;
}

const COMMANDS: CommandItem[] = [
  {
    command: "/new",
    description: "创建新会话",
    icon: <PlusCircle size={16} />,
  },
];

const MessageInput: React.FC<MessageInputProps> = ({
  onSendMessage,
  disabled = false,
  onCreateNewChat,
}) => {
  const [message, setMessage] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [showCommands, setShowCommands] = useState(false);
  const [selectedCommandIndex, setSelectedCommandIndex] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const commandListRef = useRef<HTMLDivElement>(null);

  const filteredCommands = message.startsWith("/")
    ? COMMANDS.filter((cmd) =>
        cmd.command.toLowerCase().startsWith(message.toLowerCase()),
      )
    : [];

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
    }
  }, [message]);

  useEffect(() => {
    if (message.startsWith("/")) {
      setShowCommands(true);
      setSelectedCommandIndex(0);
    } else {
      setShowCommands(false);
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage("");
      setShowCommands(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (showCommands && filteredCommands.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedCommandIndex((prev) =>
          prev < filteredCommands.length - 1 ? prev + 1 : 0,
        );
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedCommandIndex((prev) =>
          prev > 0 ? prev - 1 : filteredCommands.length - 1,
        );
        return;
      }
      if (e.key === "Tab" || (e.key === "Enter" && !e.shiftKey)) {
        e.preventDefault();
        selectCommand(filteredCommands[selectedCommandIndex]);
        return;
      }
      if (e.key === "Escape") {
        setShowCommands(false);
        return;
      }
    }

    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const selectCommand = (cmd: CommandItem) => {
    setMessage(cmd.command + " ");
    setShowCommands(false);
    textareaRef.current?.focus();
  };

  const canSend = message.trim() && !disabled;

  return (
    <div className="p-4" style={{ borderTop: "1px solid var(--glass-border)" }}>
      <form onSubmit={handleSubmit} className="relative">
        <motion.div
          animate={{
            boxShadow: isFocused
              ? "0 0 0 2px rgba(102, 126, 234, 0.3), 0 0 20px rgba(102, 126, 234, 0.2)"
              : "0 0 0 0 transparent",
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
              placeholder="输入消息... (Shift+Enter 换行, / 查看命令)"
              disabled={disabled}
              rows={1}
              className="w-full px-4 py-3 bg-transparent resize-none focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                maxHeight: "150px",
                color: "var(--text-primary)",
              }}
            />

            <AnimatePresence>
              {showCommands && filteredCommands.length > 0 && (
                <motion.div
                  ref={commandListRef}
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 10, scale: 0.95 }}
                  transition={{ duration: 0.15 }}
                  className="absolute bottom-full left-0 mb-2 w-64 rounded-xl glass-card overflow-hidden z-50"
                  style={{
                    boxShadow: "var(--shadow-lg)",
                  }}
                >
                  <div
                    className="px-3 py-2 text-xs font-medium border-b"
                    style={{
                      color: "var(--text-muted)",
                      borderColor: "var(--glass-border)",
                    }}
                  >
                    <Command size={12} className="inline mr-1" />
                    命令提示
                  </div>
                  {filteredCommands.map((cmd, index) => (
                    <motion.button
                      key={cmd.command}
                      type="button"
                      whileHover={{ backgroundColor: "var(--glass-hover)" }}
                      onClick={() => selectCommand(cmd)}
                      className={`w-full px-3 py-2.5 text-left transition-colors flex items-center gap-3 ${
                        index === selectedCommandIndex
                          ? "bg-gradient-to-r from-primary/10 to-primary-dark/10"
                          : ""
                      }`}
                      style={{
                        borderBottom: "1px solid var(--glass-border)",
                      }}
                    >
                      <span
                        style={{
                          color:
                            index === selectedCommandIndex
                              ? "var(--primary)"
                              : "var(--text-muted)",
                        }}
                      >
                        {cmd.icon}
                      </span>
                      <div className="flex-1">
                        <span
                          className="text-sm font-mono font-medium"
                          style={{
                            color:
                              index === selectedCommandIndex
                                ? "var(--primary)"
                                : "var(--text-primary)",
                          }}
                        >
                          {cmd.command}
                        </span>
                        <span
                          className="text-xs ml-2"
                          style={{ color: "var(--text-muted)" }}
                        >
                          {cmd.description}
                        </span>
                      </div>
                    </motion.button>
                  ))}
                  <div
                    className="px-3 py-1.5 text-xs"
                    style={{ color: "var(--text-muted)" }}
                  >
                    ↑↓ 选择 · Tab/Enter 确认 · Esc 关闭
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <motion.button
            type="submit"
            disabled={!canSend}
            whileHover={canSend ? { scale: 1.05 } : {}}
            whileTap={canSend ? { scale: 0.95 } : {}}
            className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-300 ${
              canSend
                ? "bg-gradient-to-r from-primary to-primary-dark text-white shadow-glow hover:shadow-glow-lg"
                : "bg-white/5 text-white/30 cursor-not-allowed"
            }`}
          >
            {disabled ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              >
                <Loader2 size={20} />
              </motion.div>
            ) : (
              <Send size={20} className={canSend ? "translate-x-0.5" : ""} />
            )}
          </motion.button>
        </motion.div>

        <div className="flex items-center justify-between mt-2 px-2">
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            按 Enter 发送，Shift+Enter 换行，输入 / 查看命令
          </span>
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            {message.length} 字符
          </span>
        </div>
      </form>
    </div>
  );
};

export default MessageInput;
