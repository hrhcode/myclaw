import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AppProvider } from "./contexts/AppContext";
import ChatPage from "./components/chat/ChatPage";
import ConversationsPage from "./components/conversations/ConversationsPage";
import SettingsPage from "./components/settings/SettingsPage";
import MemoryPage from "./components/memory";
import { LogsPage, HistoryLogsPage } from "./components/logs";
import ToolsPage from "./components/tools/ToolsPage";
import "./App.css";

/**
 * 主应用组件
 */
const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AppProvider>
        <BrowserRouter>
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
        </BrowserRouter>
      </AppProvider>
    </ThemeProvider>
  );
};

export default App;
