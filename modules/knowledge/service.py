
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

from modules.knowledge.model import KnowledgeDocument
async def upload_document(db:Session,file:UploadFile,visibility,userid):
    # 1.上传文件
    name, suffix, content = await _read_upload(file)

    # 2.把信息存入数据库
    document:KnowledgeDocument = _save_document(db, name, suffix, content, visibility, userid)
    # 3.切片
    # 3.1 读取硬盘上的文件和内容  _document_path =  ./data/docs/public/eab51198bb5346da9ad94b94b89ae534.md
    # 读取硬盘文件，转成一个charmdb能存的document   documents = []
    documents = load_file(_document_path(document.source_path), settings.docs_dir)
    # 切片存储  切完后的列表数据
    chunks = split_docs(documents)

    # 把切的块存入charomdb


    document.chunk_count = len(chunks)
    document.status = "pending" if chunks else "error"
    document.error_message = None if chunks else "未读取到可索引文本，请检查文件"
    db.commit()


    # 4.存入chromdb
    return document