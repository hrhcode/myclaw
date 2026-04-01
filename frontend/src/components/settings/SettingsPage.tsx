import { useState, useEffect, useCallback, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, CheckCircle, Cpu, Eye, EyeOff, Loader2 } from "lucide-react";
import MainLayout from "../layout/MainLayout";
import {
  getBrowserConfig,
  getConfig,
  getEmbeddingProviderModels,
  getEmbeddingProviders,
  getProviderModels,
  getProviders,
  getWebSearchConfig,
  setBrowserConfig as setBrowserConfigApi,
  setConfig,
  setWebSearchConfig as setWebSearchConfigApi,
} from "../../services/api";
import type { BrowserConfig, WebSearchConfig } from "../../services/api";
import type { Model, Provider } from "../../types";
import { SectionCard } from "../admin";
import BrowserConfigPanel from "./BrowserConfigPanel";
import WebSearchConfigPanel from "./WebSearchConfigPanel";

const Toast: React.FC<{
  message: { type: "success" | "error"; text: string } | null;
}> = ({ message }) => (
  <AnimatePresence>
    {message ? (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="fixed top-4 left-1/2 -translate-x-1/2 z-50"
      >
        <SectionCard className="px-4 py-2">
          <div
            className="inline-flex items-center gap-2 text-sm"
            style={{ color: message.type === "success" ? "#16a34a" : "#dc2626" }}
          >
            {message.type === "success" ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
            <span>{message.text}</span>
          </div>
        </SectionCard>
      </motion.div>
    ) : null}
  </AnimatePresence>
);

const SettingsPage: React.FC = () => {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [embeddingProviders, setEmbeddingProviders] = useState<Provider[]>([]);
  const [embeddingModels, setEmbeddingModels] = useState<Model[]>([]);
  const [selectedProvider, setSelectedProvider] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [selectedEmbeddingProvider, setSelectedEmbeddingProvider] = useState("");
  const [selectedEmbeddingModel, setSelectedEmbeddingModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [openrouterApiKey, setOpenrouterApiKey] = useState("");
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

  const prevProviderRef = useRef("");
  const prevEmbeddingProviderRef = useRef("");

  const showMessage = (type: "success" | "error", text: string) => {
    setMessage({ type, text });
    window.setTimeout(() => setMessage(null), 2600);
  };

  const saveConfigItem = async (key: string, value: string, label: string) => {
    try {
      await setConfig(key, value);
      showMessage("success", `${label} 已保存`);
    } catch (error) {
      console.error(`Failed to save ${key}:`, error);
      showMessage("error", `${label} 保存失败`);
    }
  };

  const loadModels = useCallback(
    async (provider: string) => {
      try {
        const modelList = await getProviderModels(provider);
        setModels(modelList);
        if (selectedModel && !modelList.find((item) => item.id === selectedModel)) {
          setSelectedModel(modelList[0]?.id || "");
        } else if (!selectedModel && modelList.length > 0) {
          setSelectedModel(modelList[0].id);
        }
      } catch (error) {
        console.error("Failed to load models:", error);
      }
    },
    [selectedModel],
  );

  const loadEmbeddingModels = useCallback(
    async (provider: string) => {
      try {
        const modelList = await getEmbeddingProviderModels(provider);
        setEmbeddingModels(modelList);
        if (selectedEmbeddingModel && !modelList.find((item) => item.id === selectedEmbeddingModel)) {
          setSelectedEmbeddingModel(modelList[0]?.id || "");
        } else if (!selectedEmbeddingModel && modelList.length > 0) {
          setSelectedEmbeddingModel(modelList[0].id);
        }
      } catch (error) {
        console.error("Failed to load embedding models:", error);
      }
    },
    [selectedEmbeddingModel],
  );

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
      const savedOpenrouterKey = await getConfig("openrouter_api_key").catch(() => "");
      const savedEmbeddingProvider = await getConfig("embedding_provider").catch(() => "");
      const savedEmbeddingModel = await getConfig("embedding_model").catch(() => "");

      const nextProvider = savedProvider || providerList[0]?.id || "";
      setSelectedProvider(nextProvider);
      prevProviderRef.current = nextProvider;

      const nextEmbeddingProvider = savedEmbeddingProvider || embeddingProviderList[0]?.id || "";
      setSelectedEmbeddingProvider(nextEmbeddingProvider);
      prevEmbeddingProviderRef.current = nextEmbeddingProvider;

      setSelectedModel(savedModel || "");
      setSelectedEmbeddingModel(savedEmbeddingModel || "");
      setApiKey(savedApiKey || "");
      setOpenrouterApiKey(savedOpenrouterKey || "");

      try {
        const webSearch = await getWebSearchConfig();
        setWebSearchConfigState({
          enabled: webSearch.enabled,
          provider: webSearch.provider as WebSearchConfig["provider"],
          tavily_api_key: webSearch.tavily_api_key || "",
          brave_api_key: webSearch.brave_api_key || "",
          perplexity_api_key: webSearch.perplexity_api_key || "",
          max_results: webSearch.max_results,
          search_depth: webSearch.search_depth as WebSearchConfig["search_depth"],
          include_answer: webSearch.include_answer,
          timeout_seconds: webSearch.timeout_seconds,
          cache_ttl_minutes: webSearch.cache_ttl_minutes,
        });
        setExistingWebSearchKeys({
          tavily: !!webSearch.tavily_api_key,
          brave: !!webSearch.brave_api_key,
          perplexity: !!webSearch.perplexity_api_key,
        });
      } catch (error) {
        console.error("Failed to load web search config:", error);
      }

      try {
        const browser = await getBrowserConfig();
        setBrowserConfigState({
          default_type: browser.default_type,
          headless: browser.headless,
          viewport_width: browser.viewport_width,
          viewport_height: browser.viewport_height,
          timeout_ms: browser.timeout_ms,
          ssrf_allow_private: browser.ssrf_allow_private,
          ssrf_whitelist: browser.ssrf_whitelist,
          max_instances: browser.max_instances,
          idle_timeout_ms: browser.idle_timeout_ms,
          use_system_browser: browser.use_system_browser,
          system_browser_channel: browser.system_browser_channel,
        });
      } catch (error) {
        console.error("Failed to load browser config:", error);
      }
    } catch (error) {
      console.error("Failed to load settings:", error);
      showMessage("error", "设置加载失败");
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

  const handleProviderChange = async (value: string) => {
    setSelectedProvider(value);
    if (value && value !== prevProviderRef.current) {
      await saveConfigItem("llm_provider", value, "LLM 提供商");
      prevProviderRef.current = value;
    }
  };

  const handleModelChange = async (value: string) => {
    setSelectedModel(value);
    if (value) {
      await saveConfigItem("llm_model", value, "LLM 模型");
    }
  };

  const handleEmbeddingProviderChange = async (value: string) => {
    setSelectedEmbeddingProvider(value);
    if (value && value !== prevEmbeddingProviderRef.current) {
      await saveConfigItem("embedding_provider", value, "Embedding 提供商");
      prevEmbeddingProviderRef.current = value;
    }
  };

  const handleEmbeddingModelChange = async (value: string) => {
    setSelectedEmbeddingModel(value);
    if (value) {
      await saveConfigItem("embedding_model", value, "Embedding 模型");
    }
  };

  const handleApiKeyBlur = async () => {
    if (apiKey.trim()) {
      await saveConfigItem("zhipu_api_key", apiKey, "智谱 API Key");
    }
  };

  const handleOpenrouterKeyBlur = async () => {
    if (openrouterApiKey.trim()) {
      await saveConfigItem("openrouter_api_key", openrouterApiKey, "OpenRouter API Key");
    }
  };

  const handleWebSearchConfigChange = async (
    key: keyof WebSearchConfig,
    value: string | boolean | number,
  ) => {
    const next = { ...webSearchConfig, [key]: value };
    setWebSearchConfigState(next);
    try {
      await setWebSearchConfigApi(next);
      showMessage("success", "联网搜索配置已保存");
    } catch (error) {
      console.error("Failed to save web search config:", error);
      showMessage("error", "联网搜索配置保存失败");
    }
  };

  const handleSaveWebSearchKey = async (_key: keyof WebSearchConfig, value: string) => {
    const next = { ...webSearchConfig, tavily_api_key: value };
    setWebSearchConfigState(next);
    try {
      await setWebSearchConfigApi(next);
      setExistingWebSearchKeys((prev) => ({ ...prev, tavily: true }));
      showMessage("success", "Tavily API Key 已保存");
    } catch (error) {
      console.error("Failed to save tavily_api_key:", error);
      showMessage("error", "Tavily API Key 保存失败");
      throw error;
    }
  };

  const handleBrowserConfigChange = async (
    key: keyof BrowserConfig,
    value: string | boolean | number,
  ) => {
    const next = { ...browserConfig, [key]: value };
    setBrowserConfigState(next);
    try {
      await setBrowserConfigApi(next);
      showMessage("success", "浏览器配置已保存");
    } catch (error) {
      console.error("Failed to save browser config:", error);
      showMessage("error", "浏览器配置保存失败");
    }
  };

  if (isLoading) {
    return (
      <MainLayout headerTitle="设置">
        <div className="h-full flex items-center justify-center">
          <Loader2 size={40} className="text-primary animate-spin" />
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout headerTitle="设置">
      <Toast message={message} />
      <div className="admin-page">
        <div className="admin-frame">
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
            <SectionCard className="p-5">
              <div className="flex items-center gap-2 mb-4">
                <span className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: "var(--surface-subtle)" }}>
                  <Cpu size={16} />
                </span>
                <div>
                  <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                    LLM 配置
                  </h2>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    修改后自动保存
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-sm mb-1" style={{ color: "var(--text-secondary)" }}>
                    模型厂商
                  </label>
                  <select className="admin-select w-full px-3 py-2.5" value={selectedProvider} onChange={(e) => handleProviderChange(e.target.value)}>
                    <option value="">请选择厂商</option>
                    {providers.map((provider) => (
                      <option key={provider.id} value={provider.id}>
                        {provider.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm mb-1" style={{ color: "var(--text-secondary)" }}>
                    模型
                  </label>
                  <select
                    className="admin-select w-full px-3 py-2.5"
                    value={selectedModel}
                    onChange={(e) => handleModelChange(e.target.value)}
                    disabled={!selectedProvider}
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
                  <label className="block text-sm mb-1" style={{ color: "var(--text-secondary)" }}>
                    智谱 API Key
                  </label>
                  <div className="relative">
                    <input
                      type={showApiKey ? "text" : "password"}
                      className="admin-input w-full px-3 py-2.5 pr-10"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      onBlur={handleApiKeyBlur}
                      placeholder="输入后失焦自动保存"
                    />
                    <button
                      type="button"
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1"
                      onClick={() => setShowApiKey((prev) => !prev)}
                      style={{ color: "var(--text-muted)" }}
                    >
                      {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>
              </div>
            </SectionCard>

            <SectionCard className="p-5">
              <div className="flex items-center gap-2 mb-4">
                <span className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: "var(--surface-subtle)" }}>
                  <Cpu size={16} />
                </span>
                <div>
                  <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                    Embedding 配置
                  </h2>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    记忆检索使用
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-sm mb-1" style={{ color: "var(--text-secondary)" }}>
                    模型厂商
                  </label>
                  <select
                    className="admin-select w-full px-3 py-2.5"
                    value={selectedEmbeddingProvider}
                    onChange={(e) => handleEmbeddingProviderChange(e.target.value)}
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
                  <label className="block text-sm mb-1" style={{ color: "var(--text-secondary)" }}>
                    模型
                  </label>
                  <select
                    className="admin-select w-full px-3 py-2.5"
                    value={selectedEmbeddingModel}
                    onChange={(e) => handleEmbeddingModelChange(e.target.value)}
                    disabled={!selectedEmbeddingProvider}
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
                  <label className="block text-sm mb-1" style={{ color: "var(--text-secondary)" }}>
                    OpenRouter API Key
                  </label>
                  <div className="relative">
                    <input
                      type={showOpenrouterKey ? "text" : "password"}
                      className="admin-input w-full px-3 py-2.5 pr-10"
                      value={openrouterApiKey}
                      onChange={(e) => setOpenrouterApiKey(e.target.value)}
                      onBlur={handleOpenrouterKeyBlur}
                      placeholder="输入后失焦自动保存"
                    />
                    <button
                      type="button"
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1"
                      onClick={() => setShowOpenrouterKey((prev) => !prev)}
                      style={{ color: "var(--text-muted)" }}
                    >
                      {showOpenrouterKey ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>
              </div>
            </SectionCard>
          </div>

          <WebSearchConfigPanel
            config={webSearchConfig}
            onChange={handleWebSearchConfigChange}
            onSaveKey={handleSaveWebSearchKey}
            tavilyApiKeySet={existingWebSearchKeys.tavily}
          />

          <BrowserConfigPanel config={browserConfig} onChange={handleBrowserConfigChange} />
        </div>
      </div>
    </MainLayout>
  );
};

export default SettingsPage;
