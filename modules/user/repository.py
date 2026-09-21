from sqlalchemy.orm import Session
from modules.user.model import User, role_permissions,Permission
from sqlalchemy import select

# 访问数据库的文件
# 通过邮箱查询用户是否存在
def get_user_by_email(db: Session, email: str):
    return db.scalar(select(User).where(User.email == email))

def get_user_by_id(db: Session, user_id: int):
    return db.scalar(select(User).where(User.id == user_id))

# 定义一个user表插入一条数据的函数

def create_user(db: Session, user: User):
    db.add(user)
    db.commit()
    db.refresh(user)
    pass

    # 获取该用户的权限code

#获取该用户的权限code
#获取该用户的权限code
def get_perssion(db:Session,id:int):
    #  Table 表在联合查询是加一个.c
    codes = db.scalars(
        select(Permission.code)
        .join(role_permissions, Permission.code == role_permissions.c.permission_code)  # c.role → c.permission_code
        .join(User, User.role_code == role_permissions.c.role_code)
        .where(User.id == id, User.is_active.is_(True))
    ).all()
    return set(codes)

from modules.user.schemas import ProfileUpdateIn
from modules.user.schemas import RegisterIn,CurrentUser

def update_user_profile(data:ProfileUpdateIn,user:CurrentUser,db:Session):
    myuser = db.get(User,user.id)
    if data.username is not None:
        myuser.username = data.username
    if data.email is not None:
        myuser.email = data.email
    if data.full_name is not None:
        myuser.full_name = data.full_name

    db.flush()
    db.commit()
    return myuser

def update_password_hash(db:Session,user_id:int,password:str):
    user=db.get(User,user_id)
    user.password_hash = password
    db.flush()
    db.commit()
    return True







