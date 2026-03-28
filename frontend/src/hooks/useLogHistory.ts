/**
 * 历史日志查询 Hook
 * 用于从数据库查询历史日志记录
 */
import { useState, useCallback, useRef } from "react";

export interface LogHistoryEntry {
  id: number;
  timestamp: string;
  level: string;
  logger: string;
  message: string;
  extra?: Record<string, unknown>;
  created_at?: string;
}

export interface LogHistoryData {
  items: LogHistoryEntry[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface UseLogHistoryOptions {
  page?: number;
  pageSize?: number;
  level?: string;
  keyword?: string;
  startTime?: string;
  endTime?: string;
  order?: "asc" | "desc";
}

interface UseLogHistoryReturn {
  logs: LogHistoryEntry[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  loading: boolean;
  error: string | null;
  fetchLogs: (params: UseLogHistoryOptions) => Promise<void>;
  refresh: () => Promise<void>;
}

const API_BASE_URL = "http://localhost:8000/api";

/**
 * 历史日志查询 Hook
 * 
 * @param initialOptions 初始查询参数
 * @returns 日志数据和操作方法
 */
export function useLogHistory(initialOptions?: UseLogHistoryOptions): UseLogHistoryReturn {
  const [logs, setLogs] = useState<LogHistoryEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(initialOptions?.page ?? 1);
  const [pageSize, setPageSize] = useState(initialOptions?.pageSize ?? 50);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const lastParamsRef = useRef<UseLogHistoryOptions>(initialOptions ?? {});

  const fetchLogs = useCallback(async (params: UseLogHistoryOptions) => {
    setLoading(true);
    setError(null);
    
    lastParamsRef.current = params;

    try {
      const queryParams = new URLSearchParams();
      queryParams.append("page", String(params.page ?? 1));
      queryParams.append("page_size", String(params.pageSize ?? 50));
      if (params.level) queryParams.append("level", params.level);
      if (params.keyword) queryParams.append("keyword", params.keyword);
      if (params.startTime) queryParams.append("start_time", params.startTime);
      if (params.endTime) queryParams.append("end_time", params.endTime);
      if (params.order) queryParams.append("order", params.order);

      const response = await fetch(`${API_BASE_URL}/logs/history?${queryParams.toString()}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success && result.data) {
        setLogs(result.data.items);
        setTotal(result.data.total);
        setPage(result.data.page);
        setPageSize(result.data.page_size);
        setTotalPages(result.data.total_pages);
      } else {
        throw new Error(result.error || "获取日志失败");
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "获取日志失败";
      setError(errorMessage);
      console.error("获取历史日志失败:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    await fetchLogs(lastParamsRef.current);
  }, [fetchLogs]);

  return {
    logs,
    total,
    page,
    pageSize,
    totalPages,
    loading,
    error,
    fetchLogs,
    refresh,
  };
}
