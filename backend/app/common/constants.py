"""
常量定义模块
集中管理所有应用常量
"""

# API配置键
API_KEY_KEY = "zhipu_api_key"
LLM_MODEL_KEY = "llm_model"
LLM_PROVIDER_KEY = "llm_provider"
OPENROUTER_API_KEY_KEY = "openrouter_api_key"
EMBEDDING_PROVIDER_KEY = "embedding_provider"
EMBEDDING_MODEL_KEY = "embedding_model"

# 网络搜索配置键
WEB_SEARCH_PROVIDER_KEY = "web_search_provider"
TAVILY_API_KEY_KEY = "tavily_api_key"
WEB_SEARCH_MAX_RESULTS_KEY = "web_search_max_results"
WEB_SEARCH_DEPTH_KEY = "web_search_depth"
WEB_SEARCH_INCLUDE_ANSWER_KEY = "web_search_include_answer"
WEB_SEARCH_TIMEOUT_KEY = "web_search_timeout"
WEB_SEARCH_CACHE_TTL_KEY = "web_search_cache_ttl"

# 浏览器配置键
BROWSER_ENABLED_KEY = "browser_enabled"
BROWSER_DEFAULT_TYPE_KEY = "browser_default_type"
BROWSER_HEADLESS_KEY = "browser_headless"
BROWSER_VIEWPORT_WIDTH_KEY = "browser_viewport_width"
BROWSER_VIEWPORT_HEIGHT_KEY = "browser_viewport_height"
BROWSER_TIMEOUT_MS_KEY = "browser_timeout_ms"
BROWSER_SSRF_ALLOW_PRIVATE_KEY = "browser_ssrf_allow_private"
BROWSER_SSRF_WHITELIST_KEY = "browser_ssrf_whitelist"
BROWSER_MAX_INSTANCES_KEY = "browser_max_instances"
BROWSER_IDLE_TIMEOUT_MS_KEY = "browser_idle_timeout_ms"
BROWSER_USE_SYSTEM_BROWSER_KEY = "browser_use_system_browser"
BROWSER_SYSTEM_BROWSER_CHANNEL_KEY = "browser_system_browser_channel"

# 工具启用状态配置键
TOOL_ENABLED_PREFIX = "tool_enabled_"
MCP_SERVERS_CONFIG_KEY = "mcp_servers"

# LLM提供商配置
PROVIDERS = {
    "zhipu": {
        "name": "智谱AI",
        "models": [
            {"id": "glm-4-flash", "name": "GLM-4-Flash (快速响应)"},
            {"id": "glm-4", "name": "GLM-4 (高性能)"},
            {"id": "glm-4-plus", "name": "GLM-4-Plus (旗舰)"},
        ]
    }
}

# Embedding提供商配置
EMBEDDING_PROVIDERS = {
    "openrouter": {
        "name": "OpenRouter",
        "models": [
            {"id": "nvidia/llama-nemotron-embed-vl-1b-v2:free", "name": "Llama-Nemotron-Embed-VL-1B (免费)"},
        ]
    }
}

# 嵌入服务常量
DEFAULT_EMBEDDING_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
CACHE_ENABLED_KEY = "embedding_cache_enabled"
CACHE_MAX_ENTRIES_KEY = "embedding_cache_max_entries"
EMBEDDING_PROVIDER_LOCAL = "local"
EMBEDDING_PROVIDER_OPENROUTER = "openrouter"

# 日志配置常量
MAX_LOG_BUFFER_SIZE = 1000
LOG_RETENTION_DAYS = 7
LOG_MAX_RECORDS = 100000
LOG_CLEANUP_INTERVAL_HOURS = 24

# 记忆刷新常量
AUTO_MEMORY_FLUSH_ENABLED = "auto_memory_flush_enabled"
AUTO_MEMORY_FLUSH_THRESHOLD = "auto_memory_flush_threshold"

# 通用常量
LOG_SEPARATOR = "─" * 50
LOG_SEPARATOR_SHORT = "─" * 40
