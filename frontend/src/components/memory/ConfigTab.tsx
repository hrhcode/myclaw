import { useState, useEffect, useCallback } from "react";
import { Save, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import SearchConfigPanel from "./components/SearchConfigPanel";
import { getConfig, setConfig } from "../../services/api";

/**
 * 记忆配置组件
 * 包含搜索参数配置
 */
const ConfigTab: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const [config, setConfigState] = useState({
    memory_top_k: "5",
    memory_min_score: "0.5",
    memory_use_hybrid: "true",
    memory_vector_weight: "0.7",
    memory_text_weight: "0.3",
    memory_enable_mmr: "true",
    memory_mmr_lambda: "0.7",
    memory_enable_temporal_decay: "true",
    memory_half_life_days: "30",
  });

  const loadConfig = useCallback(async () => {
    try {
      setIsLoading(true);
      const configKeys = [
        "memory_top_k",
        "memory_min_score",
        "memory_use_hybrid",
        "memory_vector_weight",
        "memory_text_weight",
        "memory_enable_mmr",
        "memory_mmr_lambda",
        "memory_enable_temporal_decay",
        "memory_half_life_days",
      ];

      const [configResults] = await Promise.all([
        Promise.all(
          configKeys.map(async (key) => {
            try {
              const value = await getConfig(key);
              return { key, value };
            } catch {
              return { key, value: null };
            }
          }),
        ),
      ]);

      const newConfig = { ...config };
      configResults.forEach(({ key, value }) => {
        if (value !== null) {
          newConfig[key as keyof typeof newConfig] = value;
        }
      });

      setConfigState(newConfig);
    } catch (error) {
      console.error("Failed to load config:", error);
      setMessage({ type: "error", text: "加载配置失败" });
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setMessage(null);

      const savePromises = Object.entries(config).map(([key, value]) =>
        setConfig(key, value),
      );

      await Promise.all(savePromises);

      setMessage({ type: "success", text: "配置保存成功！" });
    } catch (error) {
      console.error("Failed to save config:", error);
      setMessage({ type: "error", text: "保存配置失败" });
    } finally {
      setIsSaving(false);
    }
  };

  const handleConfigChange = (key: string, value: string) => {
    setConfigState((prev) => ({ ...prev, [key]: value }));
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin">
          <Loader2 size={40} className="text-primary" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto pb-8">
      {message && (
        <div
          className={`mb-6 p-4 rounded-xl flex items-center gap-3 ${
            message.type === "success"
              ? "bg-green-500/10 border border-green-500/20 text-green-400"
              : "bg-red-500/10 border border-red-500/20 text-red-400"
          }`}
        >
          {message.type === "success" ? (
            <CheckCircle size={20} />
          ) : (
            <AlertCircle size={20} />
          )}
          <span>{message.text}</span>
        </div>
      )}

      <SearchConfigPanel config={config} onChange={handleConfigChange} />

      <div className="flex justify-end mt-6">
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="btn-primary flex items-center gap-2"
        >
          {isSaving ? (
            <>
              <div className="animate-spin">
                <Loader2 size={18} />
              </div>
              <span>保存中...</span>
            </>
          ) : (
            <>
              <Save size={18} />
              <span>保存配置</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default ConfigTab;
