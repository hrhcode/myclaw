/**
 * 日志清理 Hook
 * 用于清理历史日志记录
 */
import { useState, useCallback } from "react";

interface CleanupResult {
  total_before: number;
  total_after: number;
  deleted_count: number;
  keep_count?: number;
  message: string;
}

interface UseLogCleanupReturn {
  loading: boolean;
  error: string | null;
  result: CleanupResult | null;
  cleanupKeepRecent: (keepCount: number) => Promise<CleanupResult | null>;
  cleanupAll: () => Promise<CleanupResult | null>;
  reset: () => void;
}

const API_BASE_URL = "http://localhost:8000/api";

/**
 * 日志清理 Hook
 * 
 * @returns 清理方法和状态
 */
export function useLogCleanup(): UseLogCleanupReturn {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CleanupResult | null>(null);

  /**
   * 保留最近 N 条日志
   */
  const cleanupKeepRecent = useCallback(async (keepCount: number): Promise<CleanupResult | null> => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/logs/cleanup/keep-recent?keep_count=${keepCount}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.success && data.data) {
        setResult(data.data);
        return data.data;
      } else {
        throw new Error(data.error || "清理日志失败");
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "清理日志失败";
      setError(errorMessage);
      console.error("清理日志失败:", err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 清空所有日志
   */
  const cleanupAll = useCallback(async (): Promise<CleanupResult | null> => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/logs/all`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.success && data.data) {
        setResult(data.data);
        return data.data;
      } else {
        throw new Error(data.error || "清空日志失败");
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "清空日志失败";
      setError(errorMessage);
      console.error("清空日志失败:", err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 重置状态
   */
  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
    setResult(null);
  }, []);

  return {
    loading,
    error,
    result,
    cleanupKeepRecent,
    cleanupAll,
    reset,
  };
}
