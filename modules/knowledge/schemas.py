
from datetime import datetime

from typing import Literal
from pydantic import BaseModel, ConfigDict

class VisibilityIn(BaseModel):
    visibility: Literal["public", "internal"]

class KnowledgeDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_name: str
    source_path: str
    file_type: str
    visibility: str
    status: str
    chunk_count: int
    error_message: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime

class KnowledgeDocumentPage(BaseModel):
    items:list[KnowledgeDocumentOut]
    total:int
    page:int
    page_size:int

class KnowledgeStatusOut(BaseModel):
    status: str
    chunks: int

