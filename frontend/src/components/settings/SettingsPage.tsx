import { useState, useEffect, useCallback, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, CheckCircle, Cpu, Eye, EyeOff, Loader2 } from "lucide-react";

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
  getGlobalRuntimeConfig,
  getGlobalSkills,
  getProviderModels,
  getProviders,
  getSkills,
  getWebSearchConfig,
  setBrowserConfig as setBrowserConfigApi,
  setConfig,
  setWebSearchConfig as setWebSearchConfigApi,
  updateGlobalRuntimeConfig,
  updateGlobalSkills,
} from "../../services/api";
import type { BrowserConfig, GlobalRuntimeConfig, WebSearchConfig } from "../../services/api";
import type { Model, Provider, SessionSkill, Skill } from "../../types";

const Toast: React.FC<{
  message: { type: "success" | "error"; text: string } | null;
}> = ({ message }) => (
  <AnimatePresence>
    {message ? (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="fixed top-4 left-1/2 z-50 -translate-x-1/2"
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

const defaultRuntimeConfig: GlobalRuntimeConfig = {
  workspace_path: "",
  memory_auto_extract: false,
  memory_threshold: 8,
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
  const [selectedEmbeddingProvider, setSelectedEmbeddingProvider] = useState("");
  const [selectedEmbeddingModel, setSelectedEmbeddingModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [openrouterApiKey, setOpenrouterApiKey] = useState("");
  const [showOpenrouterKey, setShowOpenrouterKey] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [webSearchConfig, setWebSearchConfigState] = useState<WebSearchConfig>(defaultWebSearchConfig);
  const [existingWebSearchKeys, setExistingWebSearchKeys] = useState({
    tavily: false,
    brave: false,
    perplexity: false,
  });
  const [browserConfig, setBrowserConfigState] = useState<BrowserConfig>(defaultBrowserConfig);
  const [runtimeConfig, setRuntimeConfig] = useState<GlobalRuntimeConfig>(defaultRuntimeConfig);
  const [memoryRetrievalConfig, setMemoryRetrievalConfig] = useState<MemoryRetrievalConfig>(
    defaultMemoryRetrievalConfig,
  );
  const [availableSkills, setAvailableSkills] = useState<Skill[]>([]);
  const [enabledSkills, setEnabledSkills] = useState<SessionSkill[]>([]);

  const prevProviderRef = useRef("");
  const prevEmbeddingProviderRef = useRef("");

  const showMessage = (type: "success" | "error", text: string) => {
    setMessage({ type, text });
    window.setTimeout(() => setMessage(null), 2600);
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

  const saveRuntimeConfig = async (changes: Partial<GlobalRuntimeConfig>, label: string) => {
    try {
      const updated = await updateGlobalRuntimeConfig(changes);
      setRuntimeConfig({
        workspace_path: updated.workspace_path || "",
        memory_auto_extract: updated.memory_auto_extract,
        memory_threshold: updated.memory_threshold,
      });
      showMessage("success", `${label}已保存`);
    } catch (error) {
      console.error(`Failed to save runtime config ${label}:`, error);
      showMessage("error", `${label}保存失败`);
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

      try {
        const [runtime, skills, activeSkills] = await Promise.all([
          getGlobalRuntimeConfig(),
          getSkills(),
          getGlobalSkills(),
        ]);
        setRuntimeConfig({
          workspace_path: runtime.workspace_path || "",
          memory_auto_extract: runtime.memory_auto_extract,
          memory_threshold: runtime.memory_threshold,
        });
        setAvailableSkills(skills);
        setEnabledSkills(activeSkills);
      } catch (error) {
        console.error("Failed to load global runtime settings:", error);
      }

      try {
        const entries = await Promise.all(
          MEMORY_RETRIEVAL_KEYS.map(async (key) => {
            const value = await getConfig(key).catch(() => defaultMemoryRetrievalConfig[key]);
            return [key, value] as const;
          }),
        );
        const nextConfig = entries.reduce(
          (acc, [key, value]) => ({ ...acc, [key]: value }),
          defaultMemoryRetrievalConfig,
        );
        setMemoryRetrievalConfig(nextConfig);
      } catch (error) {
        console.error("Failed to load memory retrieval config:", error);
      }

      const savedProvider = await getConfig("llm_provider").catch(() => "");
      const savedModel = await getConfig("llm_model").catch(() => "");
      const savedApiKey = await getConfig("zhipu_api_key").catch(() => "");
      const savedOpenrouterKey = await getConfig("openrouter_api_key").catch(() => "");
      const savedEmbeddingProvider = await getConfig("embedding_provider").catch(() => "");
      const savedEmbeddingModel = await getConfig("embedding_model").catch(() => "");

      const nextProvider = savedProvider || providerList[0]?.id || "";
      const nextEmbeddingProvider = savedEmbeddingProvider || embeddingProviderList[0]?.id || "";

      setSelectedProvider(nextProvider);
      setSelectedModel(savedModel || "");
      setSelectedEmbeddingProvider(nextEmbeddingProvider);
      setSelectedEmbeddingModel(savedEmbeddingModel || "");
      setApiKey(savedApiKey || "");
      setOpenrouterApiKey(savedOpenrouterKey || "");
      prevProviderRef.current = nextProvider;
      prevEmbeddingProviderRef.current = nextEmbeddingProvider;

      try {
        const webSearch = await getWebSearchConfig();
        setWebSearchConfigState({
          enabled: webSearch.enabled,
          provider: webSearch.provider,
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
        setBrowserConfigState(browser);
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
    void loadSettings();
  }, []);

  useEffect(() => {
    if (selectedProvider) {
      void loadModels(selectedProvider);
    }
  }, [selectedProvider, loadModels]);

  useEffect(() => {
    if (selectedEmbeddingProvider) {
      void loadEmbeddingModels(selectedEmbeddingProvider);
    }
  }, [selectedEmbeddingProvider, loadEmbeddingModels]);

  const handleProviderChange = async (value: string) => {
    setSelectedProvider(value);
    if (value && value !== prevProviderRef.current) {
      await saveConfigItem("llm_provider", value, "对话模型提供方");
      prevProviderRef.current = value;
    }
  };

  const handleModelChange = async (value: string) => {
    setSelectedModel(value);
    if (value) {
      await saveConfigItem("llm_model", value, "对话模型");
    }
  };

  const handleEmbeddingProviderChange = async (value: string) => {
    setSelectedEmbeddingProvider(value);
    if (value && value !== prevEmbeddingProviderRef.current) {
      await saveConfigItem("embedding_provider", value, "向量模型提供方");
      prevEmbeddingProviderRef.current = value;
    }
  };

  const handleEmbeddingModelChange = async (value: string) => {
    setSelectedEmbeddingModel(value);
    if (value) {
      await saveConfigItem("embedding_model", value, "向量模型");
    }
  };

  const handleApiKeyBlur = async () => {
    if (apiKey.trim()) {
      await saveConfigItem("zhipu_api_key", apiKey, "智谱接口密钥");
    }
  };

  const handleOpenrouterKeyBlur = async () => {
    if (openrouterApiKey.trim()) {
      await saveConfigItem("openrouter_api_key", openrouterApiKey, "OpenRouter 接口密钥");
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

  const handleSaveWebSearchKey = async (key: keyof WebSearchConfig, value: string) => {
    const next = { ...webSearchConfig, [key]: value };
    setWebSearchConfigState(next);
    try {
      await setWebSearchConfigApi(next);
      setExistingWebSearchKeys((prev) => ({
        ...prev,
        tavily: key === "tavily_api_key" ? true : prev.tavily,
        brave: key === "brave_api_key" ? true : prev.brave,
        perplexity: key === "perplexity_api_key" ? true : prev.perplexity,
      }));
      showMessage("success", "搜索服务接口密钥已保存");
    } catch (error) {
      console.error(`Failed to save ${String(key)}:`, error);
      showMessage("error", "搜索服务接口密钥保存失败");
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

  const handleMemoryRetrievalChange = async (
    key: keyof MemoryRetrievalConfig,
    value: string,
  ) => {
    setMemoryRetrievalConfig((prev) => ({ ...prev, [key]: value }));
    try {
      await setConfig(key, value);
    } catch (error) {
      console.error(`Failed to save ${key}:`, error);
      showMessage("error", "记忆检索设置保存失败");
    }
  };

  const handleToggleSkill = async (skill: Skill, checked: boolean) => {
    const nextSkills = checked
      ? [
          ...enabledSkills.filter((item) => item.skill_name !== skill.name),
          { skill_name: skill.name, skill_path: skill.path, enabled: true },
        ]
      : enabledSkills.filter((item) => item.skill_name !== skill.name);

    setEnabledSkills(nextSkills);
    try {
      const updated = await updateGlobalSkills(nextSkills);
      setEnabledSkills(updated);
      showMessage("success", "全局技能设置已保存");
    } catch (error) {
      console.error("Failed to update global skills:", error);
      showMessage("error", "全局技能设置保存失败");
    }
  };

  if (isLoading) {
    return (
      <MainLayout headerTitle="设置">
        <div className="flex h-full items-center justify-center">
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
          <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
            <SectionCard className="p-5">
              <div className="mb-4 flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ backgroundColor: "var(--surface-subtle)" }}>
                  <Cpu size={16} />
                </span>
                <div>
                  <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>对话模型配置</h2>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>修改后自动保存</p>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="mb-1 block text-sm" style={{ color: "var(--text-secondary)" }}>服务提供方</label>
                  <select className="admin-select w-full px-3 py-2.5" value={selectedProvider} onChange={(e) => void handleProviderChange(e.target.value)}>
                    <option value="">请选择厂商</option>
                    {providers.map((provider) => (
                      <option key={provider.id} value={provider.id}>{provider.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-sm" style={{ color: "var(--text-secondary)" }}>模型</label>
                  <select className="admin-select w-full px-3 py-2.5" value={selectedModel} onChange={(e) => void handleModelChange(e.target.value)} disabled={!selectedProvider}>
                    <option value="">请先选择厂商</option>
                    {models.map((model) => (
                      <option key={model.id} value={model.id}>{model.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-sm" style={{ color: "var(--text-secondary)" }}>智谱接口密钥</label>
                  <div className="relative">
                    <input
                      type={showApiKey ? "text" : "password"}
                      className="admin-input w-full px-3 py-2.5 pr-10"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      onBlur={() => void handleApiKeyBlur()}
                      placeholder="输入后失焦自动保存"
                    />
                    <button type="button" className="absolute right-2 top-1/2 -translate-y-1/2 p-1" onClick={() => setShowApiKey((prev) => !prev)} style={{ color: "var(--text-muted)" }}>
                      {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>
              </div>
            </SectionCard>

            <SectionCard className="p-5">
              <div className="mb-4 flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ backgroundColor: "var(--surface-subtle)" }}>
                  <Cpu size={16} />
                </span>
                <div>
                  <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>向量模型配置</h2>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>用于记忆检索</p>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="mb-1 block text-sm" style={{ color: "var(--text-secondary)" }}>服务提供方</label>
                  <select className="admin-select w-full px-3 py-2.5" value={selectedEmbeddingProvider} onChange={(e) => void handleEmbeddingProviderChange(e.target.value)}>
                    <option value="">请选择厂商</option>
                    {embeddingProviders.map((provider) => (
                      <option key={provider.id} value={provider.id}>{provider.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-sm" style={{ color: "var(--text-secondary)" }}>模型</label>
                  <select className="admin-select w-full px-3 py-2.5" value={selectedEmbeddingModel} onChange={(e) => void handleEmbeddingModelChange(e.target.value)} disabled={!selectedEmbeddingProvider}>
                    <option value="">请先选择厂商</option>
                    {embeddingModels.map((model) => (
                      <option key={model.id} value={model.id}>{model.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-sm" style={{ color: "var(--text-secondary)" }}>OpenRouter 接口密钥</label>
                  <div className="relative">
                    <input
                      type={showOpenrouterKey ? "text" : "password"}
                      className="admin-input w-full px-3 py-2.5 pr-10"
                      value={openrouterApiKey}
                      onChange={(e) => setOpenrouterApiKey(e.target.value)}
                      onBlur={() => void handleOpenrouterKeyBlur()}
                      placeholder="输入后失焦自动保存"
                    />
                    <button type="button" className="absolute right-2 top-1/2 -translate-y-1/2 p-1" onClick={() => setShowOpenrouterKey((prev) => !prev)} style={{ color: "var(--text-muted)" }}>
                      {showOpenrouterKey ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>
              </div>
            </SectionCard>
          </div>

          <WebSearchConfigPanel config={webSearchConfig} onChange={handleWebSearchConfigChange} onSaveKey={handleSaveWebSearchKey} tavilyApiKeySet={existingWebSearchKeys.tavily} />

          <SectionCard className="p-5">
            <div className="mb-4 flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ backgroundColor: "var(--surface-subtle)" }}>
                <Cpu size={16} />
              </span>
              <div>
                <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>记忆与检索</h2>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>控制知识库与历史消息的 RAG 召回策略</p>
              </div>
            </div>
            <SearchConfigPanel config={memoryRetrievalConfig} onChange={handleMemoryRetrievalChange} />
          </SectionCard>

          <SectionCard className="p-5">
            <div className="mb-4 flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ backgroundColor: "var(--surface-subtle)" }}>
                <Cpu size={16} />
              </span>
              <div>
                <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>全局运行配置</h2>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>统一控制工作目录、记忆提炼和全局技能</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="mb-1 block text-sm" style={{ color: "var(--text-secondary)" }}>工作目录</label>
                <input
                  className="admin-input w-full px-3 py-2.5"
                  value={runtimeConfig.workspace_path || ""}
                  onChange={(event) => setRuntimeConfig((prev) => ({ ...prev, workspace_path: event.target.value }))}
                  onBlur={() => void saveRuntimeConfig({ workspace_path: runtimeConfig.workspace_path || "" }, "工作目录")}
                  placeholder="请输入统一工作目录"
                />
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <label className="flex items-center justify-between rounded-xl border px-3 py-2.5" style={{ borderColor: "var(--panel-border)" }}>
                  <span style={{ color: "var(--text-secondary)" }}>自动提炼记忆</span>
                  <input
                    type="checkbox"
                    checked={runtimeConfig.memory_auto_extract}
                    onChange={(event) => {
                      const checked = event.target.checked;
                      setRuntimeConfig((prev) => ({ ...prev, memory_auto_extract: checked }));
                      void saveRuntimeConfig({ memory_auto_extract: checked }, "自动提炼记忆");
                    }}
                  />
                </label>

                <div>
                  <label className="mb-1 block text-sm" style={{ color: "var(--text-secondary)" }}>记忆提炼阈值</label>
                  <input
                    type="number"
                    min={1}
                    className="admin-input w-full px-3 py-2.5"
                    value={runtimeConfig.memory_threshold}
                    onChange={(event) => setRuntimeConfig((prev) => ({ ...prev, memory_threshold: Number.parseInt(event.target.value || "1", 10) }))}
                    onBlur={() => void saveRuntimeConfig({ memory_threshold: runtimeConfig.memory_threshold }, "记忆提炼阈值")}
                  />
                </div>
              </div>

              <div>
                <div className="mb-2 text-sm" style={{ color: "var(--text-secondary)" }}>全局技能</div>
                <div className="space-y-2">
                  {availableSkills.map((skill) => {
                    const checked = enabledSkills.some((item) => item.skill_name === skill.name && item.enabled);
                    return (
                      <label key={skill.name} className="flex items-start justify-between gap-3 rounded-xl border px-3 py-2.5" style={{ borderColor: "var(--panel-border)" }}>
                        <div>
                          <div className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{skill.name}</div>
                          <div className="text-xs" style={{ color: "var(--text-muted)" }}>{skill.description}</div>
                        </div>
                        <input type="checkbox" checked={checked} onChange={(event) => void handleToggleSkill(skill, event.target.checked)} />
                      </label>
                    );
                  })}
                </div>
              </div>
            </div>
          </SectionCard>

          <BrowserConfigPanel config={browserConfig} onChange={handleBrowserConfigChange} />
        </div>
      </div>
    </MainLayout>
  );
};

export default SettingsPage;
