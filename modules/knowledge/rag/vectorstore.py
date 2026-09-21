import chromadb
from functools import lru_cache

from langchain_chroma import Chroma

from core.config import settings
from modules.knowledge.dependencies import get_embeddings


@lru_cache(maxsize=1)
def get_chroma_client():
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(settings.chroma_dir))


def _collection_names() -> set[str]:
    names: set[str] = set()
    for item in get_chroma_client().list_collections():
        names.add(item if isinstance(item, str) else item.name)
    return names


def _get_existing_collection():
    client = get_chroma_client()
    if settings.collection_name not in _collection_names():
        return None
    return client.get_collection(settings.collection_name)


def get_vectorstore() -> Chroma:
    return Chroma(
        client=get_chroma_client(),
        collection_name=settings.collection_name,
        embedding_function=get_embeddings(),
        collection_metadata={"hnsw:space": "cosine"},
    )


def reset_collection() -> None:
    client = get_chroma_client()
    if settings.collection_name in _collection_names():
        client.delete_collection(settings.collection_name)


def collection_count() -> int:
    collection = _get_existing_collection()
    return 0 if collection is None else collection.count()


def source_count(source_path: str) -> int:
    collection = _get_existing_collection()
    if collection is None:
        return 0
    result = collection.get(where={"source_path": source_path}, include=[])
    return len(result["ids"])


def delete_source(source_path: str) -> int:
    collection = _get_existing_collection()
    if collection is None:
        return 0
    result = collection.get(where={"source_path": source_path}, include=[])
    ids = result["ids"]
    if ids:
        collection.delete(ids=ids)
    return len(ids)


def clear_vectorstore_cache() -> None:
    get_chroma_client.cache_clear()