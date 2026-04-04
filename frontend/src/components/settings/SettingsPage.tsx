import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, CheckCircle, Eye, EyeOff, Loader2 } from "lucide-react";

import MainLayout from "../layout/MainLayout";
import { SectionCard } from "../admin";
import SearchConfigPanel from "../memory/components/SearchConfigPanel";
import BrowserConfigPanel from "./BrowserConfigPanel";
import WebSearchConfigPanel from "./WebSearchConfigPanel";
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

const Toast: React.FC<{
  message: { type: "success" | "error"; text: string } | null;
}> = ({ message }) => (
  <AnimatePresence>
    {message ? (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="fixed left-1/2 top-4 z-50 -translate-x-1/2"
      >
        <SectionCard className="px-4 py-2">
          <div
            className="inline-flex items-center gap-2 text-sm"
            style={{
              color: message.type === "success" ? "#16a34a" : "#dc2626",
            }}
          >
            {message.type === "success" ? (
              <CheckCircle size={16} />
            ) : (
              <AlertCircle size={16} />
            )}
            <span>{message.text}</span>
          </div>
        </SectionCard>
      </motion.div>
    ) : null}
  </AnimatePresence>
);

const defaultWebSearchConfig: WebSearchConfig = {
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
};
const defaultBrowserConfig: BrowserConfig = {
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
};
type MemoryRetrievalConfig = {
  memory_top_k: string;
  memory_min_score: string;
  memory_use_hybrid: string;
  memory_vector_weight: string;
  memory_text_weight: string;
  memory_enable_mmr: string;
  memory_mmr_lambda: string;
  memory_enable_temporal_decay: string;
  memory_half_life_days: string;
};
const defaultMemoryRetrievalConfig: MemoryRetrievalConfig = {
  memory_top_k: "5",
  memory_min_score: "0.5",
  memory_use_hybrid: "true",
  memory_vector_weight: "0.7",
  memory_text_weight: "0.3",
  memory_enable_mmr: "true",
  memory_mmr_lambda: "0.7",
  memory_enable_temporal_decay: "true",
  memory_half_life_days: "30",
};
const MEMORY_RETRIEVAL_KEYS = Object.keys(
  defaultMemoryRetrievalConfig,
) as Array<keyof MemoryRetrievalConfig>;

