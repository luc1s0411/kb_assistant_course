
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from pydantic.deprecated.parse import load_file
from sqlalchemy.orm import Session

from core.config import settings
from modules.knowledge import repository
from modules.knowledge.model import KnowledgeDocument

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

async def upload_document(db:Session,file:UploadFile,visibility,userid):
    # 1.上传文件
    name, suffix, content = await _read_upload(file)

    # 2.把信息存入数据库
    document:KnowledgeDocument =  _save_document(db, name, suffix, content, visibility, userid)

    # 3.切片
    # 3.1 读取硬盘上的文件和内容
    documents = load_file()

    # 4.存入chromdb