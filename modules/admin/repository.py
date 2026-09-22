from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from modules.user.model import Permission, Role, User, role_permissions


def list_roles(db: Session) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.code)).all())

def list_permissions(db: Session) -> list[str]:
    return list(db.scalars(select(Permission.code).order_by(Permission.code)).all())

def get_role(db: Session, role_code: str) -> Role | None:
    return db.get(Role, role_code)


def permission_codes_exist(db: Session, codes: set[str]) -> bool:
    if not codes:
        return True
    found = set(db.scalars(select(Permission.code).where(Permission.code.in_(codes))).all())
    return found == codes


def replace_role_permissions(db: Session, role_code: str, codes: set[str]) -> None:
    db.execute(delete(role_permissions).where(role_permissions.c.role_code == role_code))
    if codes:
        db.execute(
            insert(role_permissions),
            [{"role_code": role_code, "permission_code": code} for code in sorted(codes)],
        )
