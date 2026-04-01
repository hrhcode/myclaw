import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  MessageSquare,
  Clock,
  Trash2,
  Edit3,
  ArrowRight,
  AlertTriangle,
  X,
  Check,
  Search,
  Loader2,
} from "lucide-react";
import MainLayout from "../layout/MainLayout";
import { useApp } from "../../contexts/AppContext";
import { getConversationStats } from "../../services/api";
import type { Conversation, Message } from "../../types";

interface ConversationWithStats extends Conversation {
  messageCount: number;
  lastMessage?: Message;
}

interface ConfirmDialogProps {
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}

interface RenameDialogProps {
  currentTitle: string;
  onConfirm: (newTitle: string) => void;
  onCancel: () => void;
}

/**
 * 确认删除对话框组件
 */
const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  title,
  message,
  onConfirm,
  onCancel,
}) => {
  return createPortal(
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.15, ease: "easeOut" }}
      className="fixed inset-0 z-[9999] flex items-center justify-center"
      onClick={onCancel}
    >
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
        onClick={(e) => e.stopPropagation()}
        className="relative glass-card p-6 rounded-2xl max-w-sm w-full mx-4 shadow-2xl"
        style={{ border: "1px solid var(--glass-border)" }}
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
            <AlertTriangle size={20} className="text-red-500" />
          </div>
          <h3
            className="text-lg font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            {title}
          </h3>
        </div>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
          {message}
        </p>
        <div className="flex gap-3">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onCancel}
            className="flex-1 py-2.5 px-4 rounded-xl glass text-sm font-medium"
            style={{ color: "var(--text-secondary)" }}
          >
            取消
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onConfirm}
            className="flex-1 py-2.5 px-4 rounded-xl bg-red-500 text-white text-sm font-medium hover:bg-red-600 transition-colors"
          >
            确认删除
          </motion.button>
        </div>
      </motion.div>
    </motion.div>,
    document.body,
  );
};

/**
 * 重命名对话框组件
 */
const RenameDialog: React.FC<RenameDialogProps> = ({
  currentTitle,
  onConfirm,
  onCancel,
}) => {
  const [title, setTitle] = useState(currentTitle);

  useEffect(() => {
    setTitle(currentTitle);
  }, [currentTitle]);

  return createPortal(
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.15, ease: "easeOut" }}
      className="fixed inset-0 z-[9999] flex items-center justify-center"
      onClick={onCancel}
    >
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
        onClick={(e) => e.stopPropagation()}
        className="relative glass-card p-6 rounded-2xl max-w-sm w-full mx-4 shadow-2xl"
        style={{ border: "1px solid var(--glass-border)" }}
      >
        <div className="flex items-center justify-between mb-4">
          <h3
            className="text-lg font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            重命名会话
          </h3>
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={onCancel}
            className="p-1.5 rounded-lg transition-colors"
            style={{ color: "var(--text-muted)" }}
          >
            <X size={18} />
          </motion.button>
        </div>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="请输入会话标题"
          className="w-full px-4 py-3 glass-input rounded-xl mb-4"
          style={{ color: "var(--text-primary)" }}
          autoFocus
          onKeyDown={(e) => {
            if (e.key === "Enter" && title.trim()) {
              onConfirm(title.trim());
            }
            if (e.key === "Escape") {
              onCancel();
            }
          }}
        />
        <div className="flex gap-3">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onCancel}
            className="flex-1 py-2.5 px-4 rounded-xl glass text-sm font-medium"
            style={{ color: "var(--text-secondary)" }}
          >
            取消
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onConfirm(title.trim())}
            disabled={!title.trim()}
            className="flex-1 py-2.5 px-4 rounded-xl bg-primary text-white text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <Check size={16} />
            确认
          </motion.button>
        </div>
      </motion.div>
    </motion.div>,
    document.body,
  );
};

