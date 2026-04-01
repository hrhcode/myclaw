import { AnimatePresence, motion } from "framer-motion";
import { Moon, Sun } from "lucide-react";
import { useState } from "react";
import { useTheme } from "../../contexts/ThemeContext";

const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="relative">
      <motion.button
        onClick={toggleTheme}
        whileHover={{ scale: 1.04 }}
        whileTap={{ scale: 0.96 }}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className="theme-toggle-button"
        style={{ color: "var(--text-secondary)" }}
        aria-label={theme === "dark" ? "切换到浅色模式" : "切换到深色模式"}
      >
        <AnimatePresence mode="wait">
          {theme === "dark" ? (
            <motion.div
              key="moon"
              initial={{ rotate: -90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: 90, opacity: 0 }}
              transition={{ duration: 0.18 }}
            >
              <Moon size={18} />
            </motion.div>
          ) : (
            <motion.div
              key="sun"
              initial={{ rotate: 90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: -90, opacity: 0 }}
              transition={{ duration: 0.18 }}
            >
              <Sun size={18} />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>

      <AnimatePresence>
        {showTooltip && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-full mt-2 px-3 py-1.5 rounded-lg text-xs whitespace-nowrap z-50"
            style={{
              backgroundColor: "var(--surface-elevated)",
              border: "1px solid var(--panel-border)",
              color: "var(--text-secondary)",
              boxShadow: "var(--shadow-md)",
            }}
          >
            {theme === "dark" ? "切换到浅色模式" : "切换到深色模式"}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ThemeToggle;
