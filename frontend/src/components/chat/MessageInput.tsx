import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Command, Loader2, PlusCircle, SendHorizonal } from "lucide-react";

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  onCreateNewChat?: () => void;
}

interface CommandItem {
  command: string;
  description: string;
  icon: React.ReactNode;
}

const COMMANDS: CommandItem[] = [
  {
    command: "/new",
    description: "创建一个新会话",
    icon: <PlusCircle size={15} />,
  },
];

const MessageInput: React.FC<MessageInputProps> = ({
  onSendMessage,
  disabled = false,
  onCreateNewChat: _onCreateNewChat,
}) => {
  const [message, setMessage] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [showCommands, setShowCommands] = useState(false);
  const [selectedCommandIndex, setSelectedCommandIndex] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const filteredCommands = message.startsWith("/")
    ? COMMANDS.filter((cmd) =>
        cmd.command.toLowerCase().startsWith(message.toLowerCase()),
      )
    : [];

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) {
      return;
    }

    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 220)}px`;
  }, [message]);

  useEffect(() => {
    if (message.startsWith("/")) {
      setShowCommands(true);
      setSelectedCommandIndex(0);
      return;
    }

    setShowCommands(false);
  }, [message]);

  const selectCommand = (cmd: CommandItem) => {
    setMessage(`${cmd.command} `);
    setShowCommands(false);
    textareaRef.current?.focus();
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();

    if (!message.trim() || disabled) {
      return;
    }

    onSendMessage(message.trim());
    setMessage("");
    setShowCommands(false);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (showCommands && filteredCommands.length > 0) {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setSelectedCommandIndex((prev) =>
          prev < filteredCommands.length - 1 ? prev + 1 : 0,
        );
        return;
      }

      if (event.key === "ArrowUp") {
        event.preventDefault();
        setSelectedCommandIndex((prev) =>
          prev > 0 ? prev - 1 : filteredCommands.length - 1,
        );
        return;
      }

      if (event.key === "Tab" || (event.key === "Enter" && !event.shiftKey)) {
        event.preventDefault();
        selectCommand(filteredCommands[selectedCommandIndex]);
        return;
      }

      if (event.key === "Escape") {
        setShowCommands(false);
        return;
      }
    }

    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit(event);
    }
  };

  const canSend = Boolean(message.trim()) && !disabled;

  return (
    <div className="chat-composer-wrap">
      <form onSubmit={handleSubmit} className="chat-composer relative">
        <motion.div
          animate={{
            borderColor: isFocused
              ? "var(--accent-soft)"
              : "var(--panel-border)",
            boxShadow: isFocused
              ? "0 0 0 1px var(--accent-soft), var(--shadow-md)"
              : "var(--shadow-sm)",
          }}
          transition={{ duration: 0.18 }}
          className="chat-composer-shell"
        >
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="给智能体发送消息，回车发送，Shift + 回车换行"
            disabled={disabled}
            rows={1}
            className="chat-composer-input"
          />

          <div className="chat-composer-footer">
            <div className="chat-composer-hint">
              <Command size={14} />
              <span>输入 `/` 查看快捷命令</span>
            </div>

            <div className="chat-composer-actions">
              <span className="chat-composer-count">{message.length}</span>
              <motion.button
                type="submit"
                disabled={!canSend}
                whileHover={canSend ? { scale: 1.03 } : {}}
                whileTap={canSend ? { scale: 0.97 } : {}}
                className={`chat-send-button ${canSend ? "is-ready" : ""}`}
                aria-label={disabled ? "正在发送消息" : "发送消息"}
              >
                {disabled ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <SendHorizonal size={16} />
                )}
              </motion.button>
            </div>
          </div>
        </motion.div>

        <AnimatePresence>
          {showCommands && filteredCommands.length > 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              transition={{ duration: 0.15 }}
              className="command-panel"
            >
              <div className="command-panel-header">快捷命令</div>
              {filteredCommands.map((cmd, index) => (
                <button
                  key={cmd.command}
                  type="button"
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => selectCommand(cmd)}
                  className={`command-panel-item ${index === selectedCommandIndex ? "is-selected" : ""}`}
                >
                  <span className="command-panel-icon">{cmd.icon}</span>
                  <span className="command-panel-command">{cmd.command}</span>
                  <span className="command-panel-description">
                    {cmd.description}
                  </span>
                </button>
              ))}
              <div className="command-panel-footer">
                上下选择，Tab 或 Enter 确认
              </div>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </form>
    </div>
  );
};

export default MessageInput;
