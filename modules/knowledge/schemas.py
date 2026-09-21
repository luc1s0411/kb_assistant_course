
from datetime import datetime

from pydantic import BaseModel, ConfigDict

# Literal ：限制只能传这两个参数，否则报错
from typing import Literal
class VisibilityIn(BaseModel):
    visibility: Literal["public", "internal"]

class KnowledgeDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id : int                    # id
    original_name : str         # 文档原始文件名
    source_path : str           # 源路径
    file_type: str              # 文件类型
    visibility : str            # 可见性
    status : str                # 状态
    chunk_count: int            # 切块数量
    error_message: str | None   # 错误信息
    created_by: int             # 创建人ID
    created_at: datetime        # 创建时间
    updated_at: datetime        # 更新时间

class KnowledgeDocumentPage(BaseModel):
    items: list[KnowledgeDocumentOut]
    total: int
    page: int
    page_size: int