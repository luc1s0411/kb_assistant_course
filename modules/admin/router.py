from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_session
from modules.admin import service
from modules.admin.schemas import RoleOut, RolePermissionsIn, UserRoleIn, UserRoleOut
from modules.user.permissions import require_permission
from modules.user.schemas import CurrentUser


router = APIRouter(prefix="/admin", tags=["系统管理"])


@router.get("/roles", response_model=list[RoleOut])
def roles(
    db: Session = Depends(get_session),
    _: CurrentUser = Depends(require_permission("system.manage_roles")),
) -> list[RoleOut]:
    return service.get_roles(db)

@router.get("/permissions", response_model=list[str])
def permissions(
    db: Session = Depends(get_session),
    _: CurrentUser = Depends(require_permission("system.manage_roles")),
) -> list[str]:
    return service.get_permissions(db)
