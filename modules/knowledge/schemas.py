
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KnowledgeDocumentOut(BaseModel):
    id : int                    # id
    original_name : str         # 文档原始文件名
    source_path : str           # 源路径
    file_type: str              # 文件类型
    visibility : str            # 可见性
    status : str                # 状态
    chunk_count: int            #
    error_message: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime