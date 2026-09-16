from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from database.connection import get_session
from modules.knowledge import service
# from modules.knowledge.schemas import KnowledgeDocumentOut
from modules.user.permissions import require_permission
from modules.user.schemas import CurrentUser
from modules.knowledge.schemas import KnowledgeDocumentOut

router = APIRouter(prefix="/knowledge", tags=["知识库管理"])


# 定义路由
@router.post("/documents",response_model=KnowledgeDocumentOut)
async def upload_documents(
        # UploadFile 专门承接上传的文件
        file: Annotated[UploadFile, File()],
        visibility: Annotated[Literal["public", "internal"], Form()] = "public",
        db: Session = Depends(get_session),
        user: CurrentUser = Depends(require_permission("kb.manage_docs"))
):
    # 调用service的函数，上传文件和保存文件信息
    return  await service.upload_document(db,file,visibility,user.id)
