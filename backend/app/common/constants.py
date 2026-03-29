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
