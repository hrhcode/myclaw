import { useState } from "react";
import MainLayout from "../layout/MainLayout";
import ConfigTab from "./ConfigTab";
import LongTermMemoryTab from "./LongTermMemoryTab";

/**
 * 记忆管理页面主组件
 * 包含记忆配置和长期记忆两个标签页
 */
const MemoryPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"config" | "memory">("config");

  return (
    <MainLayout headerTitle="记忆管理">
      <div className="h-full flex flex-col">
        <div className="px-6 pt-6">
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => setActiveTab("config")}
              className={`px-6 py-3 rounded-xl font-medium transition-all ${
                activeTab === "config"
                  ? "bg-gradient-to-r from-primary to-primary-dark text-white shadow-lg"
                  : "glass hover:bg-white/5"
              }`}
              style={{
                color: activeTab === "config" ? "" : "var(--text-secondary)",
              }}
            >
              记忆配置
            </button>
            <button
              onClick={() => setActiveTab("memory")}
              className={`px-6 py-3 rounded-xl font-medium transition-all ${
                activeTab === "memory"
                  ? "bg-gradient-to-r from-primary to-primary-dark text-white shadow-lg"
                  : "glass hover:bg-white/5"
              }`}
              style={{
                color: activeTab === "memory" ? "" : "var(--text-secondary)",
              }}
            >
              长期记忆
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 pb-6">
          {activeTab === "config" && <ConfigTab />}
          {activeTab === "memory" && <LongTermMemoryTab />}
        </div>
      </div>
    </MainLayout>
  );
};

export default MemoryPage;
