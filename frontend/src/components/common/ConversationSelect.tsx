import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, MessageCircle } from "lucide-react";
import { useApp } from "../../contexts/AppContext";
import { useNavigate } from "react-router-dom";

interface ConversationSelectProps {
  className?: string;
}

const ConversationSelect: React.FC<ConversationSelectProps> = ({
  className = "",
}) => {
  const {
    conversations,
    currentConversationId,
    selectConversation,
  } = useApp();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentConversation = conversations.find(
    (c) => c.id === currentConversationId
  );

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (id: number) => {
    selectConversation(id);
    navigate(`/chat/${id}`, { replace: true });
    setIsOpen(false);
  };

  const sortedConversations = [...conversations].sort(
    (a, b) =>
      new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  );

  return (
    <div ref={dropdownRef} className={`relative z-[100] ${className}`}>
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2.5 rounded-xl glass transition-all duration-200 hover:bg-white/10"
        style={{ minWidth: "180px" }}
      >
        <MessageCircle size={18} style={{ color: "var(--primary)" }} />
        <span
          className="flex-1 text-left text-sm font-medium truncate"
          style={{ color: "var(--text-primary)" }}
        >
          {currentConversation?.title || "选择会话"}
        </span>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown size={16} style={{ color: "var(--text-muted)" }} />
        </motion.div>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full left-0 mt-2 w-64 rounded-xl glass-card overflow-hidden z-[101]"
            style={{
              maxHeight: "300px",
              overflowY: "auto",
            }}
          >
            {sortedConversations.length === 0 ? (
              <div
                className="px-4 py-3 text-sm text-center"
                style={{ color: "var(--text-muted)" }}
              >
                暂无会话
              </div>
            ) : (
              sortedConversations.map((conv) => (
                <motion.button
                  key={conv.id}
                  whileHover={{ backgroundColor: "var(--glass-hover)" }}
                  onClick={() => handleSelect(conv.id)}
                  className={`w-full px-4 py-3 text-left transition-colors ${
                    conv.id === currentConversationId
                      ? "bg-gradient-to-r from-primary/10 to-primary-dark/10"
                      : ""
                  }`}
                  style={{
                    borderBottom: "1px solid var(--glass-border)",
                  }}
                >
                  <div className="flex items-center gap-2">
                    <MessageCircle
                      size={14}
                      style={{
                        color:
                          conv.id === currentConversationId
                            ? "var(--primary)"
                            : "var(--text-muted)",
                      }}
                    />
                    <span
                      className="text-sm font-medium truncate flex-1"
                      style={{
                        color:
                          conv.id === currentConversationId
                            ? "var(--primary)"
                            : "var(--text-primary)",
                      }}
                    >
                      {conv.title}
                    </span>
                  </div>
                </motion.button>
              ))
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ConversationSelect;
