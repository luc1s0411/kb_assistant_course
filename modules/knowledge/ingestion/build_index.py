import hashlib
import json
from pathlib import Path

from core.config import settings
from modules.knowledge.ingestion.loader import load_docs, load_file, split_docs
from modules.knowledge.rag.vectorstore import get_vectorstore, reset_collection
    

def _chunk_id(document) -> str:
    payload = {
        "page_content": document.page_content,
        "metadata": document.metadata,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _add_chunks(chunks) -> int:
    if not chunks:
        return 0
    ids = [_chunk_id(document) for document in chunks]
    get_vectorstore().add_documents(documents=chunks, ids=ids)
    return len(ids)


def index_document(path: str | Path) -> int:
    file_path = Path(path).resolve()
    documents = load_file(file_path, settings.docs_dir.resolve())
    chunks = split_docs(documents)
    return _add_chunks(chunks)


def index_documents() -> int:
    documents = load_docs(settings.docs_dir)
    chunks = split_docs(documents)
    reset_collection()
    return _add_chunks(chunks)