/**
 * 会话管理页面 - 显示所有会话，支持删除、重命名、跳转聊天
 */
const ConversationsPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    conversations,
    loadConversations,
    removeConversation,
    renameConversationById,
  } = useApp();
  const [conversationsWithStats, setConversationsWithStats] = useState<
    ConversationWithStats[]
  >([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<number | null>(null);
  const [renameTarget, setRenameTarget] = useState<{
    id: number;
    title: string;
  } | null>(null);

  /**
   * 加载会话统计信息
   */
  const loadConversationStats = async () => {
    setIsLoading(true);
    try {
      const statsResponse = await getConversationStats();
      const statsMap = new Map(
        statsResponse.map((item) => [item.conversation_id, item]),
      );
      const stats = conversations.map((conv) => {
        const item = statsMap.get(conv.id);
        const lastMessage =
          item?.last_message_content && item.last_message_created_at
            ? {
                id: item.last_message_id || Date.now(),
                conversation_id: conv.id,
                role: "assistant" as const,
                content: item.last_message_content,
                created_at: item.last_message_created_at,
              }
            : undefined;
        return {
          ...conv,
          messageCount: item?.message_count || 0,
          lastMessage,
        };
      });
      setConversationsWithStats(
        stats.sort(
          (a, b) =>
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
        ),
      );
    } catch (error) {
      console.error("Failed to load conversation stats:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    if (conversations.length > 0) {
      loadConversationStats();
    } else {
      setConversationsWithStats([]);
      setIsLoading(false);
    }
  }, [conversations]);

  /**
   * 格式化日期显示
   */
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "刚刚";
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    return date.toLocaleDateString("zh-CN");
  };

  /**
   * 截断消息内容
   */
  const truncateMessage = (content: string, maxLength: number = 50) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + "...";
  };

  /**
   * 过滤会话列表
   */
  const filteredConversations = conversationsWithStats.filter((conv) =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  /**
   * 处理删除会话
   * 如果只剩一个会话，则不允许删除
   */
  const handleDelete = async () => {
    if (deleteTarget === null) return;

    if (conversations.length <= 1) {
      alert("无法删除最后一个会话，系统至少需要保留一个会话");
      setDeleteTarget(null);
      return;
    }

    try {
      await removeConversation(deleteTarget);
      setDeleteTarget(null);
    } catch (error) {
      console.error("Failed to delete conversation:", error);
      alert("删除会话失败，请稍后重试");
    }
  };

  /**
   * 处理重命名会话
   */
  const handleRename = async (newTitle: string) => {
    if (renameTarget === null || !newTitle) return;
    try {
      await renameConversationById(renameTarget.id, newTitle);
      setRenameTarget(null);
    } catch (error) {
      console.error("Failed to rename conversation:", error);
    }
  };

  /**
   * 跳转到聊天页面
   */
  const goToChat = (conversationId: number) => {
    navigate(`/chat/${conversationId}`);
  };

  return (
    <MainLayout headerTitle="会话管理">
      <div className="h-full flex flex-col p-6">
        <div className="mb-6">
          <div className="relative">
            <Search
              size={18}
              className="absolute left-4 top-1/2 -translate-y-1/2"
              style={{ color: "var(--text-muted)" }}
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索会话..."
              className="w-full pl-12 pr-4 py-3 glass-input rounded-xl"
              style={{ color: "var(--text-primary)" }}
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              >
                <Loader2 size={32} className="text-primary" />
              </motion.div>
            </div>
          ) : filteredConversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64">
              <MessageSquare
                size={48}
                strokeWidth={1}
                className="mb-4 opacity-50"
                style={{ color: "var(--text-muted)" }}
              />
              <p style={{ color: "var(--text-muted)" }}>
                {searchQuery ? "没有找到匹配的会话" : "暂无会话"}
              </p>
              <p
                className="text-sm mt-1 opacity-60"
                style={{ color: "var(--text-muted)" }}
              >
                {searchQuery ? "尝试其他搜索词" : "开始一个新的对话吧"}
              </p>
            </div>
          ) : (
            <div
              className="hidden lg:block glass-card rounded-2xl overflow-hidden"
              style={{ border: "1px solid var(--glass-border)" }}
            >
              <div
                className="grid gap-0"
                style={{
                  gridTemplateColumns: "1fr 100px 140px 120px",
                }}
              >
                <div
                  className="px-5 py-3.5 text-xs font-medium uppercase tracking-wider"
                  style={{
                    color: "var(--text-muted)",
                    borderBottom: "1px solid var(--glass-border)",
                  }}
                >
                  会话标题
                </div>
                <div
                  className="px-4 py-3.5 text-xs font-medium uppercase tracking-wider text-center"
                  style={{
                    color: "var(--text-muted)",
                    borderBottom: "1px solid var(--glass-border)",
                  }}
                >
                  消息数
                </div>
                <div
                  className="px-4 py-3.5 text-xs font-medium uppercase tracking-wider"
                  style={{
                    color: "var(--text-muted)",
                    borderBottom: "1px solid var(--glass-border)",
                  }}
                >
                  更新时间
                </div>
                <div
                  className="px-4 py-3.5 text-xs font-medium uppercase tracking-wider text-center"
                  style={{
                    color: "var(--text-muted)",
                    borderBottom: "1px solid var(--glass-border)",
                  }}
                >
                  操作
                </div>
              </div>

              <AnimatePresence mode="popLayout">
                {filteredConversations.map((conv, index) => (
                  <motion.div
                    key={conv.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ delay: index * 0.03 }}
                    className="grid group cursor-pointer hover:bg-[var(--glass-bg)] transition-colors"
                    style={{
                      gridTemplateColumns: "1fr 100px 140px 120px",
                      borderBottom:
                        index < filteredConversations.length - 1
                          ? "1px solid var(--glass-border)"
                          : "none",
                    }}
                    onClick={() => goToChat(conv.id)}
                  >
                    <div className="px-5 py-4 flex items-center gap-3">
                      <div
                        className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                        style={{ backgroundColor: "var(--primary-alpha)" }}
                      >
                        <MessageSquare size={18} className="text-primary" />
                      </div>
                      <div className="min-w-0">
                        <h3
                          className="text-sm font-medium truncate"
                          style={{ color: "var(--text-primary)" }}
                        >
                          {conv.title}
                        </h3>
                        {conv.lastMessage && (
                          <p
                            className="text-xs truncate mt-0.5"
                            style={{ color: "var(--text-muted)" }}
                          >
                            {truncateMessage(conv.lastMessage.content, 40)}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="px-4 py-4 flex items-center justify-center">
                      <span
                        className="text-sm font-medium px-2.5 py-1 rounded-lg"
                        style={{
                          backgroundColor: "var(--glass-bg)",
                          color: "var(--text-secondary)",
                        }}
                      >
                        {conv.messageCount}
                      </span>
                    </div>

                    <div className="px-4 py-4 flex items-center gap-2">
                      <Clock size={14} style={{ color: "var(--text-muted)" }} />
                      <span
                        className="text-sm"
                        style={{ color: "var(--text-muted)" }}
                      >
                        {formatDate(conv.updated_at)}
                      </span>
                    </div>

                    <div className="px-4 py-4 flex items-center justify-center gap-1">
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={(e) => {
                          e.stopPropagation();
                          setRenameTarget({ id: conv.id, title: conv.title });
                        }}
                        className="p-2 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                        style={{ color: "var(--text-muted)" }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.color = "var(--primary)";
                          e.currentTarget.style.backgroundColor =
                            "var(--glass-bg)";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.color = "var(--text-muted)";
                          e.currentTarget.style.backgroundColor = "transparent";
                        }}
                        title="重命名"
                      >
                        <Edit3 size={16} />
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeleteTarget(conv.id);
                        }}
                        className="p-2 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                        style={{ color: "var(--text-muted)" }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.color = "#ef4444";
                          e.currentTarget.style.backgroundColor =
                            "rgba(239, 68, 68, 0.1)";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.color = "var(--text-muted)";
                          e.currentTarget.style.backgroundColor = "transparent";
                        }}
                        title="删除"
                      >
                        <Trash2 size={16} />
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="p-2 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                        style={{ color: "var(--text-muted)" }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.color = "var(--primary)";
                          e.currentTarget.style.backgroundColor =
                            "var(--glass-bg)";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.color = "var(--text-muted)";
                          e.currentTarget.style.backgroundColor = "transparent";
                        }}
                        title="进入聊天"
                      >
                        <ArrowRight size={16} />
                      </motion.button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}

          {filteredConversations.length > 0 && (
            <div className="lg:hidden grid grid-cols-1 gap-3">
              <AnimatePresence mode="popLayout">
                {filteredConversations.map((conv, index) => (
                  <motion.div
                    key={conv.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ delay: index * 0.03 }}
                    className="glass-card rounded-xl p-4 cursor-pointer"
                    style={{ border: "1px solid var(--glass-border)" }}
                    onClick={() => goToChat(conv.id)}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <div
                        className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                        style={{ backgroundColor: "var(--primary-alpha)" }}
                      >
                        <MessageSquare size={16} className="text-primary" />
                      </div>
                      <h3
                        className="text-sm font-medium truncate flex-1"
                        style={{ color: "var(--text-primary)" }}
                      >
                        {conv.title}
                      </h3>
                      <span
                        className="text-xs px-2 py-0.5 rounded-md"
                        style={{
                          backgroundColor: "var(--glass-bg)",
                          color: "var(--text-muted)",
                        }}
                      >
                        {conv.messageCount} 条消息
                      </span>
                    </div>
                    {conv.lastMessage && (
                      <p
                        className="text-xs line-clamp-1 mb-2"
                        style={{ color: "var(--text-muted)" }}
                      >
                        {truncateMessage(conv.lastMessage.content, 60)}
                      </p>
                    )}
                    <div className="flex items-center justify-between">
                      <span
                        className="text-xs"
                        style={{ color: "var(--text-muted)" }}
                      >
                        {formatDate(conv.updated_at)}
                      </span>
                      <div className="flex items-center gap-1">
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={(e) => {
                            e.stopPropagation();
                            setRenameTarget({ id: conv.id, title: conv.title });
                          }}
                          className="p-1.5 rounded-lg"
                          style={{ color: "var(--text-muted)" }}
                          title="重命名"
                        >
                          <Edit3 size={14} />
                        </motion.button>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteTarget(conv.id);
                          }}
                          className="p-1.5 rounded-lg"
                          style={{ color: "var(--text-muted)" }}
                          title="删除"
                        >
                          <Trash2 size={14} />
                        </motion.button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>

        <div
          className="mt-4 pt-4 text-center text-xs"
          style={{
            color: "var(--text-muted)",
            borderTop: "1px solid var(--glass-border)",
          }}
        >
          共 {filteredConversations.length} 个会话
        </div>

        <AnimatePresence>
          {deleteTarget !== null && (
            <ConfirmDialog
              title="删除会话"
              message="确定要删除这个会话吗？删除后将无法恢复，所有消息记录都将被清除。"
              onConfirm={handleDelete}
              onCancel={() => setDeleteTarget(null)}
            />
          )}
        </AnimatePresence>

        <AnimatePresence>
          {renameTarget !== null && (
            <RenameDialog
              currentTitle={renameTarget.title}
              onConfirm={handleRename}
              onCancel={() => setRenameTarget(null)}
            />
          )}
        </AnimatePresence>
      </div>
    </MainLayout>
  );
};

export default ConversationsPage;
