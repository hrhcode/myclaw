import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  BookOpenText,
  FileUp,
  Loader2,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";

import MainLayout from "../layout/MainLayout";
import { SectionCard } from "../admin";
import {
  deleteKnowledge,
  getKnowledgeBase,
  uploadMarkdownKnowledge,
} from "../../services/api";
import type { KnowledgeBaseItem, KnowledgeBaseListResponse } from "../../types";

const formatDate = (value: string) =>
  new Date(value).toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });

const KnowledgeBasePage: React.FC = () => {
  const [data, setData] = useState<KnowledgeBaseListResponse | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filter, setFilter] = useState<
    "all" | "markdown" | "assistant_reply" | "note"
  >("all");
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const loadKnowledgeBase = useCallback(async () => {
    try {
      setIsLoading(true);
      const next = await getKnowledgeBase();
      setData(next);
    } catch (error) {
      console.error("Failed to load knowledge base:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadKnowledgeBase();
  }, [loadKnowledgeBase]);

  const filteredItems = useMemo(() => {
    const items = data?.items || [];
    const query = searchQuery.trim().toLowerCase();
    return items.filter((item) => {
      const matchesFilter =
        filter === "all" ? true : item.content_type === filter;
      const matchesQuery = query
        ? [item.title, item.preview, item.source || ""].some((value) =>
            value.toLowerCase().includes(query),
          )
        : true;
      return matchesFilter && matchesQuery;
    });
  }, [data?.items, filter, searchQuery]);

  const handleChooseFile = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) {
      return;
    }
    try {
      setIsUploading(true);
      await uploadMarkdownKnowledge(file);
      await loadKnowledgeBase();
    } catch (error) {
      console.error("Failed to upload markdown knowledge:", error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (identifier: string) => {
    try {
      setDeletingId(identifier);
      await deleteKnowledge(identifier);
      await loadKnowledgeBase();
    } catch (error) {
      console.error("Failed to delete knowledge:", error);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <MainLayout headerTitle="知识库">
      <div className="admin-page">
        <div className="admin-frame">
          <input
            ref={fileInputRef}
            type="file"
            accept=".md,.markdown,text/markdown"
            className="hidden"
            onChange={(event) => void handleFileChange(event)}
          />

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <SectionCard className="p-5">
              <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                知识条目
              </div>
              <div
                className="mt-2 text-2xl font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                {data?.stats.total_items ?? 0}
              </div>
            </SectionCard>
            <SectionCard className="p-5">
              <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                Markdown 文档
              </div>
              <div
                className="mt-2 text-2xl font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                {data?.stats.markdown_groups ?? 0}
              </div>
            </SectionCard>
            <SectionCard className="p-5">
              <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                保存的 AI 回复
              </div>
              <div
                className="mt-2 text-2xl font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                {data?.stats.assistant_replies ?? 0}
              </div>
            </SectionCard>
          </div>

          <div className="admin-toolbar">
            <button
              type="button"
              className="btn-primary inline-flex items-center gap-2"
              onClick={handleChooseFile}
              disabled={isUploading}
            >
              {isUploading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <FileUp size={16} />
              )}
              <span>{isUploading ? "上传中..." : "上传 Markdown"}</span>
            </button>

            <button
              type="button"
              className="btn-secondary inline-flex items-center gap-2"
              onClick={() => void loadKnowledgeBase()}
              disabled={isLoading}
            >
              <RefreshCw size={16} />
              <span>刷新</span>
            </button>

            <div className="relative min-w-[220px] flex-1">
              <Search
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2"
                style={{ color: "var(--text-muted)" }}
              />
              <input
                type="text"
                className="admin-input w-full py-2.5 pl-9 pr-3"
                placeholder="搜索标题、摘要或来源"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
              />
            </div>

            <select
              className="admin-select px-3 py-2.5"
              value={filter}
              onChange={(event) =>
                setFilter(
                  event.target.value as
                    | "all"
                    | "markdown"
                    | "assistant_reply"
                    | "note",
                )
              }
            >
              <option value="all">全部类型</option>
              <option value="markdown">Markdown</option>
              <option value="assistant_reply">AI 回复</option>
              <option value="note">其他知识</option>
            </select>
          </div>

          {isLoading ? (
            <div className="flex h-full items-center justify-center py-16">
              <Loader2 size={36} className="text-primary animate-spin" />
            </div>
          ) : filteredItems.length === 0 ? (
            <SectionCard className="py-12 text-center">
              <BookOpenText
                size={40}
                className="mx-auto mb-3"
                style={{ color: "var(--text-muted)" }}
              />
              <p style={{ color: "var(--text-muted)" }}>
                知识库还是空的。你可以上传
                Markdown，或在聊天页把优质回复保存进来。
              </p>
            </SectionCard>
          ) : (
            <div className="grid gap-3">
              {filteredItems.map((item) => (
                <KnowledgeRow
                  key={item.id}
                  item={item}
                  deleting={deletingId === item.id}
                  onDelete={() => void handleDelete(item.id)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
};

const KnowledgeRow: React.FC<{
  item: KnowledgeBaseItem;
  deleting: boolean;
  onDelete: () => void;
}> = ({ item, deleting, onDelete }) => {
  const typeLabel =
    item.content_type === "markdown"
      ? "Markdown"
      : item.content_type === "assistant_reply"
        ? "AI 回复"
        : "知识条目";

  return (
    <SectionCard className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <span
              className="rounded-md px-2 py-0.5 text-xs"
              style={{
                backgroundColor: "var(--surface-subtle)",
                color: "var(--text-secondary)",
              }}
            >
              {typeLabel}
            </span>
            <span
              className="rounded-md px-2 py-0.5 text-xs"
              style={{
                backgroundColor: "var(--surface-subtle)",
                color: "var(--text-secondary)",
              }}
            >
              {item.item_count} 段
            </span>
            {item.source ? (
              <span
                className="rounded-md px-2 py-0.5 text-xs"
                style={{
                  backgroundColor: "var(--surface-subtle)",
                  color: "var(--text-secondary)",
                }}
              >
                来源: {item.source}
              </span>
            ) : null}
          </div>

          <h3
            className="text-base font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            {item.title}
          </h3>
          <p
            className="mt-2 text-sm leading-7"
            style={{ color: "var(--text-secondary)" }}
          >
            {item.preview}
          </p>
          <div className="mt-3 text-xs" style={{ color: "var(--text-muted)" }}>
            更新于 {formatDate(item.updated_at)}
          </div>
        </div>

        <button
          type="button"
          className="rounded-lg p-2"
          style={{ color: "#dc2626" }}
          onClick={onDelete}
          disabled={deleting}
          title="删除知识"
        >
          {deleting ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Trash2 size={16} />
          )}
        </button>
      </div>
    </SectionCard>
  );
};

export default KnowledgeBasePage;
