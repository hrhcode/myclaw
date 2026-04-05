/**
 * Gateway WebSocket 连接管理 Hook
 *
 * 实时接收通道消息事件（incoming / reply）。
 */
import { useEffect, useRef, useCallback, useState } from "react";

export interface GatewayEvent {
  type: "incoming" | "reply";
  conversation_id?: number | null;
  channel_id: number;
  channel_type: string;
  chat_id: string;
  chat_type: string;
  user_id?: string;
  user_name?: string;
  text: string;
}

interface UseGatewayWebSocketOptions {
  onEvent?: (event: GatewayEvent) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

interface UseGatewayWebSocketReturn {
  isConnected: boolean;
  connectionStatus: "connecting" | "connected" | "disconnected" | "error";
}

export function useGatewayWebSocket(
  options: UseGatewayWebSocketOptions = {},
): UseGatewayWebSocketReturn {
  const {
    onEvent,
    onConnect,
    onDisconnect,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );
  const shouldReconnectRef = useRef(true);
  const mountedRef = useRef(false);

  const [connectionStatus, setConnectionStatus] = useState<
    "connecting" | "connected" | "disconnected" | "error"
  >("disconnected");

  const isConnected = connectionStatus === "connected";

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const getWsUrl = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}/api/gateway/ws`;
  }, []);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    clearReconnectTimeout();

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setConnectionStatus("disconnected");
  }, [clearReconnectTimeout]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    clearReconnectTimeout();
    setConnectionStatus("connecting");

    const url = getWsUrl();

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnectionStatus("connected");
        reconnectAttemptsRef.current = 0;
        onConnect?.();

        // 心跳
        ws.send(JSON.stringify({ type: "ping" }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "pong") return;
          if (data.type === "incoming" || data.type === "reply") {
            onEvent?.(data as GatewayEvent);
          }
        } catch {
          // 忽略解析错误
        }
      };

      ws.onclose = () => {
        setConnectionStatus("disconnected");
        onDisconnect?.();

        if (
          shouldReconnectRef.current &&
          reconnectAttemptsRef.current < maxReconnectAttempts
        ) {
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            if (shouldReconnectRef.current) {
              const currentWs = wsRef.current;
              if (
                currentWs === null ||
                currentWs.readyState === WebSocket.CLOSED
              ) {
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

      ws.onerror = () => {
        setConnectionStatus("error");
      };
    } catch {
      setConnectionStatus("error");
    }
  }, [
    getWsUrl,
    onConnect,
    onDisconnect,
    onEvent,
    clearReconnectTimeout,
    reconnectInterval,
    maxReconnectAttempts,
  ]);

  useEffect(() => {
    mountedRef.current = true;
    shouldReconnectRef.current = true;

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
  };
}
