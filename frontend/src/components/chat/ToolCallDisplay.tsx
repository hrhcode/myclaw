/**
 * 工具调用展示组件
 * 
 * 在聊天消息中展示工具调用的状态和结果
 */
import { motion, AnimatePresence } from 'framer-motion';
import { Wrench, CheckCircle, XCircle, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

export interface ToolCallData {
  toolName: string;
  toolCallId: string;
  arguments: string;
}

export interface ToolResultData {
  toolCallId: string;
  content: string;
}

interface ToolCallDisplayProps {
  toolCalls: ToolCallData[];
  toolResults: Map<string, ToolResultData>;
}

/**
 * 单个工具调用卡片
 */
const ToolCallCard: React.FC<{
  call: ToolCallData;
  result?: ToolResultData;
}> = ({ call, result }) => {
  const [expanded, setExpanded] = useState(false);

  const parseResult = () => {
    if (!result?.content) return null;
    try {
      return JSON.parse(result.content);
    } catch {
      return { raw: result.content };
    }
  };

  const resultData = parseResult();
  const isSuccess = resultData?.success;

  return (
    <motion.div
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card rounded-lg overflow-hidden"
      style={{ border: '1px solid var(--glass-border)' }}
    >
      {/* 工具调用头部 */}
      <div
        className="flex items-center justify-between px-3 py-2 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
        style={{ background: 'var(--glass-bg)' }}
      >
        <div className="flex items-center gap-2">
          <Wrench size={14} className="text-primary" />
          <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
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
          <ChevronUp size={14} style={{ color: 'var(--text-muted)' }} />
        ) : (
          <ChevronDown size={14} style={{ color: 'var(--text-muted)' }} />
        )}
      </div>

      {/* 展开详情 */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-3 py-2 space-y-2" style={{ background: 'var(--bg-secondary)' }}>
              {/* 参数 */}
              <div>
                <div className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>
                  参数
                </div>
                <pre
                  className="text-xs p-2 rounded overflow-x-auto"
                  style={{
                    background: 'var(--glass-bg)',
                    color: 'var(--text-primary)',
                    border: '1px solid var(--glass-border)'
                  }}
                >
                  {JSON.stringify(JSON.parse(call.arguments || '{}'), null, 2)}
                </pre>
              </div>

              {/* 结果 */}
              {result && (
                <div>
                  <div className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>
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
                    {resultData?.content
                      ? JSON.stringify(resultData.content, null, 2)
                      : resultData?.error || '未知结果'}
                  </pre>
                </div>
              )}

              {/* 执行时间 */}
              {resultData?.execution_time_ms && (
                <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  执行时间: {resultData.execution_time_ms}ms
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

/**
 * 工具调用展示组件
 */
const ToolCallDisplay: React.FC<ToolCallDisplayProps> = ({ toolCalls, toolResults }) => {
  if (toolCalls.length === 0) return null;

  return (
    <div className="mb-2 space-y-2">
      {toolCalls.map((call) => (
        <ToolCallCard
          key={call.toolCallId}
          call={call}
          result={toolResults.get(call.toolCallId)}
        />
      ))}
    </div>
  );
};

export default ToolCallDisplay;
