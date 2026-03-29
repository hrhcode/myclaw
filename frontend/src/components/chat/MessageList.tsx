import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import { Bot, User, Sparkles, Wrench, CheckCircle, XCircle, Loader2, ChevronDown, ChevronUp } from "lucide-react";
import React, { useState } from "react";
import type { Message, ToolCallInfo, ToolResultInfo } from "../../types";
import CodeBlock from "./CodeBlock";

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
 * 打字指示器组件
 */
const TypingIndicator: React.FC = () => (
  <div className="typing-indicator">
    <span></span>
    <span></span>
    <span></span>
  </div>
);

/**
 * 空状态组件
 */
const EmptyState: React.FC = () => (
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

/**
 * 工具调用卡片组件
 */
const ToolCallCard: React.FC<{
  call: ToolCallInfo;
  result?: ToolResultInfo;
}> = ({ call, result }) => {
  const [expanded, setExpanded] = useState(false);

  const parseResult = (): { success?: boolean; content?: unknown; error?: string; execution_time_ms?: number } | null => {
    if (!result?.content) return null;
    try {
      return JSON.parse(result.content);
    } catch {
      return { content: result.content };
    }
  };

  const resultData = parseResult();
  const isSuccess = resultData?.success;

  return (
    <motion.div
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card rounded-lg overflow-hidden text-sm"
      style={{ border: "1px solid var(--glass-border)" }}
    >
      <div
        className="flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-white/5"
        onClick={() => setExpanded(!expanded)}
        style={{ background: "var(--glass-bg)" }}
      >
        <div className="flex items-center gap-2">
          <Wrench size={14} className="text-primary" />
          <span className="font-medium" style={{ color: "var(--text-primary)" }}>
            {call.toolName}
          </span>
          {result ? (
            isSuccess ? (
              <CheckCircle size={14} className="text-green-500" />
            ) : (
              <XCircle size={14} className="text-red-500" />
            )
          ) : (
            <Loader2 size={14} className="animate-spin text-primary" />
          )}
        </div>
        {expanded ? (
          <ChevronUp size={14} style={{ color: "var(--text-muted)" }} />
        ) : (
          <ChevronDown size={14} style={{ color: "var(--text-muted)" }} />
        )}
      </div>

      {expanded && (
        <div className="px-3 py-2 space-y-2" style={{ background: "var(--bg-secondary)" }}>
          <div>
            <div className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>
              参数
            </div>
            <pre
              className="text-xs p-2 rounded overflow-x-auto"
              style={{
                background: "var(--glass-bg)",
                color: "var(--text-primary)",
                border: "1px solid var(--glass-border)"
              }}
            >
              {(() => {
                try {
                  return JSON.stringify(JSON.parse(call.arguments || '{}'), null, 2);
                } catch {
                  return call.arguments || '{}';
                }
              })()}
            </pre>
          </div>

          {result && resultData && (
            <div>
              <div className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>
                结果
              </div>
              <pre
                className="text-xs p-2 rounded overflow-x-auto max-h-40"
                style={{
                  background: isSuccess ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                  color: isSuccess ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
                  border: `1px solid ${isSuccess ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                }}
              >
                {resultData.content
                  ? JSON.stringify(resultData.content, null, 2)
                  : resultData.error || '未知结果'}
              </pre>
            </div>
          )}

          {resultData?.execution_time_ms && (
            <div className="text-xs" style={{ color: "var(--text-muted)" }}>
              执行时间: {resultData.execution_time_ms}ms
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
};

/**
 * 工具调用列表组件
 */
const ToolCallsDisplay: React.FC<{
  toolCalls?: ToolCallInfo[];
  toolResults?: Map<string, ToolResultInfo>;
}> = ({ toolCalls, toolResults }) => {
  if (!toolCalls || toolCalls.length === 0) return null;

  return (
    <div className="mb-2 space-y-2">
      {toolCalls.map((call) => (
        <ToolCallCard
          key={call.toolCallId}
          call={call}
          result={toolResults?.get(call.toolCallId)}
        />
      ))}
    </div>
  );
};

/**
 * 消息列表组件 - 显示对话中的所有消息
 * 采用玻璃拟态设计，支持动画效果和主题切换
 */
const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {messages.length === 0 ? (
        <EmptyState />
      ) : (
        messages.map((message) => (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.2,
              ease: [0.4, 0, 0.2, 1],
            }}
            className={`flex gap-3 ${
              message.role === "user" ? "flex-row-reverse" : "flex-row"
            }`}
          >
            <MessageAvatar role={message.role} />

            <div
              className={`max-w-[75%] flex flex-col ${
                message.role === "user" ? "items-end" : "items-start"
              }`}
            >
              <div
                className={`message-bubble ${
                  message.role === "user" ? "message-user" : "message-ai"
                }`}
              >
                {message.role === "assistant" && (
                  <ToolCallsDisplay
                    toolCalls={message.toolCalls}
                    toolResults={message.toolResults}
                  />
                )}
                
                {message.content === "" ? (
                  <TypingIndicator />
                ) : (
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown
                      components={
                        {
                          pre({ children }) {
                            return <>{children}</>;
                          },
                          code({ className, children, ...props }) {
                            const match = /language-(\w+)/.exec(
                              className || "",
                            );
                            const language = match ? match[1] : "";
                            const value = String(children).replace(/\n$/, "");

                            if (language) {
                              return (
                                <CodeBlock language={language} value={value} />
                              );
                            }

                            return (
                              <code className={className} {...props}>
                                {children}
                              </code>
                            );
                          },
                        } satisfies Components
                      }
                    >
                      {message.content}
                    </ReactMarkdown>
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
            </div>
          </motion.div>
        ))
      )}
    </div>
  );
};

export default MessageList;
