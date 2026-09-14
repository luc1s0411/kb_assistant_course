from openai.types.admin.organization import role
from sqlalchemy.orm import Session
from modules.user.model import User, Permission, role_permissions
from sqlalchemy import select

from modules.user.schemas import ProfileUpdateIn, CurrentUser


# 访问数据库的文件
#通过邮箱查询用户是否存在
def get_user_by_email(db:Session,email:str):
    # select * from user where user.email=email
    return db.scalar(select(User).where(User.email == email))

def get_user_by_id(db:Session,user_id:int):
    # select * from user where user.id=id
    return db.scalar(select(User).where(User.id == user_id))
# 定义向user表插入一条数据的函数

def create_user(db:Session,user:User):
    db.add(user)
    db.commit()
    db.refresh(user)

#获取该用户的权限code
def get_permission(db:Session, id:int):
    #  Table 表在联合查询是加一个.c
    codes = db.scalars(select(Permission.code).
                       join(role_permissions,Permission.code
                             == role_permissions.c.permission_code).
               join(User,User.role_code == role_permissions.c.role_code)
               .where(User.id == id,User.is_active.is_(True))).all()
    return set(codes)

def update_user_profile(data:ProfileUpdateIn,
                        user:CurrentUser,
                        db:Session):
    my_user = db.get(User,user.id)
    if data.username!=None:
        my_user.username = data.username
    if data.email!=None:
        my_user.email = data.email
    if data.full_name!=None:
        my_user.full_name = data.full_name

    db.flush()
    db.commit()
    return my_user