
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KnowledgeDocumentOut(BaseModel):
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