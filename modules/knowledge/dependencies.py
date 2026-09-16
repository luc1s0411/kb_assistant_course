from functools import lru_cache

from langchain_ollama import OllamaEmbeddings

from core.config import settings


@lru_cache(maxsize=1)
def get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=settings.ollama_embedding_model,
        base_url=settings.ollama_base_url,
    )


def clear_dependency_cache() -> None:
    get_embeddings.cache_clear()