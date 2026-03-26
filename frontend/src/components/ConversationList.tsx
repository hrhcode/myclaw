import { useState } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Trash2,
  MessageSquare,
  Clock,
  AlertTriangle,
} from "lucide-react";
import type { Conversation } from "../types";

interface ConversationListProps {
  conversations: Conversation[];
  currentConversationId: number | null;
  onSelectConversation: (id: number) => void;
  onCreateConversation: () => void;
  onDeleteConversation: (id: number) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

/**
 * 确认删除对话框组件 - 使用 Portal 渲染到 body，避免被父容器 CSS 限制
 */
const ConfirmDialog: React.FC<{
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}> = ({ isOpen, title, message, onConfirm, onCancel }) => {
  if (!isOpen) return null;

  return createPortal(
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[9999] flex items-center justify-center"
        onClick={onCancel}
      >
        <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
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
          <p
            className="text-sm mb-6"
            style={{ color: "var(--text-secondary)" }}
          >
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
      </motion.div>
    </AnimatePresence>,
    document.body,
  );
};

/**
 * 会话列表组件 - 显示和管理所有对话会话
 * 采用玻璃拟态设计，支持动画效果和主题切换
 */
const ConversationList: React.FC<ConversationListProps> = ({
  conversations,
  currentConversationId,
  onSelectConversation,
  onCreateConversation,
  onDeleteConversation,
  isCollapsed,
  onToggleCollapse,
}) => {
  const [deleteTarget, setDeleteTarget] = useState<number | null>(null);

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
   * 处理删除按钮点击 - 显示确认对话框
   */
  const handleDeleteClick = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    setDeleteTarget(id);
  };

  /**
   * 确认删除
   */
  const handleConfirmDelete = () => {
    if (deleteTarget !== null) {
      onDeleteConversation(deleteTarget);
      setDeleteTarget(null);
    }
  };

  /**
   * 取消删除
   */
  const handleCancelDelete = () => {
    setDeleteTarget(null);
  };

  return (
    <motion.div
      initial={{ x: -20, opacity: 0 }}
      animate={{
        x: 0,
        opacity: 1,
        width: isCollapsed ? 0 : 288,
      }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className="h-full flex flex-col glass-card overflow-hidden"
      style={{ borderRight: "1px solid var(--glass-border)" }}
    >
      <div
        className="p-4 flex-shrink-0"
        style={{ borderBottom: "1px solid var(--glass-border)" }}
      >
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onCreateConversation}
          className="w-full btn-primary flex items-center justify-center gap-2 py-3"
        >
          <Plus size={20} />
          <span>新建对话</span>
        </motion.button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        <AnimatePresence mode="popLayout">
          {conversations.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center py-12"
              style={{ color: "var(--text-muted)" }}
            >
              <MessageSquare
                size={48}
                strokeWidth={1}
                className="mb-4 opacity-50"
              />
              <p className="text-sm">暂无对话</p>
              <p className="text-xs mt-1 opacity-60">点击上方按钮开始新对话</p>
            </motion.div>
          ) : (
            conversations.map((conversation, index) => (
              <motion.div
                key={conversation.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => onSelectConversation(conversation.id)}
                className={`group relative p-4 rounded-xl cursor-pointer transition-all duration-300 ${
                  currentConversationId === conversation.id
                    ? "bg-gradient-to-r from-primary/20 to-primary-dark/20 border border-primary/30 shadow-glow"
                    : "glass"
                }`}
              >
                {currentConversationId === conversation.id && (
                  <motion.div
                    layoutId="activeIndicator"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-gradient-to-b from-primary to-primary-dark rounded-r-full"
                  />
                )}

                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <h3
                      className="text-sm font-medium truncate mb-1"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {conversation.title}
                    </h3>
                    <div
                      className="flex items-center gap-1.5 text-xs"
                      style={{ color: "var(--text-muted)" }}
                    >
                      <Clock size={12} />
                      <span>{formatDate(conversation.updated_at)}</span>
                    </div>
                  </div>

                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={(e) => handleDeleteClick(e, conversation.id)}
                    className="opacity-0 group-hover:opacity-100 p-2 rounded-lg transition-all"
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
                  >
                    <Trash2 size={16} />
                  </motion.button>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

      <div
        className="p-4 flex-shrink-0"
        style={{ borderTop: "1px solid var(--glass-border)" }}
      >
        <div
          className="flex items-center justify-between text-xs"
          style={{ color: "var(--text-muted)" }}
        >
          <span>共 {conversations.length} 个对话</span>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <span>在线</span>
          </div>
        </div>
      </div>

      <ConfirmDialog
        isOpen={deleteTarget !== null}
        title="删除对话"
        message="确定要删除这个对话吗？删除后将无法恢复。"
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
      />
    </motion.div>
  );
};

export default ConversationList;
