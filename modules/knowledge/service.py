
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from core.config import settings
from modules.knowledge import repository
# 定义10m，我们限定上传的文件最大10m
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

async  def _read_upload(file:UploadFile):
    # file.filename 获取文件名称
    original_name = Path((file.filename or "").replace("\\", "/")).name
    # .suffix 获取文件后缀
    suffix = Path(original_name).suffix.lower()
    # read 读取文件内容
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    return original_name, suffix, content


def _document_path(source_path: str) -> Path:
    # ./data/docs
    root = settings.docs_dir.resolve()
    path = (root / source_path).resolve()
    if not path.is_relative_to(root) or path == root:
        raise HTTPException(status_code=400, detail="文档路径越出知识目录")
    return path

def _save_document(db, name, suffix, content, visibility, user_id):
    # 1.存到本地   2534536sld3466.txt 新起文件名，避免覆盖
    stored_name = f"{uuid4().hex}{suffix}"
    # visibility==public /internal
    source_path = f"{visibility}/{stored_name}"
    # path = /data/docs/public/存储的文件名     path = /data/docs/internal/存储的文件名
    path = _document_path(source_path)
    # 如果没有这个父文件，我来创建
    path.parent.mkdir(parents=True, exist_ok=True)
    # 把数据写到文件
    path.write_bytes(content)
    # 2.存到mysql
    row = repository.create_document(
        db,
        original_name=name,
        stored_name=stored_name,
        source_path=source_path,
        file_type=suffix.lstrip("."),
        visibility=visibility,
        created_by=user_id,
    )
    db.commit()
    return row

from pathlib import Path

import docx
from langchain_core.documents import Document
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.config import settings


SUPPORTED_SUFFIXES = {".pdf", ".docx", ".md", ".txt"}
VISIBILITIES = {"public", "internal"}

def _visibility(path: Path, docs_dir: Path) -> str:
    relative = path.relative_to(docs_dir)
    first_part = relative.parts[0].lower() if len(relative.parts) > 1 else "public"
    if first_part in {"employee", "hr", "internal"}:
        return "internal"
    return first_part if first_part in VISIBILITIES else "public"

def _metadata(path: Path, docs_dir: Path, **extra) -> dict:
    return {
        "source": path.name,
        "source_path": path.relative_to(docs_dir).as_posix(),
        "visibility": _visibility(path, docs_dir),
        "file_type": path.suffix.lower().lstrip("."),
        **extra,
    }

def load_text(path: Path, docs_dir: Path) -> list[Document]:
    # 读取文件内容
    text = path.read_text(encoding="utf-8-sig")
    if not text.strip():
        return []
    return [Document(page_content=text, metadata=_metadata(path, docs_dir))]

def load_docx(path: Path, docs_dir: Path) -> list[Document]:
    document = docx.Document(str(path))
    blocks = [paragraph.text.strip() for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            blocks.append(" | ".join(cell.text.strip() for cell in row.cells))
    text = "\n".join(block for block in blocks if block)
    if not text:
        return []
    return [Document(page_content=text, metadata=_metadata(path, docs_dir))]

def load_pdf(path: Path, docs_dir: Path) -> list[Document]:
    reader = PdfReader(str(path))
    documents: list[Document] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            documents.append(
                Document(
                    page_content=text,
                    metadata=_metadata(path, docs_dir, page=page_number),
                )
            )
    return documents

def load_file(path: Path, docs_dir: Path) -> list[Document]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return load_pdf(path, docs_dir)
    if suffix == ".docx":
        return load_docx(path, docs_dir)
    if suffix in {".txt", ".md"}:
        return load_text(path, docs_dir)
    raise ValueError("只支持 txt、md、pdf、docx")


def split_docs(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        add_start_index=True,
    )
    return splitter.split_documents(documents)
from modules.knowledge.ingestion.build_index import _add_chunks
from modules.knowledge.model import KnowledgeDocument
async def upload_document(db:Session,file:UploadFile,visibility,userid):
    # 1.上传文件
    name, suffix, content = await _read_upload(file)

    # 2.把信息存入数据库
    document:KnowledgeDocument = _save_document(db, name, suffix, content, visibility, userid)
    # 3.切片
    # 3.1 读取硬盘上的文件和内容  _document_path =  ./data/docs/public/eab51198bb5346da9ad94b94b89ae534.md
    # 读取硬盘文件，转成一个chromadb能存的document   documents = []
    documents = load_file(_document_path(document.source_path), settings.docs_dir)
    # 切片存储  切完后的列表数据
    chunks = split_docs(documents)

    # 把切的块存入chromadb
    _add_chunks(chunks)

    document.chunk_count = len(chunks)
    document.status = "indexed" if chunks else "error"
    document.error_message = None if chunks else "未读取到可索引文本，请检查文件"
    db.commit()


    # 4.存入chromadb
    return document

def _index_saved_document(db: Session, row) -> int:
    source_path = row.source_path
    try:
        # 先清掉该来源可能残留的旧块，再只索引当前文件。
        delete_source(source_path)
        chunks = index_document(_document_path(source_path))
        if chunks:
            # 告诉mysql存了多少片
            repository.mark_indexed(row, chunks)
        else:
            row.chunk_count = 0
            repository.mark_error(row, "未读取到该文档的可索引文本，请检查文件")
        db.commit()
        return chunks
    except Exception as exc:
        db.rollback()
        try:
            # 防止 add_documents 中途失败后留下当前来源的半截数据。
            delete_source(source_path)
        except Exception:
            pass
        row.chunk_count = 0
        repository.mark_error(row, "当前文件索引失败，请检查解析文件、Ollama 与 Chroma")
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="文档变更已保存，但当前文件索引失败；修复后调用 POST /knowledge/reindex",
        ) from exc


