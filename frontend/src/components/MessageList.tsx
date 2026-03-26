import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import { Bot, User, Sparkles } from "lucide-react";
import React from "react";
import type { Message } from "../types";

interface MessageListProps {
  messages: Message[];
}

/**
 * 消息头像组件 - 使用 React.memo 防止流式输出时不必要的重新渲染
 */
const MessageAvatar = React.memo(({ role }: { role: "user" | "assistant" }) => (
  <div
    className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
      role === "user"
        ? "bg-gradient-to-br from-primary to-primary-dark"
        : "glass border border-[var(--glass-border)]"
    }`}
  >
    {role === "user" ? (
      <User size={16} className="text-white" />
    ) : (
      <Bot size={16} className="text-primary" />
    )}
  </div>
));

MessageAvatar.displayName = "MessageAvatar";

/**
 * 消息列表组件 - 显示对话中的所有消息
 * 采用玻璃拟态设计，支持动画效果和主题切换
 */
const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  /**
   * 渲染打字指示器
   */
  const TypingIndicator = () => (
    <div className="typing-indicator">
      <span></span>
      <span></span>
      <span></span>
    </div>
  );

  /**
   * 渲染空状态
   */
  const EmptyState = () => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="h-full flex items-center justify-center"
    >
      <div className="text-center">
        <motion.div
          animate={{
            scale: [1, 1.1, 1],
            rotate: [0, 5, -5, 0],
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="w-24 h-24 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-primary/20 to-primary-dark/20 flex items-center justify-center border border-[var(--glass-border)]"
        >
          <Sparkles size={40} className="text-primary" />
        </motion.div>
        <h3
          className="text-xl font-semibold mb-2"
          style={{ color: "var(--text-primary)" }}
        >
          开始新的对话
        </h3>
        <p
          className="text-sm max-w-xs mx-auto"
          style={{ color: "var(--text-muted)" }}
        >
          输入消息开始与AI助手对话，探索无限可能
        </p>
      </div>
    </motion.div>
  );

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      <AnimatePresence mode="popLayout">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          messages.map((message, index) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{
                duration: 0.3,
                delay: index * 0.05,
                ease: [0.4, 0, 0.2, 1],
              }}
              className={`flex gap-3 ${
                message.role === "user" ? "flex-row-reverse" : "flex-row"
              }`}
            >
              <MessageAvatar role={message.role} />

              <motion.div
                initial={{
                  opacity: 0,
                  x: message.role === "user" ? 20 : -20,
                }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: 0.1 }}
                className={`max-w-[75%] flex flex-col ${
                  message.role === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`message-bubble ${
                    message.role === "user" ? "message-user" : "message-ai"
                  }`}
                >
                  {message.content === "" ? (
                    <TypingIndicator />
                  ) : (
                    <div className="prose prose-sm max-w-none">
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                  )}
                </div>

                <div
                  className={`text-xs mt-1.5 ${
                    message.role === "user" ? "text-right" : "text-left"
                  }`}
                  style={{ color: "var(--text-muted)" }}
                >
                  {new Date(message.created_at).toLocaleTimeString("zh-CN", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </div>
              </motion.div>
            </motion.div>
          ))
        )}
      </AnimatePresence>
    </div>
  );
};

export default MessageList;
