from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from modules.user.model import Permission, Role, User, role_permissions


def list_roles(db: Session) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.code)).all())

def list_permissions(db: Session) -> list[str]:
    return list(db.scalars(select(Permission.code).order_by(Permission.code)).all())
