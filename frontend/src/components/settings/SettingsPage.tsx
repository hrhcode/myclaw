import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
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
  getWebSearchConfig,
  setWebSearchConfig as setWebSearchConfigApi,
  getBrowserConfig,
  setBrowserConfig as setBrowserConfigApi,
} from "../../services/api";
import type { Provider, Model } from "../../types";
import type { WebSearchConfig, BrowserConfig } from "../../services/api";
import WebSearchConfigPanel from "./WebSearchConfigPanel";
import BrowserConfigPanel from "./BrowserConfigPanel";

/**
 * Toast 通知组件 - 固定在屏幕中上角
 */
const Toast: React.FC<{
  message: { type: "success" | "error"; text: string } | null;
}> = ({ message }) => {
  return (
    <AnimatePresence>
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className={`fixed top-4 left-1/2 -translate-x-1/2 z-50 px-4 py-3 rounded-xl flex items-center gap-3 shadow-lg ${
            message.type === "success"
              ? "bg-green-500/20 border border-green-500/30 text-green-400"
              : "bg-red-500/20 border border-red-500/30 text-red-400"
          }`}
        >
          {message.type === "success" ? (
            <CheckCircle size={18} />
          ) : (
            <AlertCircle size={18} />
          )}
          <span className="text-sm">{message.text}</span>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

/**
 * 配置页面组件 - 配置API和模型参数
 * 采用玻璃拟态设计，支持动画效果和主题切换
 * 实时保存配置，无需手动点击保存按钮
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
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const [webSearchConfig, setWebSearchConfigState] = useState<WebSearchConfig>({
    enabled: false,
    provider: "tavily",
    tavily_api_key: "",
    brave_api_key: "",
    perplexity_api_key: "",
    max_results: 5,
    search_depth: "basic",
    include_answer: true,
    timeout_seconds: 30,
    cache_ttl_minutes: 15,
  });
  const [existingWebSearchKeys, setExistingWebSearchKeys] = useState({
    tavily: false,
    brave: false,
    perplexity: false,
  });

  const [browserConfig, setBrowserConfigState] = useState<BrowserConfig>({
    default_type: "chromium",
    headless: false,
    viewport_width: 1280,
    viewport_height: 720,
    timeout_ms: 30000,
    ssrf_allow_private: false,
    ssrf_whitelist: "",
    max_instances: 1,
    idle_timeout_ms: 300000,
    use_system_browser: true,
    system_browser_channel: "chrome",
  });

  const prevProviderRef = useRef<string>("");
  const prevEmbeddingProviderRef = useRef<string>("");

  /**
   * 显示保存状态提示
   */
  const showMessage = (type: "success" | "error", text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  /**
   * 保存单个配置项
   */
  const saveConfigItem = async (key: string, value: string) => {
    try {
      await setConfig(key, value);
      showMessage("success", `${key} 已保存`);
    } catch (error) {
      console.error(`Failed to save ${key}:`, error);
      showMessage("error", `保存 ${key} 失败`);
    }
  };

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
        prevProviderRef.current = savedProvider;
      } else if (providerList.length > 0) {
        setSelectedProvider(providerList[0].id);
        prevProviderRef.current = providerList[0].id;
      }

      if (savedEmbeddingProvider) {
        setSelectedEmbeddingProvider(savedEmbeddingProvider);
        prevEmbeddingProviderRef.current = savedEmbeddingProvider;
      } else if (embeddingProviderList.length > 0) {
        setSelectedEmbeddingProvider(embeddingProviderList[0].id);
        prevEmbeddingProviderRef.current = embeddingProviderList[0].id;
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

      try {
        const webSearchCfg = await getWebSearchConfig();
        // 使用函数式更新避免依赖旧的 state
        const newWebSearchConfig = {
          enabled: webSearchCfg.enabled,
          provider: webSearchCfg.provider as WebSearchConfig["provider"],
          tavily_api_key: webSearchCfg.tavily_api_key || "",
          brave_api_key: webSearchCfg.brave_api_key || "",
          perplexity_api_key: webSearchCfg.perplexity_api_key || "",
          max_results: webSearchCfg.max_results,
          search_depth:
            webSearchCfg.search_depth as WebSearchConfig["search_depth"],
          include_answer: webSearchCfg.include_answer,
          timeout_seconds: webSearchCfg.timeout_seconds,
          cache_ttl_minutes: webSearchCfg.cache_ttl_minutes,
        };
        // 注意：这里不能直接调用 setWebSearchConfig，因为它被 useState 覆盖了
        // 我们需要使用一个不同的变量名来存储状态设置函数
        setWebSearchConfigState(newWebSearchConfig);
        setExistingWebSearchKeys({
          tavily: !!webSearchCfg.tavily_api_key,
          brave: !!webSearchCfg.brave_api_key,
          perplexity: !!webSearchCfg.perplexity_api_key,
        });
      } catch (error) {
        console.error("Failed to load web search config:", error);
      }

      try {
        const browserCfg = await getBrowserConfig();
        setBrowserConfigState({
          default_type: browserCfg.default_type,
          headless: browserCfg.headless,
          viewport_width: browserCfg.viewport_width,
          viewport_height: browserCfg.viewport_height,
          timeout_ms: browserCfg.timeout_ms,
          ssrf_allow_private: browserCfg.ssrf_allow_private,
          ssrf_whitelist: browserCfg.ssrf_whitelist,
          max_instances: browserCfg.max_instances,
          idle_timeout_ms: browserCfg.idle_timeout_ms,
          use_system_browser: browserCfg.use_system_browser,
          system_browser_channel: browserCfg.system_browser_channel,
        });
      } catch (error) {
        console.error("Failed to load browser config:", error);
      }
    } catch (error) {
      console.error("Failed to load settings:", error);
      showMessage("error", "加载设置失败");
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
   * 处理 LLM 提供商变更（实时保存）
   */
  const handleProviderChange = async (value: string) => {
    setSelectedProvider(value);
    if (value && value !== prevProviderRef.current) {
      await saveConfigItem("llm_provider", value);
      prevProviderRef.current = value;
    }
  };

  /**
   * 处理 LLM 模型变更（实时保存）
   */
  const handleModelChange = async (value: string) => {
    setSelectedModel(value);
    if (value) {
      await saveConfigItem("llm_model", value);
    }
  };

  /**
   * 处理 Embedding 提供商变更（实时保存）
   */
  const handleEmbeddingProviderChange = async (value: string) => {
    setSelectedEmbeddingProvider(value);
    if (value && value !== prevEmbeddingProviderRef.current) {
      await saveConfigItem("embedding_provider", value);
      prevEmbeddingProviderRef.current = value;
    }
  };

  /**
   * 处理 Embedding 模型变更（实时保存）
   */
  const handleEmbeddingModelChange = async (value: string) => {
    setSelectedEmbeddingModel(value);
    if (value) {
      await saveConfigItem("embedding_model", value);
    }
  };

  /**
   * 处理 API Key 失焦保存
   */
  const handleApiKeyBlur = async () => {
    if (apiKey.trim()) {
      await saveConfigItem("zhipu_api_key", apiKey);
    }
  };

  /**
   * 处理 OpenRouter API Key 失焦保存
   */
  const handleOpenrouterKeyBlur = async () => {
    if (openrouterApiKey.trim()) {
      await saveConfigItem("openrouter_api_key", openrouterApiKey);
    }
  };

  /**
   * 处理网络搜索配置变更（实时保存）
   */
  const handleWebSearchConfigChange = async (
    key: keyof WebSearchConfig,
    value: string | boolean | number,
  ) => {
    const newConfig = {
      ...webSearchConfig,
      [key]: value,
    };
    setWebSearchConfigState(newConfig);

    try {
      await setWebSearchConfigApi(newConfig);
      showMessage("success", "网络搜索配置已保存");
    } catch (error) {
      console.error("Failed to save web search config:", error);
      showMessage("error", "保存网络搜索配置失败");
    }
  };

  /**
   * 处理网络搜索 API Key 保存
   */
  const handleSaveWebSearchKey = async (
    _key: keyof WebSearchConfig,
    value: string,
  ) => {
    const newConfig = {
      ...webSearchConfig,
      tavily_api_key: value,
    };
    setWebSearchConfigState(newConfig);

    try {
      await setWebSearchConfigApi(newConfig);
      showMessage("success", "Tavily API Key 已保存");
      setExistingWebSearchKeys((prev) => ({
        ...prev,
        tavily: true,
      }));
    } catch (error) {
      console.error(`Failed to save tavily_api_key:`, error);
      showMessage("error", "保存 API Key 失败");
      throw error;
    }
  };

  /**
   * 处理浏览器配置变更（实时保存）
   */
  const handleBrowserConfigChange = async (
    key: keyof BrowserConfig,
    value: string | boolean | number,
  ) => {
    const newConfig = {
      ...browserConfig,
      [key]: value,
    };
    setBrowserConfigState(newConfig);

    try {
      await setBrowserConfigApi(newConfig);
      showMessage("success", "浏览器配置已保存");
    } catch (error) {
      console.error("Failed to save browser config:", error);
      showMessage("error", "保存浏览器配置失败");
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
      <Toast message={message} />
      <div className="h-full overflow-y-auto p-6">
        <div className="max-w-6xl mx-auto pb-8">
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
                    选择AI模型提供商和模型（自动保存）
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
                    onChange={(e) => handleProviderChange(e.target.value)}
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
                    onChange={(e) => handleModelChange(e.target.value)}
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
                      onBlur={handleApiKeyBlur}
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
                    用于智谱AI聊天功能，输入后点击其他位置自动保存
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
                    向量嵌入模型（用于记忆搜索，自动保存）
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
                      handleEmbeddingProviderChange(e.target.value)
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
                    onChange={(e) => handleEmbeddingModelChange(e.target.value)}
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
                      onBlur={handleOpenrouterKeyBlur}
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
                    用于记忆搜索功能的向量嵌入生成，输入后点击其他位置自动保存
                  </p>
                </div>
              </div>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="w-full mt-6"
          >
            <WebSearchConfigPanel
              config={webSearchConfig}
              onChange={handleWebSearchConfigChange}
              onSaveKey={handleSaveWebSearchKey}
              tavilyApiKeySet={existingWebSearchKeys.tavily}
            />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="w-full mt-6"
          >
            <BrowserConfigPanel
              config={browserConfig}
              onChange={handleBrowserConfigChange}
            />
          </motion.div>
        </div>
      </div>
    </MainLayout>
  );
};

export default SettingsPage;
