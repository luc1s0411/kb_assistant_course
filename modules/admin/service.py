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
