from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import select

from modules.knowledge.model import KnowledgeDocument
# 世界标准时间，伦敦时间 0时区时间
def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

def create_document( db: Session, original_name: str,
    stored_name: str,    source_path: str,    file_type: str,
    visibility: str,    created_by: int,):
    now = utc_now()
    row = KnowledgeDocument(
        original_name=original_name,
        stored_name=stored_name,        source_path=source_path,
        file_type=file_type,        visibility=visibility,
        status="pending",        chunk_count=0,
        error_message=None,        created_by=created_by,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    # 因为我们是保存数据，一旦提交就能够获取到id
    db.flush()
    return row

def all_documents(db: Session) -> list[KnowledgeDocument]:
    return list(db.scalars(select(KnowledgeDocument)).all())


def mark_indexed(row: KnowledgeDocument, chunks: int) -> None:
    row.status = "indexed"
    row.chunk_count = chunks
    row.error_message = None
    row.updated_at = utc_now()


def mark_error(row: KnowledgeDocument, message: str) -> None:
    row.status = "error"
    row.error_message = message[:2000]
    row.updated_at = utc_now()