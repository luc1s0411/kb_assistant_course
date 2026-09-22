from fastapi import HTTPException
from sqlalchemy.orm import Session

from modules.admin import repository
from modules.admin.schemas import RoleOut, UserRoleOut


def get_roles(db: Session) -> list[RoleOut]:
    return [
        RoleOut(
            code=role.code,
            name=role.name,
            permissions=sorted(permission.code for permission in role.permissions),
        )
        for role in repository.list_roles(db)
    ]

def get_permissions(db: Session) -> list[str]:
    return repository.list_permissions(db)

def set_role_permissions(db: Session, role_code: str, requested: list[str]) -> RoleOut:
    role = repository.get_role(db, role_code)
    if role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    codes = {code.strip() for code in requested if code.strip()}
    if not repository.permission_codes_exist(db, codes):
        raise HTTPException(status_code=400, detail="请求中包含不存在的权限码")
    if role_code == "public" and "kb.view_public" not in codes:
        raise HTTPException(status_code=400, detail="public 必须保留 kb.view_public")
    repository.replace_role_permissions(db, role_code, codes)
    db.commit()
    db.refresh(role)
    return RoleOut(code=role.code, name=role.name, permissions=sorted(codes))

def set_user_role(db: Session, user_id: int, role_code: str) -> UserRoleOut:
    if repository.get_role(db, role_code) is None:
        raise HTTPException(status_code=400, detail="角色不存在")
    user = repository.set_user_role(db, user_id, role_code)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.commit()
    return UserRoleOut(user_id=user.id, role_code=user.role_code)
