import { Suspense, lazy } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppProvider } from "./contexts/AppContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import "./App.css";
import "./openclaw.css";

const ChatPage = lazy(() => import("./components/chat/ChatPage"));
const ConversationsPage = lazy(() => import("./components/conversations/ConversationsPage"));
const SettingsPage = lazy(() => import("./components/settings/SettingsPage"));
const MemoryPage = lazy(() => import("./components/memory"));
const LogsPage = lazy(() =>
  import("./components/logs").then((module) => ({ default: module.LogsPage })),
);
const HistoryLogsPage = lazy(() =>
  import("./components/logs").then((module) => ({ default: module.HistoryLogsPage })),
);
const ToolsPage = lazy(() => import("./components/tools/ToolsPage"));
const AutomationsPage = lazy(() => import("./components/automations/AutomationsPage"));

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AppProvider>
        <BrowserRouter>
          <Suspense fallback={<div className="p-6 text-sm">页面加载中...</div>}>
            <Routes>
              <Route path="/" element={<Navigate to="/chat" replace />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/chat/:conversationId" element={<ChatPage />} />
              <Route path="/conversations" element={<ConversationsPage />} />
              <Route path="/memory" element={<Navigate to="/knowledge" replace />} />
              <Route path="/knowledge" element={<MemoryPage />} />
              <Route path="/automations" element={<AutomationsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/tools" element={<ToolsPage />} />
              <Route path="/logs" element={<Navigate to="/logs/realtime" replace />} />
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
