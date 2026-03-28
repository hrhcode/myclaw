/**
 * WebSocket 日志连接管理 Hook
 */
import { useEffect, useRef, useCallback, useState } from "react";

export interface LogEntry {
  timestamp: string;
  level: string;
  logger: string;
  message: string;
  extra?: Record<string, unknown>;
}

interface UseLogWebSocketOptions {
  url: string;
  onLog?: (log: LogEntry) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

interface UseLogWebSocketReturn {
  isConnected: boolean;
  connectionStatus: "connecting" | "connected" | "disconnected" | "error";
  connect: () => void;
  disconnect: () => void;
  sendFilter: (level: string) => void;
}

/**
 * WebSocket 日志连接管理 Hook
 * 
 * @param options 配置选项
 * @returns 连接状态和控制方法
 */
export function useLogWebSocket(options: UseLogWebSocketOptions): UseLogWebSocketReturn {
  const {
    url,
    onLog,
    onConnect,
    onDisconnect,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const shouldReconnectRef = useRef(true);
  const mountedRef = useRef(false);

  const [connectionStatus, setConnectionStatus] = useState<"connecting" | "connected" | "disconnected" | "error">("disconnected");

  const isConnected = connectionStatus === "connected";

  /**
   * 清除重连定时器
   */
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  /**
   * 断开 WebSocket 连接
   */
  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    clearReconnectTimeout();

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setConnectionStatus("disconnected");
  }, [clearReconnectTimeout]);

  /**
   * 建立 WebSocket 连接
   */
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    clearReconnectTimeout();
    setConnectionStatus("connecting");

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnectionStatus("connected");
        reconnectAttemptsRef.current = 0;
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "log" && data.data) {
            onLog?.(data.data as LogEntry);
          }
        } catch {
          // 忽略解析错误
        }
      };

      ws.onclose = () => {
        setConnectionStatus("disconnected");
        onDisconnect?.();

        if (shouldReconnectRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            // 检查连接状态后重新连接
            if (shouldReconnectRef.current) {
              const currentWs = wsRef.current;
              if (currentWs === null || currentWs.readyState === WebSocket.CLOSED) {
                // 重新创建连接
                try {
                  const newWs = new WebSocket(url);
                  wsRef.current = newWs;
                  setConnectionStatus("connecting");

                  newWs.onopen = ws.onopen;
                  newWs.onmessage = ws.onmessage;
                  newWs.onclose = ws.onclose;
                  newWs.onerror = ws.onerror;
                } catch {
                  setConnectionStatus("error");
                }
              }
            }
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        setConnectionStatus("error");
        onError?.(error);
      };
    } catch {
      setConnectionStatus("error");
    }
  }, [url, onConnect, onDisconnect, onError, onLog, clearReconnectTimeout, reconnectInterval, maxReconnectAttempts]);

  /**
   * 发送过滤级别
   */
  const sendFilter = useCallback((level: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: "filter",
        level,
      }));
    }
  }, []);

  /**
   * 初始化连接 - 使用 setTimeout 避免同步调用 setState
   */
  useEffect(() => {
    mountedRef.current = true;
    shouldReconnectRef.current = true;

    // 使用 setTimeout 延迟连接，避免在 effect 中同步调用 setState
    const initTimeout = setTimeout(() => {
      if (mountedRef.current) {
        connect();
      }
    }, 0);

    return () => {
      mountedRef.current = false;
      clearTimeout(initTimeout);
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    connectionStatus,
    connect,
    disconnect,
    sendFilter,
  };
}
