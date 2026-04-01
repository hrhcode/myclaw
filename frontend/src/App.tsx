import { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AppProvider } from "./contexts/AppContext";
import "./App.css";

const ChatPage = lazy(() => import("./components/chat/ChatPage"));
const ConversationsPage = lazy(
  () => import("./components/conversations/ConversationsPage"),
);
const SettingsPage = lazy(() => import("./components/settings/SettingsPage"));
const MemoryPage = lazy(() => import("./components/memory"));
const LogsPage = lazy(() =>
  import("./components/logs").then((module) => ({ default: module.LogsPage })),
);
const HistoryLogsPage = lazy(() =>
  import("./components/logs").then((module) => ({
    default: module.HistoryLogsPage,
  })),
);
const ToolsPage = lazy(() => import("./components/tools/ToolsPage"));

/**
 * 主应用组件
 */
const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AppProvider>
        <BrowserRouter>
          <Suspense fallback={<div className="p-6 text-sm">加载中...</div>}>
            <Routes>
              <Route path="/" element={<Navigate to="/chat" replace />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/chat/:conversationId" element={<ChatPage />} />
              <Route path="/conversations" element={<ConversationsPage />} />
              <Route path="/memory" element={<MemoryPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/tools" element={<ToolsPage />} />
              <Route
                path="/logs"
                element={<Navigate to="/logs/realtime" replace />}
              />
              <Route path="/logs/realtime" element={<LogsPage />} />
              <Route path="/logs/history" element={<HistoryLogsPage />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AppProvider>
    </ThemeProvider>
  );
};

export default App;
