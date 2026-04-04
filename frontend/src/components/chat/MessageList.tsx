import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  Copy,
  Database,
  Loader2,
  RotateCcw,
  Save,
  Search,
  Sparkles,
  User,
  Wrench,
} from "lucide-react";

import type { AgentTraceEvent, KnowledgeHit, Message } from "../../types";
import CodeBlock from "./CodeBlock";

interface MessageListProps {
  messages: Message[];
  onCopyMessage?: (message: Message) => void | Promise<void>;
  onRegenerateMessage?: (message: Message) => void;
  onSaveAssistantMessage?: (message: Message) => void | Promise<void>;
  savingMessageId?: number | null;
  onRollbackMessage?: (message: Message) => void;
}

interface TraceDisplayItem {
  event: AgentTraceEvent;
  linkedToolResultContent?: string;
  knowledgeHits?: KnowledgeHit[];
}

const MessageAvatar = React.memo(({ role }: { role: "user" | "assistant" }) => (
  <div
    className={`message-avatar ${role === "user" ? "is-user" : "is-assistant"}`}
  >
    {role === "user" ? (
      <User size={20} style={{ color: "var(--text-primary)" }} />
    ) : (
      <Bot size={20} className="text-primary" />
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
    className="flex h-full items-center justify-center"
  >
    <div className="chat-empty-state">
      <motion.div
        animate={{ scale: [1, 1.04, 1] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        className="chat-empty-icon"
      >
        <Sparkles size={50} className="text-primary" />
      </motion.div>
      <h3
        className="mb-2 text-xl font-semibold"
        style={{ color: "var(--text-primary)" }}
      >
        开始一段新对话
      </h3>
      <p
        className="mx-auto max-w-xs text-sm"
        style={{ color: "var(--text-muted)" }}
      >
        这里适合研究、编码、分析和多步推理。
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

const formatToolName = (rawName: string): string => {
  if (rawName.startsWith("mcp__")) {
    const parts = rawName.split("__");
    // mcp__<server_id>__<tool_name> — 去掉前缀和 server_id，只显示工具原始名称
    return parts.slice(2).join("__") || rawName;
  }
  return rawName;
};

const extractToolResultContent = (rawContent: string): string => {
  try {
    const parsed = JSON.parse(rawContent);
    if (parsed && typeof parsed === "object" && "content" in parsed) {
      const inner = parsed.content;
      if (typeof inner === "string") return inner;
      return JSON.stringify(inner, null, 2);
    }
    return rawContent;
  } catch {
    return rawContent;
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
  content.replace(/^\s*关键信息[：:]\s*/gm, "").trim();

const buildTraceDisplayItems = (
  events: AgentTraceEvent[] = [],
): TraceDisplayItem[] => {
  const consumedToolResultIndexes = new Set<number>();
  const items: TraceDisplayItem[] = [];

  for (let index = 0; index < events.length; index += 1) {
    const event = events[index];

    if (event.type === "knowledge_hits") {
      items.push({ event, knowledgeHits: event.payload.hits });
      continue;
    }

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

const getTraceSummary = (item: TraceDisplayItem) => {
  const { event, linkedToolResultContent } = item;
  const linkedResultData = linkedToolResultContent
    ? parseToolResult(linkedToolResultContent)
    : null;
  const resultData =
    event.type === "tool_result"
      ? parseToolResult(event.payload.content)
      : null;

  if (event.type === "tool_call") {
    if (linkedResultData?.success) return "工具执行成功";
    if (linkedResultData?.error) return linkedResultData.error;
    if (event.payload.arguments) return "已发送工具参数";
  }

  if (event.type === "tool_result") {
    if (resultData?.success) return "工具执行成功";
    if (resultData?.error) return resultData.error;
    return "等待工具输出";
  }

  if (event.type === "knowledge_hits") {
    const count = item.knowledgeHits?.length || 0;
    return count > 0 ? `${count} 条相关记录` : "未命中记录";
  }

  return event.payload.message || event.payload.content || "执行活动";
};

const getTraceMeta = (item: TraceDisplayItem) => {
  const { event } = item;
  const resultData =
    event.type === "tool_result"
      ? parseToolResult(event.payload.content)
      : null;

  if (event.type === "reasoning") {
    return {
      icon: <Search size={18} className="text-primary" />,
      title: isPostToolReflection(event) ? "thinking" : "推理",
      tone: isPostToolReflection(event) ? "next" : "thinking",
    };
  }

  if (event.type === "tool_call") {
    return {
      icon: <Wrench size={18} className="text-primary" />,
      title: formatToolName(event.payload.tool_name || "工具调用"),
      tone: "tool",
    };
  }

  if (event.type === "tool_result") {
    return {
      icon: resultData?.success ? (
        <CheckCircle2 size={18} className="text-emerald-500" />
      ) : (
        <Loader2 size={18} className="text-primary" />
      ),
      title: "工具结果",
      tone: resultData?.success ? "success" : "tool",
    };
  }

  if (event.type === "knowledge_hits") {
    return {
      icon: <Database size={18} className="text-primary" />,
      title: "命中知识库",
      tone: "knowledge" as const,
    };
  }

  return {
    icon: <AlertTriangle size={18} className="text-amber-500" />,
    title: event.type === "progress_warning" ? "进度提醒" : "循环提醒",
    tone: "warning",
  };
};

const shouldExpandTraceEventByDefault = (item: TraceDisplayItem) => {
  const { event } = item;
  if (event.type === "reasoning") {
    return true;
  }
  if (event.type === "knowledge_hits") {
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
  item: TraceDisplayItem;
  index: number;
}> = ({ item, index }) => {
  const { event, linkedToolResultContent } = item;
  const [expanded, setExpanded] = useState(() =>
    shouldExpandTraceEventByDefault(item),
  );
  const meta = getTraceMeta(item);
  const summary = getTraceSummary(item);
  const linkedResultData = linkedToolResultContent
    ? parseToolResult(linkedToolResultContent)
    : null;
  const resultData =
    event.type === "tool_result"
      ? parseToolResult(event.payload.content)
      : null;
  const reasoningContent = normalizePostToolReflectionContent(
    event.payload.content || "",
  );

  return (
    <div className={`trace-line trace-line--${meta.tone}`}>
      <div className="trace-line__marker">
        <span className="trace-line__index">{index + 1}</span>
      </div>

      <div className="trace-line__body">
        {isPostToolReflection(event) ? (
          <div className="trace-line__header">
            <div className="trace-line__title-wrap">
              <span className="trace-line__icon">{meta.icon}</span>
              <div className="trace-line__copy">
                <div className="trace-line__title">{meta.title}</div>
                <div className="trace-line__summary">{summary}</div>
              </div>
            </div>
          </div>
        ) : (
          <>
            <button
              type="button"
              onClick={() => setExpanded((value) => !value)}
              className="trace-line__header"
            >
              <div className="trace-line__title-wrap">
                <span className="trace-line__icon">{meta.icon}</span>
                <div className="trace-line__copy">
                  <div className="trace-line__title">{meta.title}</div>
                  <div className="trace-line__summary">{summary}</div>
                </div>
              </div>
              <span className={`trace-line__toggle${expanded ? " trace-line__toggle--expanded" : ""}`} />
            </button>

            {expanded ? (
              <div className="trace-line__detail">
                {event.type === "reasoning" ? (
                  <div className="trace-event-content trace-event-reasoning">
                    {reasoningContent || "当前没有可展示的思考内容。"}
                  </div>
                ) : null}

                {event.type === "tool_call" ? (
                  <>
                    <pre className="trace-event-content overflow-x-auto text-xs">
                      {tryFormatJson(event.payload.arguments || "{}")}
                    </pre>
                    {linkedResultData?.execution_time_ms ? (
                      <div className="trace-line__meta">
                        执行耗时：{linkedResultData.execution_time_ms} ms
                      </div>
                    ) : null}
                    {linkedToolResultContent ? (
                      <pre className="trace-event-content trace-event-content--result max-h-80 overflow-x-auto text-xs">
                        {tryFormatJson(extractToolResultContent(linkedToolResultContent))}
                      </pre>
                    ) : null}
                  </>
                ) : null}

                {event.type === "tool_result" ? (
                  <>
                    {resultData?.execution_time_ms ? (
                      <div className="trace-line__meta">
                        执行耗时：{resultData.execution_time_ms} ms
                      </div>
                    ) : null}
                    <pre className="trace-event-content trace-event-content--result max-h-80 overflow-x-auto text-xs">
                      {tryFormatJson(extractToolResultContent(event.payload.content || ""))}
                    </pre>
                  </>
                ) : null}

                {event.type === "progress_warning" ||
                event.type === "loop_warning" ? (
                  <div className="trace-event-content whitespace-pre-wrap text-sm">
                    {event.payload.message ||
                      "检测到最近进展有限，智能体已经调整执行策略。"}
                  </div>
                ) : null}

                {event.type === "knowledge_hits" ? (
                  <div className="trace-event-content">
                    {item.knowledgeHits?.map((hit, i) => (
                      <div
                        key={`${hit.memory_id || "knowledge"}-${i}`}
                        className="trace-event-knowledge"
                      >
                        <div className="trace-event-knowledge__title">
                          {hit.title || "知识片段"}
                        </div>
                        <div className="trace-event-knowledge__snippet">
                          {summarizeKnowledgeHit(hit.content)}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
};

const AssistantTraceTimeline: React.FC<{
  traceEvents?: AgentTraceEvent[];
  isStreaming?: boolean;
}> = ({ traceEvents, isStreaming }) => {
  const items = useMemo(
    () => buildTraceDisplayItems(traceEvents || []),
    [traceEvents],
  );

  if (items.length === 0 && !isStreaming) {
    return null;
  }

  return (
    <div className="assistant-trace">
      <div className="assistant-trace__timeline">
        {items.map((item, index) => (
          <TraceEventCard key={item.event.id} item={item} index={index} />
        ))}
        {isStreaming && items.length === 0 ? null : null}
      </div>
    </div>
  );
};

const summarizeKnowledgeHit = (content: string) =>
  content.replace(/\s+/g, " ").trim().slice(0, 120);

const AssistantResponseBlock: React.FC<{
  message: Message;
  isStreaming?: boolean;
  isLastAssistant?: boolean;
  onCopy?: (message: Message) => void | Promise<void>;
  onRegenerate?: (message: Message) => void;
  onSaveAssistantMessage?: (message: Message) => void | Promise<void>;
  savingMessageId?: number | null;
}> = ({
  message,
  isStreaming,
  isLastAssistant,
  onCopy,
  onRegenerate,
  onSaveAssistantMessage,
  savingMessageId,
}) => {
  const isSaving = savingMessageId === message.id;

  if (message.content === "") {
    return isStreaming ? (
      <div className="assistant-response assistant-response--pending">
        <TypingIndicator />
      </div>
    ) : null;
  }

  return (
    <div className="assistant-response">
      <AssistantMarkdownBody content={message.content} />
      {!isStreaming ? (
        <div className="assistant-response__footer">
          <button
            type="button"
            className="assistant-action-icon"
            onClick={() => void onCopy?.(message)}
            disabled={!onCopy}
            title="复制"
            aria-label="复制"
          >
            <Copy size={18} />
          </button>
          {isLastAssistant ? (
            <button
              type="button"
              className="assistant-action-icon"
              onClick={() => onRegenerate?.(message)}
              disabled={!onRegenerate}
              title="重新执行"
              aria-label="重新执行"
            >
              <RotateCcw size={18} />
            </button>
          ) : null}
          <button
            type="button"
            className="assistant-action-icon"
            onClick={() => void onSaveAssistantMessage?.(message)}
            disabled={!onSaveAssistantMessage || isSaving}
            title={isSaving ? "正在保存到知识库" : "保存到知识库"}
            aria-label={isSaving ? "正在保存到知识库" : "保存到知识库"}
          >
            {isSaving ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <Save size={18} />
            )}
          </button>
        </div>
      ) : null}
    </div>
  );
};

const MessageList: React.FC<MessageListProps> = ({
  messages,
  onCopyMessage,
  onRegenerateMessage,
  onSaveAssistantMessage,
  savingMessageId,
  onRollbackMessage,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const isInitialLoad = useRef(true);

  const lastAssistantId = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      if (messages[i].role === "assistant") return messages[i].id;
    }
    return null;
  }, [messages]);

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
            {message.role === "user" ? (
              <div className="message-shell is-user">
                <div className="message-meta">
                  <span className="message-time">
                    {new Date(message.created_at).toLocaleString("zh-CN", {
                      hour: "2-digit",
                      minute: "2-digit",
                      hour12: false,
                    })}
                  </span>
                  <div className="message-meta-main">
                    <MessageAvatar role="user" />
                  </div>
                </div>
                <div className="message-bubble message-user">
                  <button
                    type="button"
                    className="rollback-button"
                    onClick={() => onRollbackMessage?.(message)}
                    title="回滚到此消息之前"
                    aria-label="回滚到此消息之前"
                  >
                    <RotateCcw size={18} />
                  </button>
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                </div>
              </div>
            ) : (
              <div className="message-shell is-assistant">
                <div className="message-bubble message-ai">
                  <AssistantTraceTimeline
                    traceEvents={message.traceEvents}
                    isStreaming={message.isStreaming}
                  />
                  <AssistantResponseBlock
                    message={message}
                    isStreaming={message.isStreaming}
                    isLastAssistant={message.id === lastAssistantId}
                    onCopy={onCopyMessage}
                    onRegenerate={onRegenerateMessage}
                    onSaveAssistantMessage={onSaveAssistantMessage}
                    savingMessageId={savingMessageId}
                  />
                </div>
              </div>
            )}
          </motion.div>
        ))
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
