﻿import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import {
  Bot,
  Loader2,
  Search,
  Sparkles,
  User,
  Wrench,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import React, { useState, useEffect, useRef, useCallback } from "react";
import type { AgentTraceEvent, Message } from "../../types";
import CodeBlock from "./CodeBlock";

interface MessageListProps {
  messages: Message[];
}

interface TraceDisplayItem {
  event: AgentTraceEvent;
  linkedToolResultContent?: string;
}

const MessageAvatar = React.memo(({ role }: { role: "user" | "assistant" }) => (
  <div
    className={`message-avatar ${role === "user" ? "is-user" : "is-assistant"}`}
  >
    {role === "user" ? (
      <User size={16} style={{ color: "var(--text-primary)" }} />
    ) : (
      <Bot size={16} className="text-primary" />
    )}
  </div>
));

MessageAvatar.displayName = "MessageAvatar";

const TypingIndicator: React.FC = () => (
  <div className="typing-indicator">
    <span></span>
    <span></span>
    <span></span>
  </div>
);

const EmptyState: React.FC = () => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5 }}
    className="h-full flex items-center justify-center"
  >
    <div className="chat-empty-state">
      <motion.div
        animate={{ scale: [1, 1.04, 1] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        className="chat-empty-icon"
      >
        <Sparkles size={40} className="text-primary" />
      </motion.div>
      <h3
        className="text-xl font-semibold mb-2"
        style={{ color: "var(--text-primary)" }}
      >
        开始一段新的对话
      </h3>
      <p
        className="text-sm max-w-xs mx-auto"
        style={{ color: "var(--text-muted)" }}
      >
        这里适合研究、编码、分析和多步骤推理。智能体
        的回复与执行轨迹会保持清晰、克制地展开。
      </p>
    </div>
  </motion.div>
);

const tryFormatJson = (value?: string) => {
  if (!value) {
    return "";
  }

  try {
    return JSON.stringify(JSON.parse(value), null, 2);
  } catch {
    return value;
  }
};

const parseToolResult = (value?: string) => {
  if (!value) {
    return null;
  }

  try {
    return JSON.parse(value) as {
      success?: boolean;
      error?: string;
      execution_time_ms?: number;
      content?: unknown;
    };
  } catch {
    return { content: value };
  }
};

const isPostToolReflection = (event: AgentTraceEvent) =>
  event.type === "reasoning" && event.payload.phase === "post_tool_reflection";

const normalizePostToolReflectionContent = (content: string) =>
  content.replace(/^\s*关键信息[：:]\s*/gm, "");

const buildTraceDisplayItems = (
  events: AgentTraceEvent[] = [],
): TraceDisplayItem[] => {
  const consumedToolResultIndexes = new Set<number>();
  const items: TraceDisplayItem[] = [];

  for (let index = 0; index < events.length; index += 1) {
    const event = events[index];

    if (event.type === "tool_result" && consumedToolResultIndexes.has(index)) {
      continue;
    }

    if (event.type === "tool_call") {
      const matchedIndex = events.findIndex(
        (candidate, candidateIndex) =>
          candidateIndex > index &&
          !consumedToolResultIndexes.has(candidateIndex) &&
          candidate.type === "tool_result" &&
          candidate.payload.tool_call_id &&
          candidate.payload.tool_call_id === event.payload.tool_call_id,
      );

      if (matchedIndex !== -1) {
        consumedToolResultIndexes.add(matchedIndex);
        items.push({
          event,
          linkedToolResultContent: events[matchedIndex].payload.content,
        });
        continue;
      }
    }

    items.push({ event });
  }

  return items;
};

const AssistantMarkdownBody: React.FC<{ content: string }> = ({ content }) => (
  <div className="prose prose-sm max-w-none assistant-prose">
    <ReactMarkdown
      components={
        {
          pre({ children }) {
            return <>{children}</>;
          },
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            const language = match ? match[1] : "";
            const value = String(children).replace(/\n$/, "");

            if (language) {
              return <CodeBlock language={language} value={value} />;
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
      {content}
    </ReactMarkdown>
  </div>
);

const shouldExpandTraceEventByDefault = (event: AgentTraceEvent) => {
  if (event.type === "reasoning") {
    return true;
  }

  if (event.type === "tool_call") {
    return false;
  }

  if (event.type === "tool_result") {
    const result = parseToolResult(event.payload.content);
    return result?.success === false;
  }

  return true;
};

const TraceEventCard: React.FC<{
  event: AgentTraceEvent;
  linkedToolResultContent?: string;
}> = ({ event, linkedToolResultContent }) => {
  const [expanded, setExpanded] = useState(() =>
    shouldExpandTraceEventByDefault(event),
  );
  const resultData =
    event.type === "tool_result"
      ? parseToolResult(event.payload.content)
      : null;
  const linkedResultData = linkedToolResultContent
    ? parseToolResult(linkedToolResultContent)
    : null;

  const meta = {
    reasoning: {
      icon: <Search size={14} className="text-primary" />,
      label: "思考",
      accent: "rgba(59, 130, 246, 0.08)",
    },
    tool_call: {
      icon: <Wrench size={14} className="text-primary" />,
      label: event.payload.tool_name || "工具调用",
      accent: "rgba(14, 165, 233, 0.06)",
    },
    tool_result: {
      icon: resultData?.success ? (
        <CheckCircle2 size={14} className="text-emerald-500" />
      ) : (
        <Loader2 size={14} className="text-primary" />
      ),
      label: "工具结果",
      accent: resultData?.success
        ? "rgba(16, 185, 129, 0.06)"
        : "rgba(249, 115, 22, 0.08)",
    },
    progress_warning: {
      icon: <AlertTriangle size={14} className="text-amber-500" />,
      label: "进度提醒",
      accent: "rgba(245, 158, 11, 0.08)",
    },
    loop_warning: {
      icon: <AlertTriangle size={14} className="text-rose-500" />,
      label: "循环提醒",
      accent: "rgba(244, 63, 94, 0.08)",
    },
  }[event.type];

  return (
    <div
      className="trace-event-card"
      style={{
        background: `linear-gradient(180deg, ${meta.accent}, transparent)`,
      }}
    >
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="w-full flex items-center justify-between px-4 py-3 text-left"
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="trace-event-icon">{meta.icon}</div>
          <div className="min-w-0">
            <div
              className="text-sm font-medium truncate"
              style={{ color: "var(--text-primary)" }}
            >
              {meta.label}
            </div>
            <div
              className="text-xs truncate"
              style={{ color: "var(--text-muted)" }}
            >
              {event.type === "tool_call" && event.payload.arguments
                ? linkedResultData
                  ? linkedResultData.success
                    ? "工具执行成功"
                    : linkedResultData.error || "工具执行失败"
                  : tryFormatJson(event.payload.arguments)
                : event.type === "tool_result"
                  ? resultData?.success
                    ? "工具执行成功"
                    : resultData?.error || "等待工具输出"
                  : event.payload.message ||
                    event.payload.content ||
                    "执行活动"}
            </div>
          </div>
        </div>
        <span className="trace-event-toggle">{expanded ? "收起" : "展开"}</span>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-3">
          {event.type === "reasoning" && (
            <div className="trace-event-content trace-event-reasoning">
              {event.payload.content || "当前没有可展示的思考内容。"}
            </div>
          )}

          {event.type === "tool_call" && (
            <>
              <pre className="trace-event-content text-xs overflow-x-auto">
                {tryFormatJson(event.payload.arguments || "{}")}
              </pre>
              {linkedResultData ? (
                <>
                  {linkedResultData.execution_time_ms ? (
                    <div
                      className="text-xs"
                      style={{ color: "var(--text-muted)" }}
                    >
                      执行耗时：{linkedResultData.execution_time_ms} ms
                    </div>
                  ) : null}
                  <pre className="trace-event-content text-xs overflow-x-auto max-h-80">
                    {tryFormatJson(linkedToolResultContent || "")}
                  </pre>
                </>
              ) : null}
            </>
          )}

          {event.type === "tool_result" && (
            <>
              {resultData?.execution_time_ms ? (
                <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                  执行耗时：{resultData.execution_time_ms} ms
                </div>
              ) : null}
              <pre className="trace-event-content text-xs overflow-x-auto max-h-80">
                {tryFormatJson(event.payload.content || "")}
              </pre>
            </>
          )}

          {(event.type === "progress_warning" ||
            event.type === "loop_warning") && (
            <div className="trace-event-content text-sm whitespace-pre-wrap">
              {event.payload.message || "检测到进展停滞后，智能体已调整执行策略。"}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const isInitialLoad = useRef(true);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  }, []);

  const handleScroll = useCallback(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    const { scrollTop, scrollHeight, clientHeight } = container;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
    setShouldAutoScroll(isNearBottom);
  }, []);

  useEffect(() => {
    if (messages.length > 0 && isInitialLoad.current) {
      setTimeout(() => {
        scrollToBottom("instant");
        isInitialLoad.current = false;
      }, 100);
    }
  }, [messages.length, scrollToBottom]);

  useEffect(() => {
    if (shouldAutoScroll && messages.length > 0) {
      scrollToBottom("smooth");
    }
  }, [messages, shouldAutoScroll, scrollToBottom]);

  return (
    <div ref={containerRef} className="message-thread" onScroll={handleScroll}>
      {messages.length === 0 ? (
        <EmptyState />
      ) : (
        messages.map((message) => (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
            className={`message-row ${message.role === "user" ? "is-user" : "is-assistant"}`}
          >
            <div
              className={`message-shell ${message.role === "user" ? "is-user" : "is-assistant"}`}
            >
              <div className="message-meta">
                <div className="message-meta-main">
                  <MessageAvatar role={message.role} />
                  <span className="message-role-label">
                    {message.role === "user" ? "你" : "智能体"}
                  </span>
                </div>
                <span className="message-time">
                  {new Date(message.created_at).toLocaleTimeString("zh-CN", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>

              <div
                className={`message-bubble ${message.role === "user" ? "message-user" : "message-ai"}`}
              >
                {message.role === "assistant" && (
                  <div className="trace-inline-list">
                    {buildTraceDisplayItems(message.traceEvents || []).map(
                      (item) =>
                        isPostToolReflection(item.event) ? (
                          <AssistantMarkdownBody
                            key={item.event.id}
                            content={normalizePostToolReflectionContent(
                              item.event.payload.content || "",
                            )}
                          />
                        ) : (
                          <TraceEventCard
                            key={item.event.id}
                            event={item.event}
                            linkedToolResultContent={
                              item.linkedToolResultContent
                            }
                          />
                        ),
                    )}
                    {message.isStreaming &&
                    (buildTraceDisplayItems(message.traceEvents || []).length ||
                      0) === 0 ? (
                      <div className="trace-inline-pending">
                        <Loader2 size={14} className="animate-spin" />
                        <span>智能体正在准备执行步骤…</span>
                      </div>
                    ) : null}
                  </div>
                )}

                {message.content === "" ? (
                  <TypingIndicator />
                ) : message.role === "assistant" ? (
                  <AssistantMarkdownBody content={message.content} />
                ) : (
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        ))
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
