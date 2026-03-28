import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Save,
  Cpu,
  CheckCircle,
  AlertCircle,
  Loader2,
  Eye,
  EyeOff,
} from "lucide-react";
import MainLayout from "../layout/MainLayout";
import {
  getProviders,
  getProviderModels,
  getEmbeddingProviders,
  getEmbeddingProviderModels,
  getConfig,
  setConfig,
} from "../../services/api";
import type { Provider, Model } from "../../types";

/**
 * 配置页面组件 - 配置API和模型参数
 * 采用玻璃拟态设计，支持动画效果和主题切换
 */
const SettingsPage: React.FC = () => {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [embeddingProviders, setEmbeddingProviders] = useState<Provider[]>([]);
  const [embeddingModels, setEmbeddingModels] = useState<Model[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [selectedEmbeddingProvider, setSelectedEmbeddingProvider] =
    useState<string>("");
  const [selectedEmbeddingModel, setSelectedEmbeddingModel] =
    useState<string>("");
  const [apiKey, setApiKey] = useState<string>("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [openrouterApiKey, setOpenrouterApiKey] = useState<string>("");
  const [showOpenrouterKey, setShowOpenrouterKey] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  /**
   * 加载模型列表
   */
  const loadModels = useCallback(
    async (provider: string) => {
      try {
        const modelList = await getProviderModels(provider);
        setModels(modelList);

        if (selectedModel && !modelList.find((m) => m.id === selectedModel)) {
          setSelectedModel(modelList.length > 0 ? modelList[0].id : "");
        } else if (modelList.length > 0 && !selectedModel) {
          setSelectedModel(modelList[0].id);
        }
      } catch (error) {
        console.error("Failed to load models:", error);
      }
    },
    [selectedModel],
  );

  /**
   * 加载Embedding模型列表
   */
  const loadEmbeddingModels = useCallback(
    async (provider: string) => {
      try {
        const modelList = await getEmbeddingProviderModels(provider);
        setEmbeddingModels(modelList);

        if (
          selectedEmbeddingModel &&
          !modelList.find((m) => m.id === selectedEmbeddingModel)
        ) {
          setSelectedEmbeddingModel(
            modelList.length > 0 ? modelList[0].id : "",
          );
        } else if (modelList.length > 0 && !selectedEmbeddingModel) {
          setSelectedEmbeddingModel(modelList[0].id);
        }
      } catch (error) {
        console.error("Failed to load embedding models:", error);
      }
    },
    [selectedEmbeddingModel],
  );

  /**
   * 加载设置数据
   */
  const loadSettings = async () => {
    try {
      setIsLoading(true);

      const providerList = await getProviders();
      const embeddingProviderList = await getEmbeddingProviders();
      setProviders(providerList);
      setEmbeddingProviders(embeddingProviderList);

      const savedProvider = await getConfig("llm_provider").catch(() => "");
      const savedModel = await getConfig("llm_model").catch(() => "");
      const savedApiKey = await getConfig("zhipu_api_key").catch(() => "");
      const savedOpenrouterKey = await getConfig("openrouter_api_key").catch(
        () => "",
      );
      const savedEmbeddingProvider = await getConfig(
        "embedding_provider",
      ).catch(() => "");
      const savedEmbeddingModel = await getConfig("embedding_model").catch(
        () => "",
      );

      if (savedProvider) {
        setSelectedProvider(savedProvider);
      } else if (providerList.length > 0) {
        setSelectedProvider(providerList[0].id);
      }

      if (savedEmbeddingProvider) {
        setSelectedEmbeddingProvider(savedEmbeddingProvider);
      } else if (embeddingProviderList.length > 0) {
        setSelectedEmbeddingProvider(embeddingProviderList[0].id);
      }

      if (savedApiKey) {
        setApiKey(savedApiKey);
      }

      if (savedOpenrouterKey) {
        setOpenrouterApiKey(savedOpenrouterKey);
      }

      if (savedModel) {
        setSelectedModel(savedModel);
      }

      if (savedEmbeddingModel) {
        setSelectedEmbeddingModel(savedEmbeddingModel);
      }
    } catch (error) {
      console.error("Failed to load settings:", error);
      setMessage({ type: "error", text: "加载设置失败" });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  useEffect(() => {
    if (selectedProvider) {
      loadModels(selectedProvider);
    }
  }, [selectedProvider, loadModels]);

  useEffect(() => {
    if (selectedEmbeddingProvider) {
      loadEmbeddingModels(selectedEmbeddingProvider);
    }
  }, [selectedEmbeddingProvider, loadEmbeddingModels]);

  /**
   * 保存设置
   */
  const handleSave = async () => {
    if (!apiKey.trim()) {
      setMessage({ type: "error", text: "请输入智谱AI API Key" });
      return;
    }

    if (!selectedProvider) {
      setMessage({ type: "error", text: "请选择LLM提供商" });
      return;
    }

    if (!selectedModel) {
      setMessage({ type: "error", text: "请选择LLM模型" });
      return;
    }

    if (!selectedEmbeddingProvider) {
      setMessage({ type: "error", text: "请选择Embedding提供商" });
      return;
    }

    if (!selectedEmbeddingModel) {
      setMessage({ type: "error", text: "请选择Embedding模型" });
      return;
    }

    try {
      setIsSaving(true);
      setMessage(null);

      await setConfig("zhipu_api_key", apiKey);
      await setConfig("llm_provider", selectedProvider);
      await setConfig("llm_model", selectedModel);

      if (openrouterApiKey.trim()) {
        await setConfig("openrouter_api_key", openrouterApiKey);
      }

      await setConfig("embedding_provider", selectedEmbeddingProvider);
      await setConfig("embedding_model", selectedEmbeddingModel);

      setMessage({ type: "success", text: "设置保存成功！" });
    } catch (error) {
      console.error("Failed to save settings:", error);
      setMessage({ type: "error", text: "保存设置失败" });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <MainLayout headerTitle="配置">
        <div className="h-full flex items-center justify-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          >
            <Loader2 size={40} className="text-primary" />
          </motion.div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout headerTitle="配置">
      <div className="h-full overflow-y-auto p-6">
        <div className="max-w-6xl mx-auto pb-8">
          <AnimatePresence mode="wait">
            {message && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
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
              </motion.div>
            )}
          </AnimatePresence>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="glass-card rounded-2xl p-6"
              style={{ border: "1px solid var(--glass-border)" }}
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/20 to-primary-dark/20 flex items-center justify-center">
                  <Cpu size={20} className="text-primary" />
                </div>
                <div>
                  <h2
                    className="text-lg font-semibold"
                    style={{ color: "var(--text-primary)" }}
                  >
                    LLM配置
                  </h2>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    选择AI模型提供商和模型
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label
                    className="block text-sm font-medium mb-2"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    模型厂商
                  </label>
                  <select
                    value={selectedProvider}
                    onChange={(e) => setSelectedProvider(e.target.value)}
                    className="w-full px-4 py-3 glass-input rounded-xl appearance-none cursor-pointer"
                    style={{
                      color: "var(--text-primary)",
                      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='${encodeURIComponent("var(--text-muted)")}'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
                      backgroundRepeat: "no-repeat",
                      backgroundPosition: "right 1rem center",
                      backgroundSize: "1.5rem",
                    }}
                  >
                    <option value="">请选择厂商</option>
                    {providers.map((provider) => (
                      <option key={provider.id} value={provider.id}>
                        {provider.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label
                    className="block text-sm font-medium mb-2"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    模型
                  </label>
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    disabled={!selectedProvider}
                    className="w-full px-4 py-3 glass-input rounded-xl appearance-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{
                      color: "var(--text-primary)",
                      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='${encodeURIComponent("var(--text-muted)")}'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
                      backgroundRepeat: "no-repeat",
                      backgroundPosition: "right 1rem center",
                      backgroundSize: "1.5rem",
                    }}
                  >
                    <option value="">请先选择厂商</option>
                    {models.map((model) => (
                      <option key={model.id} value={model.id}>
                        {model.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label
                    className="block text-sm font-medium mb-2"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    智谱AI API Key
                  </label>
                  <div className="relative">
                    <input
                      type={showApiKey ? "text" : "password"}
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="请输入您的智谱AI API Key"
                      className="w-full px-4 py-3 pr-12 glass-input rounded-xl"
                      style={{ color: "var(--text-primary)" }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 transition-colors"
                      style={{ color: "var(--text-muted)" }}
                      onMouseEnter={(e) =>
                        (e.currentTarget.style.color = "var(--text-primary)")
                      }
                      onMouseLeave={(e) =>
                        (e.currentTarget.style.color = "var(--text-muted)")
                      }
                    >
                      {showApiKey ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                  <p
                    className="mt-2 text-xs"
                    style={{ color: "var(--text-muted)" }}
                  >
                    用于智谱AI聊天功能，API Key将安全存储在数据库中
                  </p>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="glass-card rounded-2xl p-6"
              style={{ border: "1px solid var(--glass-border)" }}
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-700/20 flex items-center justify-center">
                  <Cpu size={20} className="text-purple-400" />
                </div>
                <div>
                  <h2
                    className="text-lg font-semibold"
                    style={{ color: "var(--text-primary)" }}
                  >
                    Embedding配置
                  </h2>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    向量嵌入模型（用于记忆搜索）
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label
                    className="block text-sm font-medium mb-2"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    模型厂商
                  </label>
                  <select
                    value={selectedEmbeddingProvider}
                    onChange={(e) =>
                      setSelectedEmbeddingProvider(e.target.value)
                    }
                    className="w-full px-4 py-3 glass-input rounded-xl appearance-none cursor-pointer"
                    style={{
                      color: "var(--text-primary)",
                      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='${encodeURIComponent("var(--text-muted)")}'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
                      backgroundRepeat: "no-repeat",
                      backgroundPosition: "right 1rem center",
                      backgroundSize: "1.5rem",
                    }}
                  >
                    <option value="">请选择厂商</option>
                    {embeddingProviders.map((provider) => (
                      <option key={provider.id} value={provider.id}>
                        {provider.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label
                    className="block text-sm font-medium mb-2"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    模型
                  </label>
                  <select
                    value={selectedEmbeddingModel}
                    onChange={(e) => setSelectedEmbeddingModel(e.target.value)}
                    disabled={!selectedEmbeddingProvider}
                    className="w-full px-4 py-3 glass-input rounded-xl appearance-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{
                      color: "var(--text-primary)",
                      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='${encodeURIComponent("var(--text-muted)")}'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
                      backgroundRepeat: "no-repeat",
                      backgroundPosition: "right 1rem center",
                      backgroundSize: "1.5rem",
                    }}
                  >
                    <option value="">请先选择厂商</option>
                    {embeddingModels.map((model) => (
                      <option key={model.id} value={model.id}>
                        {model.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label
                    className="block text-sm font-medium mb-2"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    OpenRouter API Key
                  </label>
                  <div className="relative">
                    <input
                      type={showOpenrouterKey ? "text" : "password"}
                      value={openrouterApiKey}
                      onChange={(e) => setOpenrouterApiKey(e.target.value)}
                      placeholder="请输入您的OpenRouter API Key"
                      className="w-full px-4 py-3 pr-12 glass-input rounded-xl"
                      style={{ color: "var(--text-primary)" }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowOpenrouterKey(!showOpenrouterKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 transition-colors"
                      style={{ color: "var(--text-muted)" }}
                      onMouseEnter={(e) =>
                        (e.currentTarget.style.color = "var(--text-primary)")
                      }
                      onMouseLeave={(e) =>
                        (e.currentTarget.style.color = "var(--text-muted)")
                      }
                    >
                      {showOpenrouterKey ? (
                        <EyeOff size={18} />
                      ) : (
                        <Eye size={18} />
                      )}
                    </button>
                  </div>
                  <p
                    className="mt-2 text-xs"
                    style={{ color: "var(--text-muted)" }}
                  >
                    用于记忆搜索功能的向量嵌入生成
                  </p>
                </div>
              </div>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="flex justify-end mt-6"
          >
            <motion.button
              onClick={handleSave}
              disabled={isSaving}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="btn-primary flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{
                      duration: 1,
                      repeat: Infinity,
                      ease: "linear",
                    }}
                  >
                    <Loader2 size={18} />
                  </motion.div>
                  <span>保存中...</span>
                </>
              ) : (
                <>
                  <Save size={18} />
                  <span>保存设置</span>
                </>
              )}
            </motion.button>
          </motion.div>
        </div>
      </div>
    </MainLayout>
  );
};

export default SettingsPage;
