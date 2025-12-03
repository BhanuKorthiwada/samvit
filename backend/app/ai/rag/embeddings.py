"""Embedding utilities for RAG."""

import hashlib
import logging
import os
from functools import lru_cache

from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingConfig(BaseModel):
    """Configuration for embedding model."""

    model_name: str = "text-embedding-3-small"
    dimension: int = 1536
    batch_size: int = 100


@lru_cache
def get_embedding_config() -> EmbeddingConfig:
    """Get embedding configuration."""
    return EmbeddingConfig()


def get_embedding_function():
    """Get the embedding function for ChromaDB.

    Uses OpenAI embeddings via ChromaDB's built-in support.
    Falls back to default embedding function if API key not set or in test mode.
    """
    import chromadb.utils.embedding_functions as embedding_functions

    config = get_embedding_config()

    is_test_mode = os.getenv("PYTEST_CURRENT_TEST") is not None
    api_key = settings.openai_api_key

    if is_test_mode or not api_key or api_key.startswith("sk-test"):
        logger.info("Using default embedding function (test mode or no API key)")
        return embedding_functions.DefaultEmbeddingFunction()

    return embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name=config.model_name,
    )


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of content for deduplication."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