from modules.knowledge.schemas import KnowledgeDocumentPage
def get_documents(db:Session, page:int, page_size:int):
    rows, total = repository.list_documents(db, page, page_size)
    return KnowledgeDocumentPage(items=rows, total=total,page_size=page_size, page=page)

from modules.knowledge.rag.vectorstore import delete_source
from modules.knowledge.ingestion.build_index import index_document
# 线程锁，控制多人同时操作，只有一个人能执行，顺次执行。为了避免高并发的数据错乱
from threading import RLock
INDEX_LOCK = RLock()
def change_visibility(db: Session, document_id: int, visibility: str):
    with INDEX_LOCK:
        # 一行数据
        row = repository.get_document(db, document_id)
        if row is None:
            raise HTTPException(status_code=404, detail="文档不存在")

        old_source_path = row.source_path
        # 找到文件存到硬盘的路径
        old_path = _document_path(old_source_path)
        if not old_path.is_file():
            raise HTTPException(status_code=409, detail="文档文件缺失，请删除记录后重新上传")
        if row.visibility == visibility:
            return row

        # 用户想改的硬盘路径
        new_path = _document_path(f"{visibility}/{row.stored_name}")
        if new_path.exists():
            raise HTTPException(status_code=409, detail="目标文件已经存在")

        try:
            # 删除chromdb中的文档数据
            old_vector_count = delete_source(old_source_path)
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail="索引服务不可用，本次可见范围修改未执行",
            ) from exc

        new_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # 硬盘移动了老文件到新位置
            old_path.replace(new_path)

            row.visibility = visibility
            row.source_path = new_path.relative_to(settings.docs_dir.resolve()).as_posix()
            row.status = "pending"
            row.chunk_count = 0
            row.error_message = None
            db.commit()
        except Exception:
            db.rollback()
            if new_path.exists():
                new_path.replace(old_path)
            if old_vector_count and old_path.is_file():
                try:
                    # 如果报错，之前冲chromdb删除的数据，再恢复回来(重新构建)。
                    index_document(old_path)
                except Exception:
                    pass
            raise

        # 第一，把文件加载到chrmadb，第二，更新mysql数据中的数据
        _index_saved_document(db, row)
        db.refresh(row)
        return row

def delete_document(db: Session, document_id: int) -> None:
    with INDEX_LOCK:
        row = repository.get_document(db, document_id)
        if row is None:
            raise HTTPException(status_code=404, detail="文档不存在")

        source_path = row.source_path
        path = _document_path(source_path)
        backup = path.with_suffix(path.suffix + f".{uuid4().hex}.pending_delete")

        try:
            #从chromadb删除一条数据
            deleted_vectors = delete_source(source_path)
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail="索引服务不可用，本次删除未执行",
            ) from exc

        try:
            if path.exists():
                path.replace(backup)
            db.delete(row)
            db.commit()
        except Exception:
            db.rollback()
            if backup.exists():
                backup.replace(path)
            if deleted_vectors and path.is_file():
                try:
                    index_document(path)
                except Exception:
                    pass
            raise
        # 在硬盘删除一个文档
        backup.unlink(missing_ok=True)

from modules.knowledge.rag.vectorstore import delete_source, reset_collection, source_count
from modules.knowledge.ingestion.build_index import index_document, index_documents
from modules.knowledge.repository import *
def _refresh_index(db: Session) -> int:
    try:
        chunks = index_documents()
        for row in repository.all_documents(db):
            # 用mysql中的一条数据，取chromadb查找切片数
            count = source_count(row.source_path)
            if count:
                # 更新回mysql
                repository.mark_indexed(row, count)
            else:
                row.chunk_count = 0
                repository.mark_error(row, "未读取到该文档的可索引文本，请检查文件")
        db.commit()
        return chunks
    except Exception as exc:
        db.rollback()
        try:
            # 全量重建失败时不保留可能只写入一部分的 collection。
            reset_collection()
        except Exception:
            pass
        for row in repository.all_documents(db):
            row.chunk_count = 0
            repository.mark_error(row, "索引重建失败，请检查解析文件及索引服务后重新构建")
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="全量索引重建失败；修复后再次调用 POST /knowledge/reindex",
        ) from exc

def rebuild_index(db: Session) -> dict:
    with INDEX_LOCK:
        return {"status": "ok", "chunks": _refresh_index(db)}

from modules.knowledge.rag.vectorstore import collection_count
def get_index_status() -> dict:
    try:
        return {"status": "ok", "chunks": collection_count()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="索引服务不可用") from exc