const SettingsPage: React.FC = () => {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [embeddingProviders, setEmbeddingProviders] = useState<Provider[]>([]);
  const [embeddingModels, setEmbeddingModels] = useState<Model[]>([]);
  const [selectedProvider, setSelectedProvider] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [selectedEmbeddingProvider, setSelectedEmbeddingProvider] =
    useState("");
  const [selectedEmbeddingModel, setSelectedEmbeddingModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [openrouterApiKey, setOpenrouterApiKey] = useState("");
  const [showOpenrouterKey, setShowOpenrouterKey] = useState(false);
  const [webSearchConfig, setWebSearchConfigState] = useState<WebSearchConfig>(
    defaultWebSearchConfig,
  );
  const [existingWebSearchKeys, setExistingWebSearchKeys] = useState({
    tavily: false,
    brave: false,
    perplexity: false,
  });
  const [browserConfig, setBrowserConfigState] =
    useState<BrowserConfig>(defaultBrowserConfig);
  const [memoryRetrievalConfig, setMemoryRetrievalConfig] =
    useState<MemoryRetrievalConfig>(defaultMemoryRetrievalConfig);
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const prevProviderRef = useRef("");
  const prevEmbeddingProviderRef = useRef("");

  const showMessage = (type: "success" | "error", text: string) => {
    setMessage({ type, text });
    window.setTimeout(() => setMessage(null), 2400);
  };

  const saveConfigItem = async (key: string, value: string, label: string) => {
    try {
      await setConfig(key, value);
      showMessage("success", `${label}已保存`);
    } catch (error) {
      console.error(`Failed to save ${key}:`, error);
      showMessage("error", `${label}保存失败`);
    }
  };

  const loadModels = useCallback(
    async (provider: string) => {
      try {
        const modelList = await getProviderModels(provider);
        setModels(modelList);
        if (
          selectedModel &&
          !modelList.find((item) => item.id === selectedModel)
        )
          setSelectedModel(modelList[0]?.id || "");
        else if (!selectedModel && modelList.length > 0)
          setSelectedModel(modelList[0].id);
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
        if (
          selectedEmbeddingModel &&
          !modelList.find((item) => item.id === selectedEmbeddingModel)
        )
          setSelectedEmbeddingModel(modelList[0]?.id || "");
        else if (!selectedEmbeddingModel && modelList.length > 0)
          setSelectedEmbeddingModel(modelList[0].id);
      } catch (error) {
        console.error("Failed to load embedding models:", error);
      }
    },
    [selectedEmbeddingModel],
  );

  useEffect(() => {
    const loadSettings = async () => {
      try {
        setIsLoading(true);
        const providerList = await getProviders();
        const embeddingProviderList = await getEmbeddingProviders();
        setProviders(providerList);
        setEmbeddingProviders(embeddingProviderList);

        const entries = await Promise.all(
          MEMORY_RETRIEVAL_KEYS.map(
            async (key) =>
              [
                key,
                await getConfig(key).catch(
                  () => defaultMemoryRetrievalConfig[key],
                ),
              ] as const,
          ),
        );
        setMemoryRetrievalConfig(
          entries.reduce(
            (acc, [key, value]) => ({ ...acc, [key]: value }),
            defaultMemoryRetrievalConfig,
          ),
        );

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
        const nextProvider = savedProvider || providerList[0]?.id || "";
        const nextEmbeddingProvider =
          savedEmbeddingProvider || embeddingProviderList[0]?.id || "";

        setSelectedProvider(nextProvider);
        setSelectedModel(savedModel || "");
        setSelectedEmbeddingProvider(nextEmbeddingProvider);
        setSelectedEmbeddingModel(savedEmbeddingModel || "");
        setApiKey(savedApiKey || "");
        setOpenrouterApiKey(savedOpenrouterKey || "");
        prevProviderRef.current = nextProvider;
        prevEmbeddingProviderRef.current = nextEmbeddingProvider;

        const webSearch = await getWebSearchConfig().catch(
          () => defaultWebSearchConfig,
        );
        setWebSearchConfigState({
          ...defaultWebSearchConfig,
          ...webSearch,
          search_depth:
            webSearch.search_depth === "advanced" ? "advanced" : "basic",
          tavily_api_key: webSearch.tavily_api_key || "",
          brave_api_key: webSearch.brave_api_key || "",
          perplexity_api_key: webSearch.perplexity_api_key || "",
        });
        setExistingWebSearchKeys({
          tavily: !!webSearch.tavily_api_key,
          brave: !!webSearch.brave_api_key,
          perplexity: !!webSearch.perplexity_api_key,
        });
        setBrowserConfigState(
          await getBrowserConfig().catch(() => defaultBrowserConfig),
        );
      } catch (error) {
        console.error("Failed to load settings:", error);
        showMessage("error", "设置加载失败");
      } finally {
        setIsLoading(false);
      }
    };
    void loadSettings();
  }, []);

  useEffect(() => {
    if (selectedProvider) void loadModels(selectedProvider);
  }, [selectedProvider, loadModels]);
  useEffect(() => {
    if (selectedEmbeddingProvider)
      void loadEmbeddingModels(selectedEmbeddingProvider);
  }, [selectedEmbeddingProvider, loadEmbeddingModels]);

  const handleProviderChange = async (value: string) => {
    setSelectedProvider(value);
    if (value && value !== prevProviderRef.current) {
      await saveConfigItem("llm_provider", value, "对话模型提供方");
      prevProviderRef.current = value;
    }
  };

  const handleEmbeddingProviderChange = async (value: string) => {
    setSelectedEmbeddingProvider(value);
    if (value && value !== prevEmbeddingProviderRef.current) {
      await saveConfigItem("embedding_provider", value, "向量模型提供方");
      prevEmbeddingProviderRef.current = value;
    }
  };

  if (isLoading) {
    return (
      <MainLayout headerTitle="配置" headerSubtitle="统一管理模型、工具与检索">
        <div className="flex h-full items-center justify-center">
          <Loader2 size={40} className="animate-spin text-primary" />
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout
      headerTitle="配置"
      headerSubtitle="更克制、更紧凑的全局配置台。"
    >
      <Toast message={message} />
      <div className="admin-page">
        <div className="admin-frame settings-page-shell settings-page-shell--minimal">
          <div className="settings-rows">
            <div className="settings-row-2col">
              <div className="settings-block">
                <div className="settings-block__head">
                  <h3>对话模型</h3>
                  <span>生成</span>
                </div>
                <div className="settings-stack">
                  <div className="settings-field">
                    <label>提供方</label>
                    <select
                      className="admin-select w-full px-3 py-2.5"
                      value={selectedProvider}
                      onChange={(e) =>
                        void handleProviderChange(e.target.value)
                      }
                    >
                      <option value="">请选择厂商</option>
                      {providers.map((provider) => (
                        <option key={provider.id} value={provider.id}>
                          {provider.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="settings-field">
                    <label>模型</label>
                    <select
                      className="admin-select w-full px-3 py-2.5"
                      value={selectedModel}
                      onChange={(e) => {
                        setSelectedModel(e.target.value);
                        void saveConfigItem(
                          "llm_model",
                          e.target.value,
                          "对话模型",
                        );
                      }}
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
                  <div className="settings-field">
                    <label>智谱 API Key</label>
                    <div className="relative">
                      <input
                        type={showApiKey ? "text" : "password"}
                        className="admin-input w-full px-3 py-2.5 pr-10"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        onBlur={() =>
                          void (
                            apiKey.trim() &&
                            saveConfigItem(
                              "zhipu_api_key",
                              apiKey,
                              "智谱 API Key",
                            )
                          )
                        }
                        placeholder="输入后自动保存"
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
              </div>

              <div className="settings-block">
                <div className="settings-block__head">
                  <h3>向量模型</h3>
                  <span>检索</span>
                </div>
                <div className="settings-stack">
                  <div className="settings-field">
                    <label>提供方</label>
                    <select
                      className="admin-select w-full px-3 py-2.5"
                      value={selectedEmbeddingProvider}
                      onChange={(e) =>
                        void handleEmbeddingProviderChange(e.target.value)
                      }
                    >
                      <option value="">请选择厂商</option>
                      {embeddingProviders.map((provider) => (
                        <option key={provider.id} value={provider.id}>
                          {provider.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="settings-field">
                    <label>模型</label>
                    <select
                      className="admin-select w-full px-3 py-2.5"
                      value={selectedEmbeddingModel}
                      onChange={(e) => {
                        setSelectedEmbeddingModel(e.target.value);
                        void saveConfigItem(
                          "embedding_model",
                          e.target.value,
                          "向量模型",
                        );
                      }}
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
                  <div className="settings-field">
                    <label>OpenRouter API Key</label>
                    <div className="relative">
                      <input
                        type={showOpenrouterKey ? "text" : "password"}
                        className="admin-input w-full px-3 py-2.5 pr-10"
                        value={openrouterApiKey}
                        onChange={(e) => setOpenrouterApiKey(e.target.value)}
                        onBlur={() =>
                          void (
                            openrouterApiKey.trim() &&
                            saveConfigItem(
                              "openrouter_api_key",
                              openrouterApiKey,
                              "OpenRouter API Key",
                            )
                          )
                        }
                        placeholder="输入后自动保存"
                      />
                      <button
                        type="button"
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1"
                        onClick={() => setShowOpenrouterKey((prev) => !prev)}
                        style={{ color: "var(--text-muted)" }}
                      >
                        {showOpenrouterKey ? (
                          <EyeOff size={16} />
                        ) : (
                          <Eye size={16} />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="settings-row-2col">
              <WebSearchConfigPanel
                config={webSearchConfig}
                onChange={async (key, value) => {
                  const next = { ...webSearchConfig, [key]: value };
                  setWebSearchConfigState(next);
                  try {
                    await setWebSearchConfigApi(next);
                    showMessage("success", "联网搜索配置已保存");
                  } catch (error) {
                    console.error("Failed to save web search config:", error);
                    showMessage("error", "联网搜索配置保存失败");
                  }
                }}
                onSaveKey={async (key, value) => {
                  const next = { ...webSearchConfig, [key]: value };
                  setWebSearchConfigState(next);
                  await setWebSearchConfigApi(next);
                  setExistingWebSearchKeys((prev) => ({
                    ...prev,
                    tavily: key === "tavily_api_key" ? true : prev.tavily,
                    brave: key === "brave_api_key" ? true : prev.brave,
                    perplexity:
                      key === "perplexity_api_key" ? true : prev.perplexity,
                  }));
                  showMessage("success", "搜索服务密钥已保存");
                }}
                tavilyApiKeySet={existingWebSearchKeys.tavily}
              />

              <SearchConfigPanel
                config={memoryRetrievalConfig}
                onChange={async (key, value) => {
                  setMemoryRetrievalConfig((prev) => ({
                    ...prev,
                    [key]: value,
                  }));
                  try {
                    await setConfig(key, value);
                  } catch (error) {
                    console.error(`Failed to save ${key}:`, error);
                    showMessage("error", "知识库检索配置保存失败");
                  }
                }}
              />
            </div>

            <div className="settings-row-1col">
              <BrowserConfigPanel
                config={browserConfig}
                onChange={async (key, value) => {
                  const next = { ...browserConfig, [key]: value };
                  setBrowserConfigState(next);
                  try {
                    await setBrowserConfigApi(next);
                    showMessage("success", "浏览器配置已保存");
                  } catch (error) {
                    console.error("Failed to save browser config:", error);
                    showMessage("error", "浏览器配置保存失败");
                  }
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default SettingsPage;
