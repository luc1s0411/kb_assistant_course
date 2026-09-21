from typing import Annotated, Literal
from modules.knowledge.schemas import KnowledgeStatusOut

from fastapi import APIRouter, Depends, File, Form, UploadFile,Query
from sqlalchemy.orm import Session
from database.connection import get_session
from modules.knowledge.service import *
from modules.knowledge.schemas import KnowledgeDocumentOut
from modules.user.permissions import require_permission
from modules.user.schemas import CurrentUser


router = APIRouter(prefix="/knowledge", tags=["知识库管理"])

from modules.knowledge.schemas import KnowledgeDocumentOut
# 定义路由
@router.post("/documents",response_model=KnowledgeDocumentOut)
async def uploaddocuments(
        # UploadFile 专门承接上传的文件
        file: Annotated[UploadFile, File()],
        visibility: Annotated[Literal["public", "internal"], Form()] = "public",
        db: Session = Depends(get_session),
        user: CurrentUser = Depends(require_permission("kb.manage_docs"))
):
    # 调用sevice的函数，上传文件和保存文件信息
    return  await service.upload_document(db,file,visibility,user.id)


from modules.knowledge.schemas import KnowledgeDocumentPage
from modules.knowledge import service

@router.get("/documents", response_model=KnowledgeDocumentPage)
def documents(page: int = Query(default=1, ge=1),
              page_size: int = Query(default=10, ge=1),
              db: Session = Depends(get_session),
              user: CurrentUser = Depends(require_permission("kb.manage_docs"))):


    return service.get_documents(db, page, page_size)

from modules.knowledge.schemas import VisibilityIn
@router.patch(
    path="/documents/{document_id}/visibility",
    response_model=KnowledgeDocumentOut
)
def update_visibility(
    document_id: int,
    data: VisibilityIn,
    db: Session = Depends(get_session),
        # _：是一个变量名，表示这个参数是必须的，但不需要使用这个数据本身
    _: CurrentUser = Depends(require_permission("kb.manage_docs")),
) -> KnowledgeDocumentOut:
    return service.change_visibility(db, document_id, data.visibility)

from fastapi import Response

@router.delete(path="/documents/{document_id}", status_code=204)
def remove_document(
    document_id: int,
    db: Session = Depends(get_session),
    _: CurrentUser = Depends(require_permission("kb.manage_docs")),
) -> Response:
    service.delete_document(db, document_id)
    return Response(status_code=204)


@router.post("/reindex", response_model=KnowledgeStatusOut)
def reindex(
    db: Session = Depends(get_session),
    _: CurrentUser = Depends(require_permission("kb.manage_docs")),
) -> dict:
    return service.rebuild_index(db)

from modules.user.dependencies import get_current_user
@router.get("/status", response_model=KnowledgeStatusOut)
def index_status(_: CurrentUser = Depends(get_current_user)) -> dict:
    return service.get_index_status()

