from app.services.log_service import (
    LogEntry,
    WebSocketLogHandler,
    DatabaseLogHandler,
    LogService,
    get_ws_log_handler,
    get_db_log_handler,
    setup_log_handlers,
    cleanup_log_handlers,
)
from app.services.embedding_service import (
    EmbeddingService,
    LocalEmbeddingService,
    get_embedding_service,
    embedding_to_bytes,
    bytes_to_embedding,
    cosine_similarity,
)
from app.services.llm_service import (
    LLMService,
    get_llm_service,
)
from app.services.memory_flush_service import (
    MemoryFlushService,
    get_memory_flush_service,
)
from app.services.memory_summarizer import (
    MemorySummarizer,
    get_memory_summarizer,
)
from app.services.sqlite_vec_service import (
    SQLiteVecService,
    get_sqlite_vec_service,
)
from app.services.vector_search_service import (
    check_sqlite_vec_available,
    generate_and_store_embedding,
    generate_embedding_standalone,
    search_messages_by_similarity,
    search_long_term_memory_by_similarity,
    hybrid_memory_search,
    index_message_embedding,
    index_long_term_memory_embedding,
    batch_index_conversation_messages,
    search_messages_by_bm25,
    search_long_term_memory_by_bm25,
    hybrid_search,
    mmr_rerank,
    apply_temporal_decay,
)

__all__ = [
    "LogEntry",
    "WebSocketLogHandler",
    "DatabaseLogHandler",
    "LogService",
    "get_ws_log_handler",
    "get_db_log_handler",
    "setup_log_handlers",
    "cleanup_log_handlers",
    "EmbeddingService",
    "LocalEmbeddingService",
    "get_embedding_service",
    "embedding_to_bytes",
    "bytes_to_embedding",
    "cosine_similarity",
    "LLMService",
    "get_llm_service",
    "MemoryFlushService",
    "get_memory_flush_service",
    "MemorySummarizer",
    "get_memory_summarizer",
    "SQLiteVecService",
    "get_sqlite_vec_service",
    "check_sqlite_vec_available",
    "generate_and_store_embedding",
    "generate_embedding_standalone",
    "search_messages_by_similarity",
    "search_long_term_memory_by_similarity",
    "hybrid_memory_search",
    "index_message_embedding",
    "index_long_term_memory_embedding",
    "batch_index_conversation_messages",
    "search_messages_by_bm25",
    "search_long_term_memory_by_bm25",
    "hybrid_search",
    "mmr_rerank",
    "apply_temporal_decay",
]
