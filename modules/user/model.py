from sqlalchemy import String,ForeignKey,Table,Column,Boolean
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped,mapped_column,relationship
from database.base import Base
from datetime import datetime

role_permissions=Table(
    "role_permissions",
    Base.metadata,
    Column("role_code",String(32),ForeignKey("roles.code"),onupdate="CASCADE",primary_key=True),
    Column("permission_code",String(64),ForeignKey("permissions.code"),onupdate="CASCADE",primary_key=True)
)


class Role(Base):
    __tablename__ = 'roles'
    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    permissions:Mapped[list["Permission"]]=relationship(
        secondary=role_permissions,lazy="selectin"
    )


class Permission(Base):
    __tablename__ = "permissions"
    #每个权限一个代码
    code:Mapped[str] = mapped_column(String(64), primary_key=True)
#权限和角色是多对多，，一个角色有多种权限，一个权限也可以被多个人使用。
#这是一个中间表，之前设计中间表class role_permissions
#在sqlalchemy中，我们使用Table来定义中间表，好处是sqlalchemy替我们维护表


# 为什么要继承这个Base？
# 因为我们要把我们的类注册到数据库中(sqlalchemy)
class User(Base):
    __tablename__ = "users"
    #tinyint(-128-127) int(-21亿-21亿) bigint(最大922亿亿)
    id:Mapped[int] = mapped_column(mysql.BIGINT(unsigned=True),
                                   primary_key=True,
                                   autoincrement=True
                                   )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)#unique:唯一约束nullable不能为空
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False,default="public")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100))
    role_code: Mapped[str] = mapped_column(
        ForeignKey("roles.code"), default="public", nullable=False
    )
    is_active:Mapped[bool] = mapped_column(Boolean,nullable=False,default=True)
    created_at: Mapped[datetime] = mapped_column(mysql.DATETIME(fsp=6), nullable=False)
    role: Mapped[Role] = relationship(lazy="selectin")